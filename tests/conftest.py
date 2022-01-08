from __future__ import annotations

import asyncio
import json
import subprocess
from collections import Counter
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from enum import Enum
from pathlib import Path
from shutil import copy, rmtree
from time import time
from typing import Any

import aiohttp
import pytest
from aiohttp.test_utils import unused_port
from environs import Env
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import cerbottana.databases.database as d
from cerbottana import utils
from cerbottana.connection import Connection
from cerbottana.database import Database
from cerbottana.models.room import Room
from cerbottana.tasks.veekun import csv_to_sqlite

# pylint: disable=protected-access, redefined-outer-name


def pytest_collection_modifyitems(items):
    for item in items:
        # Mark tests using a real showdown instance with `pytest.mark.real_ps_instance`
        if "showdown_connection" in item.fixturenames:
            item.add_marker(pytest.mark.real_ps_instance)


database_metadata: dict[str, Any] = {
    "database": d.Base.metadata,
}


class ControlMessage(bytes, Enum):
    # server to client
    PROCESS_MESSAGES = b"process_messages"
    PROCESS_AND_REPLY = b"process_and_reply"

    # client to server
    PROCESSING_DONE = b"processing_done"


class MockedConnection(Connection):
    async def _parse_binary_message(self, message: bytes) -> None:
        if message in (
            ControlMessage.PROCESS_MESSAGES,
            ControlMessage.PROCESS_AND_REPLY,
        ):
            for room in list(Room._instances.get(self, {}).values()):
                await room.process_all_messages()
            if message == ControlMessage.PROCESS_AND_REPLY:
                await self.send_bytes(ControlMessage.PROCESSING_DONE)

    async def _send_message_delay(self) -> None:
        # No need to throttle messages
        self.lastmessage = time()

    async def send_bytes(self, message: bytes) -> None:
        if self.websocket is not None:
            await self._send_message_delay()
            print(f">b {message.decode()}")
            await self.websocket.send_bytes(message)


class ServerWs(aiohttp.web.WebSocketResponse):
    async def add_user_join(
        self,
        room: str,
        user: str,
        rank: str = " ",
        *,
        group: str = " ",
    ) -> None:
        roomid = utils.to_room_id(room)
        userid = utils.to_user_id(user)

        await self.add_messages(
            [
                f">{roomid}",
                f"|j|{rank}{userid}",
            ]
        )
        await self.add_queryresponse_userdetails(
            user, group=group, rooms={roomid: rank}
        )

    async def add_user_namechange(
        self,
        room: str,
        user: str,
        olduser: str,
        rank: str = " ",
        *,
        group: str = " ",
    ) -> None:
        roomid = utils.to_room_id(room)
        userid = utils.to_user_id(user)
        olduserid = utils.to_user_id(olduser)

        await self.add_messages(
            [
                f">{roomid}",
                f"|n|{rank}{userid}|{olduserid}",
            ]
        )
        await self.add_queryresponse_userdetails(
            user, group=group, rooms={roomid: rank}
        )

    async def add_user_leave(self, room: str, user: str) -> None:
        roomid = utils.to_room_id(room)
        userid = utils.to_user_id(user)

        await self.add_messages(
            [
                f">{roomid}",
                f"|l|{userid}",
            ]
        )

    async def add_queryresponse_userdetails(
        self,
        user: str,
        *,
        group: str = " ",
        rooms: dict[str, str] | None = None,
    ) -> None:
        userid = utils.to_user_id(user)

        if rooms is None:
            rooms = {}

        data = {
            "id": user,
            "userid": userid,
            "name": user,
            "avatar": "1",
            "group": group,
            "autoconfirmed": True,
            "status": "",
            "rooms": {rooms[room].strip() + room: {} for room in rooms},
        }

        await self.add_messages(
            [
                f"|queryresponse|userdetails|{json.dumps(data)}",
            ]
        )

    async def add_messages(self, *items: list[str]) -> None:
        for item in items:
            await self.send_str("\n".join(item))

        await self.send_bytes(ControlMessage.PROCESS_MESSAGES)

    async def get_messages(self) -> Counter[str]:
        await self.send_bytes(ControlMessage.PROCESS_AND_REPLY)

        messages: Counter[str] = Counter()
        async for message in self:
            if message.type == aiohttp.WSMsgType.TEXT:
                messages.update([message.data])
            elif (
                message.type == aiohttp.WSMsgType.BINARY
                and message.data == ControlMessage.PROCESSING_DONE
            ):
                break
        return messages


@pytest.fixture()
def mock_connection(
    aiohttp_raw_server,
) -> Callable[
    [Callable[[ServerWs, MockedConnection], Awaitable[None]]], Awaitable[None]
]:
    async def make_mock_connection(
        server_handler: Callable[[ServerWs, MockedConnection], Awaitable[None]],
        *,
        username: str = "cerbottana",
        password: str = "",
        avatar: str = "",
        statustext: str = "",
        rooms: list[str] | None = None,
        main_room: str = "lobby",
        command_character: str = ".",
        administrators: list[str] | None = None,
        webhooks: dict[str, str] | None = None,
    ) -> None:
        async def handler(request: aiohttp.web_request.BaseRequest) -> ServerWs:
            ws = ServerWs(max_msg_size=0)
            await ws.prepare(request)

            await ws.add_messages(["|updateuser|*cerbottana|1|0|{}"])
            await ws.get_messages()

            await server_handler(ws, conn)

            await ws.close()
            return ws

        raw_server = await aiohttp_raw_server(handler)
        url = raw_server.make_url("/")

        if rooms is None:
            rooms = ["room1"]
        if administrators is None:
            administrators = ["parnassius"]
        if webhooks is None:
            webhooks = {"room1": "https://discord.com/api/webhooks/00000/aaaaa"}

        conn = MockedConnection(
            url=url,
            username=username,
            password=password,
            avatar=avatar,
            statustext=statustext,
            rooms=rooms,
            main_room=main_room,
            command_character=command_character,
            administrators=administrators,
            webhooks=webhooks,
            unittesting=True,
        )

        await conn._start_websocket()

        if conn.websocket is not None:
            exc = conn.websocket.exception()
            if exc:
                raise exc

    return make_mock_connection


# Full integration tests fixtures


class TestConnection(Connection):
    def __init__(
        self,
        *,
        url: str,
        username: str,
        password: str,
        avatar: str,
        statustext: str,
        rooms: list[str],
        main_room: str,
        command_character: str,
        administrators: list[str],
        webhooks: dict[str, str],
        unittesting: bool = False,
    ) -> None:
        self.recv_queue: asyncio.Queue[str] = asyncio.Queue()

        super().__init__(
            url=url,
            username=username,
            password=password,
            avatar=avatar,
            statustext=statustext,
            rooms=rooms,
            main_room=main_room,
            command_character=command_character,
            administrators=administrators,
            webhooks=webhooks,
            unittesting=unittesting,
        )

    async def _parse_text_message(self, message: str) -> None:
        await super()._parse_text_message(message)

        await self.recv_queue.put(message)

    async def await_message(self, *messages: str, startswith: bool = False) -> str:
        while True:
            # Wait at most 5 seconds. It should be more than enough for normal cases,
            # and allows to easily identify eventual problems.
            msg = await asyncio.wait_for(self.recv_queue.get(), 5)
            if startswith:
                cond = msg.startswith(messages)
            else:
                cond = msg in messages
            if cond:
                return msg


@pytest.fixture(scope="session")
def showdown_server() -> Generator[int, None, None]:
    def pull_pokemon_showdown(cwd) -> None:
        cwd.mkdir(exist_ok=True)
        subprocess.run(["git", "init", "--quiet"], cwd=cwd, check=True)
        subprocess.run(
            [
                "git",
                "pull",
                "--quiet",
                "--ff-only",
                "https://github.com/smogon/pokemon-showdown.git",
            ],
            cwd=cwd,
            check=True,
        )

    env = Env()
    env.read_env()

    # Clone pokemon showdown
    cwd = Path(__file__).parent.parent / "pokemon-showdown"
    try:
        pull_pokemon_showdown(cwd)
    except subprocess.CalledProcessError:
        # Delete the directory and retry
        rmtree(cwd)
        pull_pokemon_showdown(cwd)

    # Create the configuration file and tweak some options
    config = cwd / "config/config.js"
    copy(cwd / "config/config-example.js", config)
    with config.open("a", encoding="utf-8") as f:
        f.write("exports.bindaddress = '127.0.0.1';\n")
        f.write("exports.reportjoins = false;\n")
        f.write("exports.nothrottle = true;\n")
        f.write("exports.noipchecks = true;\n")
        f.write("exports.backdoor = false;\n")
        f.write("exports.noguestsecurity = true;\n")
        f.write("exports.repl = false;\n")  # https://git.io/JStz2

    # Create the usergroups file
    usergroups = cwd / "config/usergroups.csv"
    with usergroups.open("w", encoding="utf-8") as f:
        f.write(f"{env('USERNAME')},&\n")
        f.write(f"{env('TESTS_MOD_USERNAME')},@\n")

    external_ps_port = env("PS_PORT", None)
    if external_ps_port:
        yield int(external_ps_port)
        return

    # Start the server
    port = unused_port()
    with subprocess.Popen(
        ["./pokemon-showdown", str(port)], cwd=cwd, stdout=subprocess.PIPE, text=True
    ) as ps:
        # Wait until the server is ready
        while True:
            line = ps.stdout.readline()  # type: ignore[union-attr]
            if not line:
                raise Exception("Pokemon Showdown stopped unexpectedly")
            if line.rstrip().endswith(f" listening on 127.0.0.1:{port}"):
                # Pokemon Showdown has started
                break

        yield port

        ps.terminate()


@pytest.fixture()
def showdown_connection(
    showdown_server,
) -> Callable[[], AbstractAsyncContextManager[Any]]:
    @asynccontextmanager
    async def make_connection(
        enable_commands: bool = False,
        *,
        username: str | None = None,
        password: str = "",
        avatar: str = "",
        statustext: str = "",
        rooms: list[str] | None = None,
        main_room: str = "lobby",
        command_character: str = ".",
        administrators: list[str] | None = None,
        webhooks: dict[str, str] | None = None,
    ) -> AsyncGenerator[Any, None]:
        if username is None:
            # Create and yield two default connections if no username is passed
            env = Env()
            env.read_env()

            bot_username = env("USERNAME")
            bot_password = env("PASSWORD")
            mod_username = env("TESTS_MOD_USERNAME")
            mod_password = env("TESTS_MOD_PASSWORD")

            bot_userid = utils.to_user_id(bot_username)
            mod_userid = utils.to_user_id(mod_username)

            async with make_connection(
                True, username=bot_username, password=bot_password
            ) as bot, make_connection(
                username=mod_username, password=mod_password
            ) as mod:
                await bot.await_message(
                    f'|queryresponse|userdetails|{{"id":"{mod_userid}"', startswith=True
                )
                await mod.await_message(
                    f'|queryresponse|userdetails|{{"id":"{bot_userid}"', startswith=True
                )
                yield bot, mod
                return

        url = f"ws://localhost:{showdown_server}/showdown/websocket"

        if rooms is None:
            rooms = ["lobby"]
        if administrators is None:
            administrators = ["parnassius"]
        if webhooks is None:
            webhooks = {"room1": "https://discord.com/api/webhooks/00000/aaaaa"}

        conn = TestConnection(
            url=url,
            username=username,
            password=password,
            avatar=avatar,
            statustext=statustext,
            rooms=rooms,
            main_room=main_room,
            command_character=command_character,
            administrators=administrators,
            webhooks=webhooks,
            unittesting=True,
        )

        if not enable_commands:
            conn.commands = {}

        asyncio.create_task(conn._start_websocket())

        rooms_to_join = {utils.to_room_id(room) for room in rooms}
        while rooms_to_join:
            msg = await conn.recv_queue.get()
            msg_parts = msg.split("\n")
            roomname = ""
            if msg_parts[0][0] == ">":
                roomname = msg_parts[0]
            roomid = utils.to_room_id(roomname)
            if roomid not in rooms_to_join:
                continue
            if any(x.startswith("|init|") for x in msg_parts):
                rooms_to_join.remove(roomid)

        try:
            yield conn
        finally:
            if conn.websocket is not None:
                for task in asyncio.all_tasks():
                    if not task.get_coro().__name__.startswith("test_"):  # type: ignore
                        task.cancel()
                await conn.websocket.close()

    return make_connection


# Database fixtures


@pytest.fixture(autouse=True)
def mock_database(mocker) -> None:
    database_instances: dict[str, Database] = {}

    def mock_database_init(self, dbname: str) -> None:
        if dbname == "veekun":
            dbpath = str(utils.get_config_file(f"{dbname}.sqlite"))
            engine = f"sqlite:///{dbpath}"
        else:
            engine = "sqlite://"  # :memory: database
        self.engine = create_engine(engine, future=True)
        self.session_factory = sessionmaker(self.engine, future=True)
        self.Session = scoped_session(self.session_factory)
        database_instances[dbname] = self

    @classmethod  # type: ignore[misc]
    def mock_database_open(cls, dbname: str = "database") -> Database:
        if dbname not in database_instances:
            cls(dbname)
            if dbname in database_metadata:
                # Create schemas
                database_metadata[dbname].create_all(database_instances[dbname].engine)
        return database_instances[dbname]

    mocker.patch.object(Database, "__init__", mock_database_init)
    mocker.patch.object(Database, "open", mock_database_open)


@pytest.fixture(scope="session")
def veekun_database() -> None:
    # csv_to_sqlite is an init_task, and as such it expects an instance of Connection as
    # its first parameter. However it is never used so we just pass None instead.
    asyncio.run(csv_to_sqlite(None))  # type: ignore[arg-type]

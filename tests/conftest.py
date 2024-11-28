from __future__ import annotations

import asyncio
import json
import subprocess
from collections import Counter
from collections.abc import AsyncGenerator, Callable, Generator, Mapping
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from enum import Enum
from pathlib import Path
from shutil import copy, rmtree
from time import time
from typing import Any

import pytest
from aiohttp.test_utils import unused_port
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from xprocess import ProcessStarter  # type: ignore[import-untyped]

import cerbottana.databases.database as d
from cerbottana import utils
from cerbottana.connection import Connection
from cerbottana.database import Database
from cerbottana.models.room import Room
from cerbottana.tasks import pokedex, veekun
from cerbottana.utils import env


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
        webhooks: dict[str, str],
    ) -> None:
        self.recv_queue: asyncio.Queue[str | bytes] = asyncio.Queue()
        self.send_queue: asyncio.Queue[str | bytes] = asyncio.Queue()

        super().__init__(
            url=url,
            username=username,
            password=password,
            avatar=avatar,
            statustext=statustext,
            rooms=rooms,
            main_room=main_room,
            command_character=command_character,
            webhooks=webhooks,
        )

    async def _start_websocket(self) -> None:
        while True:
            message = await self.recv_queue.get()
            if isinstance(message, str):
                print(f"<< {message}")
                await self._parse_text_message(message)
            elif isinstance(message, bytes):
                print(f"<b {message.decode()}")
                await self._parse_binary_message(message)

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

    async def send(self, message: str) -> None:
        print(f">> {message}")
        await self.send_queue.put(message)

    async def send_bytes(self, message: bytes) -> None:
        print(f">b {message.decode()}")
        await self.send_queue.put(message)

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
            await self.recv_queue.put("\n".join(item))

        await self.recv_queue.put(ControlMessage.PROCESS_MESSAGES)

    async def get_messages(self) -> Counter[str]:
        await self.recv_queue.put(ControlMessage.PROCESS_AND_REPLY)

        messages: Counter[str] = Counter()
        while True:
            message = await self.send_queue.get()
            print(message)
            if isinstance(message, str):
                messages.update([message])
            elif message == ControlMessage.PROCESSING_DONE:
                break

        return messages


@pytest.fixture()
def mock_connection() -> Callable[[], AbstractAsyncContextManager[Any]]:
    @asynccontextmanager
    async def make_mock_connection(
        *,
        username: str = "cerbottana",
        password: str = "",
        avatar: str = "",
        statustext: str = "",
        rooms: list[str] | None = None,
        main_room: str = "lobby",
        command_character: str = ".",
        webhooks: dict[str, str] | None = None,
    ) -> AsyncGenerator[Any, None]:
        if rooms is None:
            rooms = ["room1"]
        if webhooks is None:
            webhooks = {"room1": "https://discord.com/api/webhooks/00000/aaaaa"}

        conn = MockedConnection(
            url="",
            username=username,
            password=password,
            avatar=avatar,
            statustext=statustext,
            rooms=rooms,
            main_room=main_room,
            command_character=command_character,
            webhooks=webhooks,
        )

        task = asyncio.create_task(conn.open_connection())

        await conn.get_messages()

        try:
            yield conn
        finally:
            task.cancel()
            await task

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
        webhooks: dict[str, str],
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
            webhooks=webhooks,
        )

    async def _run_init_recurring_tasks(self) -> None:
        pass

    async def _parse_text_message(self, message: str) -> None:
        await super()._parse_text_message(message)

        await self.recv_queue.put(message)

    async def await_message(self, *messages: str, startswith: bool = False) -> str:
        while True:
            # Wait at most 5 seconds. It should be more than enough for normal cases,
            # and allows to easily identify eventual problems.
            async with asyncio.timeout(5):
                msg = await self.recv_queue.get()
            if startswith:
                cond = msg.startswith(messages)
            else:
                cond = msg in messages
            if cond:
                return msg


@pytest.fixture(scope="session")
def showdown_server(xprocess) -> Generator[int, None, None]:
    external_ps_port = env.int("PS_PORT", default=None)
    if external_ps_port:
        yield external_ps_port
        return

    cwd = Path(__file__).parent.parent / "pokemon-showdown"
    if cwd_ := env.str("CERBOTTANA_SHOWDOWN_PATH", default=""):
        cwd = Path(cwd_)
    port = unused_port()

    # Clone pokemon showdown
    def pull_pokemon_showdown() -> None:
        cwd.mkdir(exist_ok=True)
        subprocess.run(["git", "init", "--quiet"], cwd=cwd, timeout=5, check=True)
        subprocess.run(
            [
                "git",
                "pull",
                "--quiet",
                "--ff-only",
                "https://github.com/smogon/pokemon-showdown.git",
            ],
            cwd=cwd,
            timeout=300,
            check=True,
        )

    try:
        pull_pokemon_showdown()
    except subprocess.CalledProcessError:
        # Delete the directory and retry
        rmtree(cwd)
        pull_pokemon_showdown()

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
        f.write(f"{env.str('USERNAME')},~\n")
        f.write(f"{env.str('TESTS_MOD_USERNAME')},@\n")

    # Start the server
    class PokemonShowdownStarter(ProcessStarter):  # type: ignore  # noqa: PGH003
        pattern = rf" listening on 127\.0\.0\.1:{port}$"
        timeout = 600
        args = ("./pokemon-showdown", str(port))
        popen_kwargs: Mapping[str, str] = {"cwd": str(cwd)}
        terminate_on_interrupt = True
        max_read_lines = None

    xprocess.ensure("showdown", PokemonShowdownStarter)
    yield port
    xprocess.getinfo("showdown").terminate()


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
        webhooks: dict[str, str] | None = None,
    ) -> AsyncGenerator[Any, None]:
        if username is None:
            # Create and yield two default connections if no username is passed
            bot_username = env.str("USERNAME")
            bot_password = env.str("PASSWORD")
            mod_username = env.str("TESTS_MOD_USERNAME")
            mod_password = env.str("TESTS_MOD_PASSWORD")

            bot_userid = utils.to_user_id(bot_username)
            mod_userid = utils.to_user_id(mod_username)

            async with (
                make_connection(
                    True, username=bot_username, password=bot_password
                ) as bot,
                make_connection(username=mod_username, password=mod_password) as mod,
            ):
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
            webhooks=webhooks,
        )

        if not enable_commands:
            conn.commands = {}

        task = asyncio.create_task(conn.open_connection())

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
            task.cancel()
            await task

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
        self.engine = create_engine(engine)
        self.session_factory = sessionmaker(self.engine)
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


@pytest.fixture(scope="session", autouse=True)
def veekun_database() -> None:
    # csv_to_sqlite is an init_task, and as such it expects an instance of Connection as
    # its first parameter. However it is never used so we just pass None instead.
    asyncio.run(veekun.csv_to_sqlite(None))  # type: ignore[arg-type]


@pytest.fixture(scope="session", autouse=True)
def pokedex_database() -> None:
    # setup_database is an init_task, and as such it expects an instance of Connection
    # as its first parameter. However it is never used so we just pass None instead.
    asyncio.run(pokedex.setup_database(None))  # type: ignore[arg-type]

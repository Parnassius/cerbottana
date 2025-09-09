from __future__ import annotations

import asyncio
import json
import subprocess
from collections import Counter
from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from enum import Enum
from pathlib import Path
from shutil import rmtree
from time import time
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import cerbottana.databases.database as d
from cerbottana import utils
from cerbottana.connection import Connection
from cerbottana.database import Database
from cerbottana.models.room import Room
from cerbottana.tasks import pokedex, veekun
from cerbottana.utils import env


def pytest_collection_modifyitems(items):
    for item in items:
        # Mark tests using the showdown cli with `pytest.mark.integration`
        if "pokemon_showdown" in item.fixturenames:
            item.add_marker(pytest.mark.integration)


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
        base_url: str,
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
            base_url=base_url,
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
                await asyncio.gather(*self.running_tasks)
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
        base_url: str = "",
        webhooks: dict[str, str] | None = None,
    ) -> AsyncGenerator[Any]:
        if rooms is None:
            rooms = ["room1"]
        if webhooks is None:
            webhooks = {}

        conn = MockedConnection(
            url="",
            username=username,
            password=password,
            avatar=avatar,
            statustext=statustext,
            rooms=rooms,
            main_room=main_room,
            command_character=command_character,
            base_url=base_url,
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


class PokemonShowdown:
    def __init__(self) -> None:
        self.cwd = Path(__file__).parent.parent / "pokemon-showdown"
        if cwd := env.str("CERBOTTANA_SHOWDOWN_PATH", default=""):
            self.cwd = Path(cwd)

        try:
            self._pull_pokemon_showdown()
        except subprocess.CalledProcessError:
            # Delete the directory and retry
            rmtree(self.cwd)
            self._pull_pokemon_showdown()

        subprocess.run(["./build"], cwd=self.cwd, timeout=300, check=True)

    def _pull_pokemon_showdown(self) -> None:
        self.cwd.mkdir(exist_ok=True)
        subprocess.run(["git", "init", "--quiet"], cwd=self.cwd, timeout=5, check=True)
        subprocess.run(
            [
                "git",
                "pull",
                "--quiet",
                "--ff-only",
                "https://github.com/smogon/pokemon-showdown.git",
            ],
            cwd=self.cwd,
            timeout=300,
            check=True,
        )

    def validate_team(
        self, formatid: str, team: str, expected_valid: bool = True
    ) -> None:
        proc = subprocess.run(
            ["./pokemon-showdown", "validate-team", formatid],
            input=team,
            capture_output=True,
            cwd=self.cwd,
            timeout=30,
            text=True,
        )

        if expected_valid:
            assert proc.returncode == 0, proc.stderr
        else:
            assert proc.returncode != 0


@pytest.fixture(scope="session")
def pokemon_showdown() -> PokemonShowdown:
    return PokemonShowdown()


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

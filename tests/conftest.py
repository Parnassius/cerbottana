from __future__ import annotations

import asyncio
import json
from collections import Counter
from collections.abc import AsyncIterator, Callable, Generator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from types import TracebackType
from typing import Any

import freezegun
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import databases.database as d
import utils
from connection import Connection
from database import Database
from models.room import Room
from tasks.veekun import csv_to_sqlite

# pylint: disable=protected-access

database_metadata: dict[str, Any] = {
    "database": d.Base.metadata,
}


class TestConnection(Connection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.recv_queue: RecvQueue
        self.send_queue: SendQueue


class RecvQueue(asyncio.Queue[tuple[int, str]]):  # pylint: disable=inherit-non-class
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
            await self.put((0, "\n".join(item)))

        await self.put((1, ""))  # process message queues
        await self.join()

    async def close(self) -> None:
        await self.put((2, ""))  # close fake websocket connection
        await self.join()


class SendQueue(asyncio.Queue[str]):  # pylint: disable=inherit-non-class
    # pylint: disable=too-few-public-methods
    def get_all(self) -> Counter[str]:
        messages: Counter[str] = Counter()
        try:
            while True:
                messages.update([self.get_nowait()])
        except asyncio.queues.QueueEmpty:
            pass
        return messages


@pytest.fixture()
def mock_connection(
    mocker,
) -> Callable[[], AbstractAsyncContextManager[TestConnection]]:
    @asynccontextmanager
    async def make_mock_connection(
        *,
        url: str = "ws://localhost:80/showdown/websocket",
        username: str = "cerbottana",
        password: str = "",
        avatar: str = "",
        statustext: str = "",
        rooms: list[str] | None = None,
        main_room: str = "lobby",
        command_character: str = ".",
        administrators: list[str] | None = None,
    ) -> AsyncIterator[TestConnection]:
        class MockProtocol:
            def __init__(self, recv_queue: RecvQueue, send_queue: SendQueue) -> None:
                self.recv_queue = recv_queue
                self.send_queue = send_queue

            def __await__(self) -> "MockProtocol":
                return self

            async def __aiter__(self) -> AsyncIterator[str]:
                while True:
                    msg = await self.recv()
                    if msg:
                        yield msg
                    self.recv_queue.task_done()

            async def recv(self) -> str:
                msg_type, msg = await self.recv_queue.get()

                if msg_type == 0:
                    pass
                elif msg_type == 1:
                    for room in list(Room._instances.get(conn, {}).values()):
                        await room.process_all_messages()
                elif msg_type == 2:
                    # cancel all running tasks
                    for task in asyncio.all_tasks():
                        if not task.get_coro().__name__.startswith("test_"):
                            task.cancel()
                    if conn.websocket is not None:
                        await conn.websocket.close()

                return msg

            async def send(self, message: str) -> None:
                await self.send_queue.put(message)

            async def close(self) -> None:
                pass

        class MockConnect:
            def __init__(self, url: str, **kwargs: Any) -> None:
                pass

            async def __aiter__(self) -> AsyncIterator[MockProtocol]:
                while True:
                    async with self as protocol:
                        yield protocol

            async def __aenter__(self) -> MockProtocol:
                return await self

            async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc_value: BaseException | None,
                traceback: TracebackType | None,
            ) -> None:
                pass

            def __await__(self) -> Generator[Any, None, MockProtocol]:
                # Create a suitable iterator by calling __await__ on a coroutine.
                return self.__await_impl__().__await__()

            async def __await_impl__(self) -> MockProtocol:
                return MockProtocol(recv_queue, send_queue)

        mocker.patch("websockets.client.connect", MockConnect)

        recv_queue: RecvQueue = RecvQueue()
        send_queue: SendQueue = SendQueue()

        if rooms is None:
            rooms = ["room1"]
        if administrators is None:
            administrators = ["parnassius"]

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
            unittesting=True,
        )

        asyncio.create_task(conn._start_websocket())

        await recv_queue.add_messages(["|updateuser|*cerbottana|1|0|{}"])

        # Clear send queue
        send_queue.get_all()

        conn.recv_queue = recv_queue
        conn.send_queue = send_queue

        try:
            yield conn
        finally:
            await recv_queue.close()

    return make_mock_connection


@pytest.fixture(autouse=True)
def mock_database(mocker) -> None:
    database_instances: dict[str, Database] = {}

    def mock_database_init(self, dbname: str) -> None:
        if dbname == "veekun":
            engine = f"sqlite:///{dbname}.sqlite"
        else:
            engine = "sqlite://"  # :memory: database
        self.engine = create_engine(engine, future=True)
        self.session_factory = sessionmaker(self.engine, future=True)
        self.Session = scoped_session(self.session_factory)
        database_instances[dbname] = self

    @classmethod  # type: ignore[misc]
    def mock_database_open(cls, dbname: str = "database") -> Database:
        if dbname not in database_instances:
            cls(dbname)  # pylint: disable=too-many-function-args
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


# Configure freezegun to ignore the connection module
# This is needed because the `send` method requires 0.1s between each message
freezegun.configure(extend_ignore_list=["connection"])  # type: ignore[attr-defined]

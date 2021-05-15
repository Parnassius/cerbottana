from __future__ import annotations

import asyncio
import json
import threading
from collections import Counter
from collections.abc import AsyncIterator, Callable, Generator
from queue import Empty as EmptyQueue
from queue import Queue
from types import TracebackType
from typing import TYPE_CHECKING, Any, Tuple

import freezegun
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from websockets.exceptions import ConnectionClosedOK

import databases.database as d
import utils
from connection import Connection
from database import Database
from tasks.veekun import csv_to_sqlite

if TYPE_CHECKING:
    BaseRecvQueue = Queue[Tuple[int, str]]
    BaseSendQueue = Queue[str]
else:
    BaseRecvQueue = Queue
    BaseSendQueue = Queue

database_metadata: dict[str, Any] = {
    "database": d.Base.metadata,
}


class RecvQueue(BaseRecvQueue):
    def add_user_join(
        self,
        room: str,
        user: str,
        rank: str = " ",
        *,
        group: str = " ",
    ) -> None:
        roomid = utils.to_room_id(room)
        userid = utils.to_user_id(user)

        self.add_messages(
            [
                f">{roomid}",
                f"|j|{rank}{userid}",
            ]
        )
        self.add_queryresponse_userdetails(user, group=group, rooms={roomid: rank})

    def add_user_namechange(
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

        self.add_messages(
            [
                f">{roomid}",
                f"|n|{rank}{userid}|{olduserid}",
            ]
        )
        self.add_queryresponse_userdetails(user, group=group, rooms={roomid: rank})

    def add_user_leave(self, room: str, user: str) -> None:
        roomid = utils.to_room_id(room)
        userid = utils.to_user_id(user)

        self.add_messages(
            [
                f">{roomid}",
                f"|l|{userid}",
            ]
        )

    def add_queryresponse_userdetails(
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

        self.add_messages(
            [
                f"|queryresponse|userdetails|{json.dumps(data)}",
            ]
        )

    def add_messages(self, *items: list[str]) -> None:
        for item in items:
            self.put((0, "\n".join(item)))

        self.put((1, ""))  # await conn._parse_message() tasks
        self.join()

    def close(self) -> None:
        self.put((2, ""))  # close fake websocket connection


class SendQueue(BaseSendQueue):
    # pylint: disable=too-few-public-methods
    def get_all(self) -> Counter[str]:
        messages: Counter[str] = Counter()
        try:
            while True:
                messages.update([self.get_nowait()])
        except EmptyQueue:
            pass
        return messages


@pytest.fixture()
def mock_connection(
    mocker,
) -> Callable[[], tuple[Connection, RecvQueue, SendQueue]]:
    def make_mock_connection(
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
        domain: str = "http://localhost:8080/",
    ) -> tuple[Connection, RecvQueue, SendQueue]:
        class MockProtocol:
            def __init__(self, recv_queue: RecvQueue, send_queue: SendQueue) -> None:
                self.recv_queue = recv_queue
                self.send_queue = send_queue

            def __await__(self) -> "MockProtocol":
                return self

            async def __aiter__(self) -> AsyncIterator[str]:
                try:
                    while True:
                        msg = await self.recv()
                        if msg:
                            yield msg
                except ConnectionClosedOK:
                    return

            async def recv(self) -> str:
                msg_type, msg = self.recv_queue.get()

                if msg_type == 0:
                    pass
                elif msg_type == 1:
                    # await conn._parse_message() tasks
                    await asyncio.gather(
                        *[
                            task
                            for task in asyncio.all_tasks()
                            if task.get_coro().__name__ == "_parse_message"
                        ]
                    )
                elif msg_type == 2:
                    # cancel all running tasks
                    for task in asyncio.all_tasks():
                        task.cancel()
                    raise ConnectionClosedOK(1000, "Connection closed")

                self.recv_queue.task_done()
                return msg

            async def send(self, message: str) -> None:
                self.send_queue.put(message)

        class MockConnect:
            def __init__(self, url: str, **kwargs: Any) -> None:
                pass

            # async with connect(...)

            async def __aenter__(self) -> MockProtocol:
                return await self

            async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc_value: BaseException | None,
                traceback: TracebackType | None,
            ) -> None:
                pass

            # await connect(...)

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

        conn = Connection(
            url=url,
            username=username,
            password=password,
            avatar=avatar,
            statustext=statustext,
            rooms=rooms,
            main_room=main_room,
            command_character=command_character,
            administrators=administrators,
            domain=domain,
            unittesting=True,
        )

        threading.Thread(target=conn.open_connection).start()

        recv_queue.add_messages(["|updateuser|*cerbottana|1|0|{}"])

        # Clear send queue
        send_queue.get_all()

        return (conn, recv_queue, send_queue)

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

    @classmethod  # type: ignore
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

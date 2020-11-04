from __future__ import annotations

import asyncio
import threading
from queue import Queue
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Type,
)

import pytest
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from websockets import ConnectionClosedOK

import databases.database as d
import databases.logs as l
from connection import Connection
from database import Database

if TYPE_CHECKING:
    BaseMessagesQueue = Queue[Tuple[int, str]]  # pylint: disable=unsubscriptable-object
else:
    BaseMessagesQueue = Queue


database_metadata: Dict[str, Any] = {
    "database": d.db.metadata,
    "logs": l.db.metadata,
}


class MessagesQueue(BaseMessagesQueue):
    def add_messages(self, *items: List[str]) -> None:
        for item in items:
            self.put((0, "\n".join(item)))

        self.put((1, ""))  # await conn._parse_message() tasks
        self.join()

    def close(self) -> None:
        self.put((2, ""))  # close fake websocket connection


@pytest.fixture()
def mock_connection(
    mocker,
) -> Callable[[], Tuple[Connection, MessagesQueue]]:
    def make_mock_connection(
        *,
        url: str = "ws://localhost:80/showdown/websocket",
        username: str = "cerbottana",
        password: str = "",
        avatar: str = "",
        statustext: str = "",
        rooms: Optional[List[str]] = None,
        private_rooms: Optional[List[str]] = None,
        main_room: Optional[str] = None,
        command_character: str = ".",
        administrators: Optional[List[str]] = None,
        domain: str = "http://localhost:8080/",
    ) -> Tuple[Connection, MessagesQueue]:
        class MockProtocol:
            def __init__(self, messages: MessagesQueue) -> None:
                self.messages = messages

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
                msg_type, msg = self.messages.get()

                if msg_type == 0:
                    pass
                elif msg_type == 1:
                    # await conn._parse_message() tasks
                    await asyncio.gather(
                        *[  # pylint: disable=protected-access
                            task
                            for task in asyncio.all_tasks(conn.loop)
                            if task._coro.__name__ == "_parse_message"  # type: ignore
                        ]
                    )
                elif msg_type == 2:
                    raise ConnectionClosedOK(1000, "Connection closed")

                self.messages.task_done()
                return msg

            async def send(self, message: str) -> None:
                pass

        class MockConnect:
            def __init__(self, url: str, **kwargs: Any) -> None:
                pass

            # async with connect(...)

            async def __aenter__(self) -> MockProtocol:
                return await self

            async def __aexit__(
                self,
                exc_type: Optional[Type[BaseException]],
                exc_value: Optional[BaseException],
                traceback: Optional[TracebackType],
            ) -> None:
                pass

            # await connect(...)

            def __await__(self) -> Generator[Any, None, MockProtocol]:
                # Create a suitable iterator by calling __await__ on a coroutine.
                return self.__await_impl__().__await__()

            async def __await_impl__(self) -> MockProtocol:
                return MockProtocol(queue)

        mocker.patch("websockets.connect", MockConnect)

        database_instances: Dict[str, Database] = {}

        def mock_database_init(self, dbname: str) -> None:
            self.engine = create_engine("sqlite://")  # :memory: database
            self.metadata = MetaData(bind=self.engine)
            self.session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(self.session_factory)
            database_instances[dbname] = self

        @classmethod  # type: ignore
        def mock_database_open(cls, dbname: str = "database") -> Database:
            if dbname not in database_instances:
                cls(dbname)  # pylint: disable=too-many-function-args
                if dbname in database_metadata:
                    # Create schemas
                    database_metadata[dbname].create_all(
                        database_instances[dbname].engine
                    )
            return database_instances[dbname]

        mocker.patch.object(Database, "__init__", mock_database_init)
        mocker.patch.object(Database, "open", mock_database_open)

        queue: MessagesQueue = MessagesQueue()

        conn = Connection(
            url,
            username,
            password,
            avatar,
            statustext,
            rooms or [],
            private_rooms or [],
            main_room,
            command_character,
            administrators or [],
            domain,
            True,  # unittesting
        )

        threading.Thread(target=conn.open_connection).start()

        queue.add_messages(["|updateuser|*cerbottana|1|0|{}"])

        return (conn, queue)

    return make_mock_connection

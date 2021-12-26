from __future__ import annotations

import asyncio
import json
from collections import Counter
from collections.abc import Awaitable, Callable
from enum import Enum
from time import time
from typing import Any

import aiohttp
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import cerbottana.databases.database as d
from cerbottana import utils
from cerbottana.connection import Connection
from cerbottana.database import Database
from cerbottana.models.room import Room
from cerbottana.tasks.veekun import csv_to_sqlite

# pylint: disable=protected-access

database_metadata: dict[str, Any] = {
    "database": d.Base.metadata,
}


class ControlMessage(bytes, Enum):
    # server to client
    PROCESS_MESSAGES = b"process_messages"
    PROCESS_AND_REPLY = b"process_and_reply"

    # client to server
    PROCESSING_DONE = b"processing_done"


class TestConnection(Connection):
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
) -> Callable[[Callable[[ServerWs, TestConnection], Awaitable[None]]], Awaitable[None]]:
    async def make_mock_connection(
        server_handler: Callable[[ServerWs, TestConnection], Awaitable[None]],
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

        await conn._start_websocket()

        if conn.websocket is not None:
            exc = conn.websocket.exception()
            if exc:
                raise exc

    return make_mock_connection


@pytest.fixture(autouse=True)
def mock_database(mocker) -> None:
    database_instances: dict[str, Database] = {}

    def mock_database_init(self, dbname: str) -> None:
        if dbname == "veekun":
            dbpath = utils.get_config_file(f"{dbname}.sqlite")
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

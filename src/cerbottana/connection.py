from __future__ import annotations

import asyncio
import re
import signal
from collections import defaultdict
from collections.abc import Coroutine
from contextvars import Context
from time import time
from typing import TYPE_CHECKING, Any

import aiohttp

from cerbottana import utils
from cerbottana.handlers import handlers
from cerbottana.models.protocol_message import ProtocolMessage
from cerbottana.models.room import Room
from cerbottana.models.user import User
from cerbottana.plugins import Command, commands
from cerbottana.tasks import background_tasks, init_tasks
from cerbottana.typedefs import RoomId

if TYPE_CHECKING:
    from cerbottana.typedefs import Tier


class Connection:
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
        self.url = url
        self.username = username
        self.password = password
        self.avatar = avatar
        self.statustext = statustext
        self.autojoin_rooms = {utils.to_room_id(x) for x in rooms}
        self.rooms: dict[RoomId, Room] = {}
        self.main_room = Room.get(self, main_room)
        self.command_character = command_character
        self.base_url = base_url
        self.webhooks = {utils.to_room_id(room): url for room, url in webhooks.items()}
        self.public_roomids: set[str] = set()
        self.init_tasks = init_tasks
        self.background_tasks = background_tasks
        self.handlers = handlers
        self.commands = commands
        self.active_commands: dict[Room | User, dict[asyncio.Task[None], Command]] = (
            defaultdict(dict)
        )
        self._client_session: aiohttp.ClientSession | None = None
        self.timestamp: float = 0
        self.lastmessage: float = 0
        self.websocket: aiohttp.ClientWebSocketResponse | None = None
        self.connection_start: float | None = None
        self.tiers: dict[str, Tier] = {}
        self.running_tasks: set[asyncio.Task[Any]] = set()  # type: ignore[explicit-any]

    @property
    def client_session(self) -> aiohttp.ClientSession:
        if self._client_session is None:
            self._client_session = aiohttp.ClientSession(
                cookie_jar=aiohttp.DummyCookieJar()
            )
        return self._client_session

    async def open_connection(self) -> None:
        signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))
        try:
            await self._start_websocket()
        except asyncio.CancelledError:
            pass
        if self._client_session is not None:
            await self._client_session.close()

    async def _start_websocket(self) -> None:
        await self._run_init_background_tasks()

        connection_retries = 0
        while True:
            try:
                async with self.client_session.ws_connect(
                    self.url, max_msg_size=0, heartbeat=60
                ) as websocket:
                    self.websocket = websocket
                    self.connection_start = time()
                    async for message in websocket:
                        if message.type == aiohttp.WSMsgType.TEXT:
                            print(f"<< {message.data}")
                            await self._parse_text_message(message.data)
                        elif message.type == aiohttp.WSMsgType.BINARY:
                            print(f"<b {message.data.decode()}")
                            await self._parse_binary_message(message.data)
                        elif message.type == aiohttp.WSMsgType.ERROR:
                            break
            except (aiohttp.ClientConnectionError, ConnectionResetError):
                pass

            for task in self.running_tasks:
                task.cancel()

            if (
                self.connection_start is not None
                and time() - self.connection_start > 60
            ):
                connection_retries = 0

            self.websocket = None
            self.connection_start = None

            if connection_retries < 12:
                # Cap the backoff to 2**12 seconds, which is a little over one hour
                connection_retries += 1
            backoff = 2**connection_retries
            print(f"Connection closed, retrying in {backoff} seconds")
            await asyncio.sleep(backoff)

    async def _run_init_background_tasks(self) -> None:
        for prio in range(1, 6):
            async with asyncio.TaskGroup() as tg:
                for task_prio, func in self.init_tasks:
                    if prio != task_prio:
                        continue
                    tg.create_task(func(self))

        for rtask in self.background_tasks:
            self.create_task(rtask(self))

    async def _parse_text_message(self, message: str) -> None:
        """Extracts a Room object from a raw message.

        Args:
            message (str): Raw message received from the websocket.
        """
        if not message:
            return

        init = False

        roomname = ""
        if message[0] == ">":
            roomname = message.split("\n")[0]
        roomid = utils.to_room_id(roomname)
        room = Room.get(self, roomid)

        for raw_msg in message.split("\n"):
            if language := re.match(r"This room's primary language is (.*)", raw_msg):
                room.language_name = language.group(1)
                continue

            if not raw_msg or raw_msg[0] != "|":
                continue

            msg = ProtocolMessage(room, raw_msg[1:])

            if msg.type == "init":
                init = True

            if init and msg.type in ["tournament"]:
                return

            room.add_message_to_queue(msg)

    async def _parse_binary_message(self, message: bytes) -> None:
        err = f"Received unexpected binary message {message!r}"
        raise TypeError(err)

    async def _send_message_delay(self) -> None:
        now = time()
        if now - self.lastmessage < 0.1:
            await asyncio.sleep(0.1)
        self.lastmessage = now

    async def send(self, message: str) -> None:
        """Sends a raw unescaped message to the websocket.

        Args:
            message (str): String to send.
        """
        if self.websocket is not None:
            await self._send_message_delay()
            print(f">> {message}")
            await self.websocket.send_str(message)

    def create_task[T](  # type: ignore[explicit-any]
        self,
        coro: Coroutine[Any, Any, T],
        *,
        name: str | None = None,
        context: Context | None = None,
    ) -> asyncio.Task[T]:
        task = asyncio.create_task(coro, name=name, context=context)
        self.running_tasks.add(task)
        task.add_done_callback(self.running_tasks.discard)
        return task

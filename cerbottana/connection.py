from __future__ import annotations

import asyncio
import re
from time import time
from typing import TYPE_CHECKING

import aiohttp

from . import utils
from .handlers import handlers
from .models.protocol_message import ProtocolMessage
from .models.room import Room
from .plugins import commands
from .tasks import init_tasks, recurring_tasks
from .typedefs import RoomId

if TYPE_CHECKING:
    from .typedefs import Tier


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
        webhooks: dict[str, str],
        unittesting: bool = False,
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
        self.webhooks = {utils.to_room_id(room): url for room, url in webhooks.items()}
        self.unittesting = unittesting
        self.public_roomids: set[str] = set()
        self.init_tasks = init_tasks
        self.recurring_tasks = recurring_tasks
        self.handlers = handlers
        self.commands = commands
        self.timestamp: float = 0
        self.lastmessage: float = 0
        self.websocket: aiohttp.ClientWebSocketResponse | None = None
        self.connection_start: float | None = None
        self.tiers: dict[str, Tier] = {}

    async def open_connection(self) -> None:
        try:
            await self._start_websocket()
        except asyncio.CancelledError:
            pass

    async def _start_websocket(self) -> None:
        for prio in range(1, 6):
            async with asyncio.TaskGroup() as tg:
                for task_prio, func, skip_unittesting in self.init_tasks:
                    if prio != task_prio or self.unittesting and skip_unittesting:
                        continue
                    tg.create_task(func(self))

        if not self.unittesting:
            for rtask in self.recurring_tasks:
                asyncio.create_task(rtask(self))

        async with aiohttp.ClientSession() as session:
            try:
                async with session.ws_connect(
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
            except aiohttp.ClientConnectionError:
                pass

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
                room.language = language.group(1)
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
        raise Exception("Received unexpected binary message")

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

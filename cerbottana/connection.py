from __future__ import annotations

import asyncio
import re
from time import time
from typing import TYPE_CHECKING

import websockets.client
from websockets.exceptions import WebSocketException

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
        administrators: list[str],
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
        self.administrators = {utils.to_user_id(user) for user in administrators}
        self.unittesting = unittesting
        self.public_roomids: set[str] = set()
        self.init_tasks = init_tasks
        self.recurring_tasks = recurring_tasks
        self.handlers = handlers
        self.commands = commands
        self.timestamp: float = 0
        self.lastmessage: float = 0
        self.loop: asyncio.AbstractEventLoop | None = None
        self.websocket: websockets.client.WebSocketClientProtocol | None = None
        self.connection_start: float | None = None
        self.tiers: dict[str, Tier] = {}

    def open_connection(self) -> None:
        try:
            asyncio.run(self._start_websocket())
        except asyncio.CancelledError:
            pass

    async def _start_websocket(self) -> None:
        self.loop = asyncio.get_running_loop()
        itasks: list[asyncio.Task[None]]
        for prio in range(5):
            itasks = []
            for func, skip_unittesting in [
                t[1:3] for t in self.init_tasks if t[0] == prio + 1
            ]:
                if self.unittesting and skip_unittesting:
                    continue
                itasks.append(asyncio.create_task(func(self)))
            await asyncio.gather(*itasks)

        if not self.unittesting:
            for rtask in self.recurring_tasks:
                asyncio.create_task(rtask(self))

        async for websocket in websockets.client.connect(
            self.url, ping_interval=None, max_size=None
        ):
            try:
                self.websocket = websocket
                self.connection_start = time()
                async for message in websocket:
                    if isinstance(message, str):
                        print(f"<< {message}")
                        await self._parse_message(message)
            except (
                WebSocketException,
                OSError,  # https://github.com/aaugustin/websockets/issues/593
            ):
                pass

    async def _parse_message(self, message: str) -> None:
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

    async def send(self, message: str) -> None:
        """Sends a raw unescaped message to the websocket.

        Args:
            message (str): String to send.
        """
        print(f">> {message}")
        now = time()
        if now - self.lastmessage < 0.1:
            await asyncio.sleep(0.1)
        self.lastmessage = now
        if self.websocket is not None:
            await self.websocket.send(message)

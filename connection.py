from __future__ import annotations

import asyncio
import re
from time import time
from typing import TYPE_CHECKING, Dict, List, Optional
from weakref import WeakValueDictionary

import websockets

import utils
from handlers import handlers
from models.room import Room
from models.user import User
from plugins import commands
from tasks import init_tasks, recurring_tasks
from typedefs import RoomId, UserId

if TYPE_CHECKING:
    from typedefs import TiersDict


class Connection:
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        avatar: str,
        statustext: str,
        rooms: List[str],
        private_rooms: List[str],
        main_room: Optional[str],
        command_character: str,
        administrators: List[str],
        domain: str,
    ) -> None:
        self.url = url
        self.username = username
        self.password = password
        self.avatar = avatar
        self.statustext = statustext
        self.rooms: Dict[RoomId, Room] = {}  # roomid, Room
        for roomid in [utils.to_room_id(room) for room in rooms]:
            self.rooms[roomid] = Room(self, roomid, is_private=False, autojoin=True)
        for roomid in [utils.to_room_id(room) for room in private_rooms]:
            self.rooms[roomid] = Room(self, roomid, is_private=True, autojoin=True)
        self.main_room = Room.get(self, main_room) if main_room else None
        self.command_character = command_character
        self.administrators = [utils.to_user_id(user) for user in administrators]
        self.domain = domain
        self.users: WeakValueDictionary[  # pylint: disable=unsubscriptable-object
            UserId, User
        ] = WeakValueDictionary()
        self.init_tasks = init_tasks
        self.recurring_tasks = recurring_tasks
        self.handlers = handlers
        self.commands = commands
        self.timestamp: float = 0
        self.lastmessage: float = 0
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.websocket: Optional[websockets.client.WebSocketClientProtocol] = None
        self.connection_start: Optional[float] = None
        self.tiers: List[TiersDict] = []

    def open_connection(self) -> None:
        self.loop = asyncio.new_event_loop()
        try:
            self.loop.run_until_complete(self._start_websocket())
        except asyncio.CancelledError:
            pass

    async def _start_websocket(self) -> None:
        itasks: List[asyncio.Task[None]]
        for prio in range(5):
            itasks = []
            for func in [t[1] for t in self.init_tasks if t[0] == prio + 1]:
                itasks.append(asyncio.create_task(func(self)))
            for itask in itasks:
                await itask

        for rtask in self.recurring_tasks:
            asyncio.create_task(rtask(self))

        try:
            async with websockets.connect(
                self.url,
                # these two should be fixed by the next websockets release
                # https://github.com/aaugustin/websockets/commit/93ad88a9a8fe2ea8d96fb1d2a0f1625a3c5fee7c
                ping_interval=None,  # type: ignore
                max_size=None,  # type: ignore
            ) as websocket:
                self.websocket = websocket
                self.connection_start = time()
                async for message in websocket:
                    if isinstance(message, str):
                        print(f"<< {message}")
                        asyncio.ensure_future(self._parse_message(message))
        except (
            websockets.exceptions.WebSocketException,
            OSError,  # https://github.com/aaugustin/websockets/issues/593
        ):
            pass

    async def _parse_message(self, message: str) -> None:
        """Extracts a Room object from a raw message.

        Args:
            message (raw): Raw message received from the websocket.
        """
        if not message:
            return

        init = False

        roomname = ""
        if message[0] == ">":
            roomname = message.split("\n")[0]
        roomid = utils.to_room_id(roomname)
        room = Room.get(self, roomid)

        # Try to set modchat if it's a public room and cerbottana has relevant auth
        if room.roombot and not room.is_private:
            await room.try_modchat()

        for msg in message.split("\n"):

            language = re.match(r"This room's primary language is (.*)", msg)
            if language:
                room.language = language.group(1)
                continue

            if not msg or msg[0] != "|":
                continue

            parts = msg.split("|")

            command = parts[1]

            if command == "init":
                init = True

            if init and command in ["tournament"]:
                return

            if command in self.handlers:
                tasks: List[asyncio.Task[None]] = []
                for func in self.handlers[command]:
                    tasks.append(asyncio.create_task(func(self, room, *parts[2:])))
                for task in tasks:
                    await task

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

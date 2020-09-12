from __future__ import annotations

import asyncio
from queue import Empty as EmptyQueue
from queue import SimpleQueue
from time import time
from typing import Dict, List, Optional
from weakref import WeakValueDictionary

import websockets
from environs import Env
from typing_extensions import TypedDict

import utils
from handlers import handlers
from models.room import Room
from models.user import User
from plugins import commands
from tasks import init_tasks, recurring_tasks

TiersDict = TypedDict(
    "TiersDict",
    {
        "name": str,
        "section": str,
        "random": bool,
    },
)


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
        command_character: str,
        administrators: List[str],
        domain: str,
    ) -> None:
        self.url = url
        self.username = username
        self.password = password
        self.avatar = avatar
        self.statustext = statustext
        self.rooms: Dict[str, Room] = {}  # roomid, Room
        for roomid in rooms:
            self.rooms[roomid] = Room(self, roomid, is_private=False)
        for roomid in private_rooms:
            self.rooms[roomid] = Room(self, roomid, is_private=True)
        self.command_character = command_character
        self.administrators = administrators
        self.domain = domain
        self.users: WeakValueDictionary[  # pylint: disable=unsubscriptable-object
            str, User
        ] = WeakValueDictionary()
        self.init_tasks = init_tasks
        self.recurring_tasks = recurring_tasks
        self.handlers = handlers
        self.commands = commands
        self.timestamp: float = 0
        self.lastmessage: float = 0
        self.queue: Optional[SimpleQueue[str]] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.websocket: Optional[websockets.client.WebSocketClientProtocol] = None
        self.connection_start: Optional[float] = None
        self.tiers: List[TiersDict] = []

    def open_connection(self, queue: SimpleQueue[str]) -> None:
        self.queue = queue
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
                    if self.queue is not None:
                        try:
                            data: Optional[str] = self.queue.get(False)
                        except EmptyQueue:
                            data = None

                        print(data)

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


env = Env()
env.read_env()

CONNECTION = Connection(
    ("wss" if env("SHOWDOWN_PORT") == "443" else "ws")
    + "://"
    + env("SHOWDOWN_HOST")
    + ":"
    + env("SHOWDOWN_PORT")
    + "/showdown/websocket",
    env("USERNAME"),
    env("PASSWORD"),
    env("AVATAR", ""),
    env("STATUSTEXT", ""),
    env.list("ROOMS", []),
    env.list("PRIVATE_ROOMS", []),
    env("COMMAND_CHARACTER"),
    env.list("ADMINISTRATORS", []),
    env("DOMAIN"),
)

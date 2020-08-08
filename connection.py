from __future__ import annotations

import asyncio
from datetime import datetime
from queue import Empty as EmptyQueue
from queue import SimpleQueue
from time import time
from typing import Dict, List, Optional

import pytz
import websockets
from environs import Env

import utils
from handlers import handlers
from plugins import commands
from room import Room
from tasks import init_tasks, recurring_tasks


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
        self.rooms = rooms
        self.private_rooms = private_rooms
        self.command_character = command_character
        self.administrators = administrators
        self.domain = domain
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
        self.tiers: List[Dict[str, str]] = []

    def open_connection(self, queue: SimpleQueue[str]) -> None:
        self.queue = queue
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self.start_websocket())

    async def start_websocket(self) -> None:
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
                ping_interval=None,  # type: ignore # should be fixed by https://github.com/aaugustin/websockets/commit/93ad88a9a8fe2ea8d96fb1d2a0f1625a3c5fee7c
                max_size=None,  # type: ignore # should be fixed by https://github.com/aaugustin/websockets/commit/93ad88a9a8fe2ea8d96fb1d2a0f1625a3c5fee7c
            ) as websocket:
                self.websocket = websocket
                self.connection_start = time()
                while True:
                    if self.queue is not None:
                        try:
                            data: Optional[str] = self.queue.get(False)
                        except EmptyQueue:
                            data = None

                        print(data)

                    message: str = await websocket.recv()
                    print(f"<< {message}")
                    asyncio.ensure_future(self.parse_message(message))
        except:  # lgtm [py/catch-base-exception]
            pass

    async def parse_message(self, message: str) -> None:
        if not message:
            return

        init = False

        room = ""
        if message[0] == ">":
            room = message.split("\n")[0]
        roomid = utils.to_room_id(room)

        if roomid in self.rooms:
            await self.try_modchat(roomid)

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
                    tasks.append(asyncio.create_task(func(self, roomid, *parts[2:])))
                for task in tasks:
                    await task

    async def try_modchat(self, roomid: str) -> None:
        room = Room.get(roomid)
        if room and not room.modchat and room.no_mods_online:
            tz = pytz.timezone("Europe/Rome")
            timestamp = datetime.now(tz)
            minutes = timestamp.hour * 60 + timestamp.minute
            # 00:30 - 08:00
            if 30 <= minutes < 8 * 60 and room.no_mods_online + (7 * 60) < time():
                await self.send_message(roomid, "/modchat +", False)

    async def send_rankhtmlbox(self, rank: str, room: str, message: str) -> None:
        await self.send_message(room, f"/addrankhtmlbox {rank}, {message}", False)

    async def send_htmlbox(
        self,
        room: Optional[str],
        user: Optional[str],
        message: str,
        simple_message: str = "",
    ) -> None:
        if room is not None:
            await self.send_message(room, f"/addhtmlbox {message}", False)
        elif user is not None:
            room = utils.can_pminfobox_to(self, utils.to_user_id(user))
            if room is not None:
                await self.send_message(room, f"/pminfobox {user}, {message}", False)
            else:
                if simple_message == "":
                    simple_message = "Questo comando è disponibile in PM "
                    simple_message += "solo se sei online in una room dove sono Roombot"
                await self.send_pm(user, simple_message)

    async def send_reply(
        self, room: Optional[str], user: str, message: str, escape: bool = True
    ) -> None:
        if room is None:
            await self.send_pm(user, message)
        else:
            await self.send_message(room, message, escape)

    async def send_message(self, room: str, message: str, escape: bool = True) -> None:
        if escape:
            if message[0] == "/":
                message = "/" + message
            elif message[0] == "!":
                message = " " + message
        await self.send(f"{room}|{message}")

    async def send_pm(self, user: str, message: str, escape: bool = True) -> None:
        if escape and message[0] == "/":
            message = "/" + message
        await self.send(f"|/w {utils.to_user_id(user)}, {message}")

    async def send(self, message: str) -> None:
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
    env.list("ROOMS"),
    env.list("PRIVATE_ROOMS"),
    env("COMMAND_CHARACTER"),
    env.list("ADMINISTRATORS"),
    env("DOMAIN"),
)

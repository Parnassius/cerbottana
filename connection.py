from typing import Optional, List

import asyncio
import os
from datetime import datetime
from time import time
import re

import pytz
import websockets

import utils

from handlers import handlers
from plugins import plugins

from room import Room


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
        self.handlers = handlers
        self.commands = plugins
        self.timestamp: float = 0
        self.lastmessage: float = 0
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.websocket = None
        self.connection_start: Optional[float] = None
        self.tiers = None

    def open_connection(self) -> None:
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self.start_websocket())

    async def start_websocket(self) -> None:
        try:
            async with websockets.connect(self.url, ping_interval=None) as websocket:
                self.websocket = websocket
                self.connection_start = time()
                while True:
                    message: str = await websocket.recv()
                    print("<< {}".format(message))
                    asyncio.ensure_future(self.parse_message(message))
        except:
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

            if roomid in self.rooms:
                match = re.match(r"^\(.+ set modchat to (.*)\)$", msg)
                if not match:
                    match = re.match(
                        r"^\|error\|Modchat is already set to (.*)\.$", msg
                    )

                if match:
                    Room.get(roomid).modchat = len(
                        match.group(1)
                    ) == 1 and utils.is_voice(match.group(1))

            if not msg or msg[0] != "|":
                continue

            parts = msg.split("|")

            command = parts[1]

            if command == "init":
                init = True

            if init and command in ["tournament"]:
                return

            if command in self.handlers:
                for func in self.handlers[command]:
                    await func(self, roomid, *parts[2:])

    async def try_modchat(self, roomid: str) -> None:
        room = Room.get(roomid)
        if room and not room.modchat and room.no_mods_online:
            tz = pytz.timezone("Europe/Rome")
            timestamp = datetime.now(tz)
            minutes = timestamp.hour * 60 + timestamp.minute
            # 00:30 - 08:00
            if 30 <= minutes < 8 * 60 and room.no_mods_online + (7 * 60) < time():
                await self.send_message(roomid, "/modchat +")

    async def send_rankhtmlbox(self, rank: str, room: str, message: str) -> None:
        await self.send_message(
            room, "/addrankhtmlbox {}, {}".format(rank, message.replace("\n", "<br>"))
        )

    async def send_htmlbox(
        self, room: str, user: str, message: str, simple_message: str = ""
    ):
        message = message.replace("\n", "<br>")
        if room is not None:
            await self.send_message(room, "/addhtmlbox {}".format(message))
        elif user is not None:
            room = utils.can_pminfobox_to(self, utils.to_user_id(user))
            if room is not None:
                await self.send_message(room, "/pminfobox {}, {}".format(user, message))
            else:
                if simple_message == "":
                    simple_message = "Questo comando è disponibile in PM "
                    simple_message += "solo se sei online in una room dove sono Roombot"
                await self.send_pm(user, simple_message)

    async def send_reply(self, room: Optional[str], user: str, message: str) -> None:
        if room is None:
            await self.send_pm(user, message)
        else:
            await self.send_message(room, message)

    async def send_message(self, room: str, message: str) -> None:
        await self.send("{}|{}".format(room, message))

    async def send_pm(self, user: str, message: str):
        await self.send("|/w {}, {}".format(utils.to_user_id(user), message))

    async def send(self, message: str) -> None:
        print(">> {}".format(message))
        now = time()
        if now - self.lastmessage < 0.1:
            await asyncio.sleep(0.1)
        self.lastmessage = now
        await self.websocket.send(message)


CONNECTION = Connection(
    ("wss" if os.environ["SHOWDOWN_PORT"] == "443" else "ws")
    + "://"
    + os.environ["SHOWDOWN_HOST"]
    + ":"
    + os.environ["SHOWDOWN_PORT"]
    + "/showdown/websocket",
    os.environ["USERNAME"],
    os.environ["PASSWORD"],
    os.environ["AVATAR"],
    os.environ["STATUSTEXT"],
    os.environ["ROOMS"].split(","),
    os.environ["PRIVATE_ROOMS"].split(","),
    os.environ["COMMAND_CHARACTER"],
    os.environ["ADMINISTRATORS"].split(","),
)

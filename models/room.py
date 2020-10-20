from __future__ import annotations

from collections import deque
from datetime import datetime
from time import time
from typing import TYPE_CHECKING, Deque, Dict, Optional

import htmlmin  # type: ignore
import pytz

import utils
from typedefs import RoomId

if TYPE_CHECKING:
    from connection import Connection

    from .user import User


class Room:
    """Represents a PS room.

    Room instances are saved in conn.rooms.

    Attributes:
        conn (Connection): Used to access the websocket.
        roomid (str): Uniquely identifies a room, see utils.to_room_id.
        is_private (bool, optional): Determined from environs. Defaults to True.
        autojoin (bool, optional): Whether the bot should join the room on startup.
            Defaults to False.
        buffer (Deque[str]): Fixed list of the last room messages.
        language (str): Room language.
        language_id (int): Veekun id for language.
        modchat (bool): True if modchat level is at least "+".
        roombot (bool): True if cerbottana is roombot in this room.
        title (str): Formatted variant of roomid.
        users (Dict[User, str]): User instance, rank string.
        no_mods_online (Optional[float])
        last_modchat_command (float)

    Todo:
        `is_private` should be determined dynamically from protocol communication.
        Rooms should be removed from conn.rooms if they |deinit|.
    """

    def __init__(
        self,
        conn: Connection,
        roomid: RoomId,
        is_private: bool = True,
        autojoin: bool = False,
    ) -> None:
        # Attributes initialized directly
        self.conn = conn
        self.roomid = roomid
        self.is_private = is_private
        self.autojoin = autojoin

        # Attributes initialized through handlers
        self.dynamic_buffer: Deque[str] = deque(maxlen=20)
        self.language = "English"
        self.modchat = False
        self.roombot = False
        self.title = ""

        # Attributes updated within this instance
        self._users: Dict[User, str] = {}  # user, rank
        self.no_mods_online: Optional[float] = None
        self.last_modchat_command: float = 0

        # Register new initialized room
        if self.roomid in self.conn.rooms:
            warn = f"Warning: overriding previous data for {self.roomid}! "
            warn += "You should avoid direct initialization and use Room.get instead."
            print(warn)
        self.conn.rooms[self.roomid] = self

    @property
    def buffer(self) -> Deque[str]:
        return self.dynamic_buffer.copy()

    @property
    def language_id(self) -> int:
        table = {
            "Japanese": 1,
            "Korean": 3,
            "Traditional Chinese": 4,
            "French": 5,
            "German": 6,
            "Spanish": 7,
            "Italian": 8,
            "English": 9,
            "Simplified Chinese": 12,
            "Portuguese": 13,
        }
        if self.language in table:
            return table[self.language]
        return table["English"]  # Default to English if language is not available.

    @property
    def users(self) -> Dict[User, str]:
        return self._users

    def add_user(self, user: User, rank: Optional[str] = None) -> None:
        """Adds a user to the room or updates it if it's already stored.

        If it's the first room joined by the user, it saves its instance in conn.users.

        Args:
            user (User): User to add.
            rank (Optional[str], optional): Room rank of user. Defaults to None if rank
               is unchanged.
        """
        if not rank:
            rank = self._users[user] if user in self._users else " "
        self._users[user] = rank

        if user.has_role("driver", self):
            if not user.idle:
                self.no_mods_online = None
            else:
                self._check_no_mods_online()

        # User persistance
        if user.userid not in self.conn.users:
            self.conn.users[user.userid] = user

    def remove_user(self, user: User) -> None:
        """Removes a user from a room.

        If it was the only room the user was in, its instance is deleted.

        Args:
            user (User): User to remove.
        """
        if user in self._users:
            self._users.pop(user)
            if user.has_role("driver", self):
                self._check_no_mods_online()

    def __str__(self) -> str:
        return self.roomid

    def __contains__(self, user: User) -> bool:
        return user in self.users

    def _check_no_mods_online(self) -> None:
        if self.no_mods_online:
            return
        for user in self._users:
            if user.idle:
                continue
            if user.has_role("driver", self):
                return
            self.no_mods_online = time()

    async def try_modchat(self) -> None:
        """Sets modchat in a specific time frame if the are no mods online."""
        if not self.modchat and self.no_mods_online:
            tz = pytz.timezone("Europe/Rome")
            timestamp = datetime.now(tz)
            minutes = timestamp.hour * 60 + timestamp.minute
            # 00:30 - 08:00
            if (
                30 <= minutes < 8 * 60
                and self.no_mods_online + (7 * 60) < time()
                and self.last_modchat_command + 15 < time()
            ):
                self.last_modchat_command = time()
                await self.send("/modchat +", False)

    async def send(self, message: str, escape: bool = True) -> None:
        """Sends a message to the room.

        Args:
            message (str): Text to be sent.
            escape (bool, optional): True if PS commands should be escaped. Defaults to
                True.
        """
        if escape:
            if message[0] == "/":
                message = "/" + message
            elif message[0] == "!":
                message = " " + message
        await self.conn.send(f"{self.roomid}|{message}")

    async def send_rankhtmlbox(self, rank: str, message: str) -> None:
        """Sends an HTML box visible only to people with a specific rank.

        Args:
            rank (str): Minimum rank required to see the HTML box.
            message (str): HTML to be sent.
        """
        message = htmlmin.minify(message)
        await self.send(f"/addrankhtmlbox {rank}, {message}", False)

    async def send_htmlbox(self, message: str) -> None:
        """Sends an HTML box visible to every user in the room.

        Args:
            message (str): HTML to be sent.
        """
        message = htmlmin.minify(message)
        await self.send(f"/addhtmlbox {message}", False)

    @classmethod
    def get(cls, conn: Connection, room: str) -> Room:
        """Safely retrieves a Room instance, if it exists, or creates a new one.

        New rooms are private by default.

        Args:
            conn (Connection): Used to access the websocket.
            room (str): The room to retrieve.

        Returns:
            Room: Existing instance associated with roomid or newly created one.
        """
        roomid = utils.to_room_id(room)
        if roomid not in conn.rooms:
            conn.rooms[roomid] = cls(conn, roomid)
        return conn.rooms[roomid]

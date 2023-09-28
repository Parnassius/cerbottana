# Author: Plato (palt0)

from __future__ import annotations

import asyncio
from collections import deque
from textwrap import shorten
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary, WeakValueDictionary

from domify import html_elements as e
from domify.base_element import BaseElement

from cerbottana import utils
from cerbottana.typedefs import RoomId

if TYPE_CHECKING:
    from cerbottana.connection import Connection
    from cerbottana.models.protocol_message import ProtocolMessage
    from cerbottana.models.user import User


class Room:
    """Represents a PS room.

    Room instances are saved in conn.rooms.

    Attributes:
        conn (Connection): Used to access the websocket.
        roomid (RoomId): Uniquely identifies a room, see utils.to_room_id.
        is_private (bool): True if room is unlisted/private.
        buffer (deque[str]): Fixed list of the last room messages.
        language (str): Room language.
        language_id (int): Veekun id for language.
        roombot (bool): True if the bot is roombot in this room.
        title (str): Formatted variant of roomid.
        users (dict[User, str]): User instance, rank string.
        webhook (str | None): Discord webhook URL. None if missing.
    """

    _instances: WeakKeyDictionary[
        Connection, WeakValueDictionary[RoomId, Room]
    ] = WeakKeyDictionary()

    def __init__(
        self,
        conn: Connection,
        roomid: RoomId,
    ) -> None:
        # Attributes initialized directly
        self.conn = conn
        self.roomid = roomid

        # Attributes initialized through handlers
        self.dynamic_buffer: deque[str] = deque(maxlen=20)
        self.language = "English"
        self.roombot = False
        self.title = ""

        # Attributes updated within this instance
        self._users: dict[User, str] = {}  # user, rank
        self._message_queue: asyncio.Queue[ProtocolMessage]

    @property
    def buffer(self) -> deque[str]:
        return self.dynamic_buffer.copy()

    @property
    def is_private(self) -> bool:
        return self.roomid not in self.conn.public_roomids

    @property
    def language_id(self) -> int:
        return utils.get_language_id(self.language)

    @property
    def users(self) -> dict[User, str]:
        return self._users

    @property
    def webhook(self) -> str | None:
        return self.conn.webhooks.get(self.roomid)

    def add_user(self, user: User, rank: str | None = None) -> None:
        """Adds a user to the room or updates it if it's already stored.

        Args:
            user (User): User to add.
            rank (str | None): Room rank of user. Defaults to None if rank is unchanged.
        """
        if not rank:
            rank = self._users[user] if user in self._users else " "
        self._users[user] = rank

    def remove_user(self, user: User) -> None:
        """Removes a user from a room.

        If it was the only room the user was in, its instance is deleted.

        Args:
            user (User): User to remove.
        """
        if user in self._users:
            self._users.pop(user)

    def __str__(self) -> str:
        return self.roomid

    def __contains__(self, user: User) -> bool:
        return user in self.users

    def add_message_to_queue(self, msg: ProtocolMessage) -> None:
        if not hasattr(self, "_message_queue"):
            self._message_queue = asyncio.Queue()
            self.conn.create_task(self._process_message_queue())
        self._message_queue.put_nowait(msg)

    async def process_all_messages(self) -> None:
        if hasattr(self, "_message_queue"):
            await self._message_queue.join()

    async def _process_message_queue(self) -> None:
        try:
            while msg := self._message_queue.get_nowait():
                if msg.type in self.conn.handlers:
                    async with asyncio.TaskGroup() as tg:
                        for handler in self.conn.handlers[msg.type]:
                            tg.create_task(handler.callback(msg))
                self._message_queue.task_done()
        except asyncio.QueueEmpty:
            del self._message_queue
        except asyncio.CancelledError:
            del self._message_queue
            raise

    async def send(self, message: str, escape: bool = True) -> None:
        """Sends a message to the room.

        Args:
            message (str): Text to be sent.
            escape (bool): True if PS commands should be escaped. Defaults to True.
        """
        if escape:
            if message[0] == "/":
                message = "/" + message
            elif message[0] == "!":
                message = " " + message
        await self.conn.send(f"{self.roomid}|{message}")

    async def send_rankhtmlbox(self, rank: str, message: BaseElement) -> None:
        """Sends an HTML box visible only to people with a specific rank.

        Args:
            rank (str): Minimum rank required to see the HTML box.
            message (BaseElement): HTML to be sent.
        """
        await self.send(f"/addrankhtmlbox {rank}, {message}", False)

    async def send_htmlbox(self, message: BaseElement) -> None:
        """Sends an HTML box visible to every user in the room.

        Args:
            message (BaseElement): HTML to be sent.
        """
        await self.send(f"/addhtmlbox {message}", False)

    async def send_htmlpage(self, pageid: str, page_room: Room) -> None:
        """Sends link to an HTML page in a room.

        Args:
            pageid (str): id of the htmlpage.
            page_room (Room): Room to be passed to the function.
        """
        await self.send_htmlbox(
            e.Button(
                pageid,
                name="send",
                value=(
                    f"/pm {self.conn.username}, "
                    f"{self.conn.command_character}{pageid} {page_room.roomid}"
                ),
            )
        )

    async def send_modnote(self, action: str, user: User, note: str = "") -> None:
        """Adds a modnote to a room.

        Args:
            action (str): id of the action performed.
            user (User): User who performed the action.
            note (str): additional notes. Defaults to "".
        """
        if not self.roombot:
            return

        arg = f"[{action}] {user.userid}"
        if note:
            arg += f": {note}"
        await self.send(f"/modnote {shorten(arg, 300)}", False)

    @classmethod
    def get(cls, conn: Connection, room: str) -> Room:
        """Safely retrieves a Room instance, if it exists, or creates a new one.

        Args:
            conn (Connection): Used to access the websocket.
            room (str): The room to retrieve.

        Returns:
            Room: Existing instance associated with roomid or newly created one.
        """

        if conn not in cls._instances:
            cls._instances[conn] = WeakValueDictionary()

        roomid = utils.to_room_id(room)
        try:
            instance = cls._instances[conn][roomid]
        except KeyError:
            instance = cls._instances[conn][roomid] = cls(conn, roomid)
        return instance

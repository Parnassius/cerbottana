from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Set

import htmlmin  # type: ignore

import utils

if TYPE_CHECKING:
    from connection import Connection

    from .room import Room


class User:
    """Represents a PS User.

    User instances are saved in conn.users if they they're contained in at least one
    room; changing `userid` removes its associated instance.

    Attributes:
        conn (Connection): Used to access the websocket.
        userstring (str): Unparsed user string without leading character rank.
        username (str): Parsed user string without leading character and status text.
        userid (str): Uniquely identifies a user, see utils.to_user_id.
        self.global_rank (str): PS global rank, defaults to None if rank is unknown.
        idle (bool): True if user is marked as idle.
        is_administrator (bool): True if user is a bot administrator.
        rooms (List[room]): List of rooms the user is in.
    """

    def __init__(
        self,
        conn: Connection,
        userstring: str,
    ):
        """Might override a previous instance associated with the same userid. Use
        User.get.
        """
        self.conn = conn
        self.userstring = userstring
        self.global_rank: str = " "

    @property
    def username(self) -> str:
        return self.userstring.split("@")[0]

    @property
    def userid(self) -> str:
        return utils.to_user_id(self.userstring)

    @property
    def idle(self) -> bool:
        return self.userstring[-2:] == "@!"

    @property
    def is_administrator(self) -> bool:
        return self.userid in self.conn.administrators

    @property
    def rooms(self) -> Set[Room]:
        return {room for room in self.conn.rooms.values() if self in room}

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            raise NotImplementedError
        return self.userid == other.userid

    def __hash__(self) -> int:
        return hash(self.userid)

    def __str__(self) -> str:
        return self.username

    def rank(self, room: Room) -> Optional[str]:
        """Retrieves user's rank.

        Args:
            room (Room): Room to check.

        Returns:
            Optional[str]: Returns rank string, None if user is not in room.
        """
        return room.users[self] if self in room else None

    def has_role(self, role: str, room: Room) -> bool:
        """Check if user has a PS room role or higher.

        Higher global roles ovveride room roles.

        Args:
            role (str): PS role (i.e. "voice", "driver").
            room (Room): Room to check.

        Returns:
            bool: True if user meets the required criteria.
        """
        if self.global_rank and utils.has_role(role, self.global_rank):
            return True

        room_rank = self.rank(room)
        if room_rank:
            return utils.has_role(role, room_rank)

        return False

    def roomname(self, room: Room) -> Optional[str]:
        """Parses the username as it's seen in a room list (i.e.: "@Plat0").

        Args:
            room (Room): Room to check.

        Returns:
            str: User string, None if user is not in room.
        """
        # TODO: Cover local / global rank interaction
        rank_ = self.rank(room)
        if rank_ is None:
            return None
        if rank_ == " ":
            return self.username
        return rank_ + self.username

    def can_pminfobox_to(self) -> Optional[Room]:
        """Finds a room that can be used to cast private infoboxes to user.

        Returns:
            Optional[Room]: Valid room, None if no room satisfies the conditions.
        """
        return next((room for room in self.rooms if room.roombot), None)

    async def send(self, message: str, escape: bool = True) -> None:
        """Sends a PM to user.

        Args:
            message (str): Text to be sent.
            escape (bool, optional): True if PS commands should be escaped. Defaults to
                True.
        """
        if escape and message[0] == "/":
            message = "/" + message
        await self.conn.send(f"|/w {self.userid}, {message}")

    async def send_htmlbox(self, message: str, simple_message: str = "") -> None:
        """Sends an HTML box in PM to user.

        Args:
            message (str): HTML to be sent.
            simple_message (str, optional): Alt text. Defaults to a generic message.
        """
        message = htmlmin.minify(message)
        room = self.can_pminfobox_to()
        if room is None:
            if simple_message == "":
                simple_message = "Questo comando è disponibile in PM "
                simple_message += "solo se sei online in una room dove sono Roombot"
            await self.send(simple_message)
        else:
            await room.send(f"/pminfobox {self.userid}, {message}", False)

    @classmethod
    def get(cls, conn: Connection, userstring: str) -> User:
        """Safely retrieves a User instance, if it exists, or creates a new one.

        Args:
            conn (Connection): Used to access the websocket.
            userstring (str): User string of the room to retrieve.

        Returns:
            User: Existing instance associated with userstring or newly created one.
        """
        userid = utils.to_user_id(userstring)
        if userid in conn.users:
            return conn.users[userid]
        return cls(conn, userstring)

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional, Set

import utils
from database import Database
from plugins import htmlpages
from typedefs import Role, UserId

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
    def userid(self) -> UserId:
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

    def has_role(self, role: Role, room: Room, ignore_grole: bool = False) -> bool:
        """Check if user has a PS room role or higher.

        Higher global roles ovveride room roles.

        Args:
            role (Role): PS role (i.e. "voice", "driver").
            room (Room): Room to check.
            ignore_grole (bool): True if global roles should be ignored.

        Returns:
            bool: True if user meets the required criteria.
        """
        if (
            not ignore_grole
            and self.global_rank
            and utils.has_role(role, self.global_rank)
        ):
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
            escape (bool): True if PS commands should be escaped. Defaults to
                True.
        """
        if escape and message[0] == "/":
            message = "/" + message
        await self.conn.send(f"|/w {self.userid}, {message}")

    async def send_htmlbox(self, message: str, simple_message: str = "") -> None:
        """Sends an HTML box in PM to user.

        Args:
            message (str): HTML to be sent.
            simple_message (str): Alt text. Defaults to a generic message.
        """
        room = self.can_pminfobox_to()
        if room is None:
            if simple_message == "":
                simple_message = "Questo comando è disponibile in PM "
                simple_message += "solo se sei online in una room dove sono Roombot"
            await self.send(simple_message)
        else:
            await room.send(f"/pminfobox {self.userid}, {message}", False)

    async def send_htmlpage(self, pageid: str, page_room: Room, page: int = 1) -> None:
        """Sends an HTML page to user.

        Args:
            pageid (str): id of the htmlpage.
            page_room (Room): Room to be passed to the function.
            page (int): Page number. Defaults to 1.
        """
        if pageid not in htmlpages:
            return
        room = self.can_pminfobox_to()
        if room is None:
            simple_message = "Questo comando è disponibile in PM "
            simple_message += "solo se sei online in una room dove sono Roombot"
            await self.send(simple_message)
        else:
            query = htmlpages[pageid](self, page_room)
            if query is None:
                return

            db = Database.open()

            with db.get_session() as session:
                query = query.with_session(session)

                last_page = math.ceil(query.count() / 100)
                page = min(page, last_page)
                rs = query.limit(100).offset(100 * (page - 1)).all()

                message = utils.render_template(
                    f"htmlpages/{pageid}.html",
                    rs=rs,
                    current_page=page,
                    last_page=last_page,
                    can_delete=self.has_role("driver", page_room),
                    room=page_room,
                    botname=self.conn.username,
                    cmd_char=self.conn.command_character,
                )

                message = f'<div class="pad">{message}</div>'
                if page_room:
                    pageid += "0" + page_room.roomid

                # Ugly hack to scroll to top when changing page
                # https://github.com/smogon/pokemon-showdown-client/pull/1645
                await room.send(f"/sendhtmlpage {self.userid}, {pageid}, <br>", False)

                await room.send(
                    f"/sendhtmlpage {self.userid}, {pageid}, {message}", False
                )

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

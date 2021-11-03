# Author: Plato (palt0)

from __future__ import annotations

import math
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary, WeakValueDictionary

from sqlalchemy import func, select

import cerbottana.databases.database as d
from cerbottana import utils
from cerbottana.database import Database
from cerbottana.plugins import htmlpages
from cerbottana.typedefs import Role, UserId

if TYPE_CHECKING:
    from cerbottana.connection import Connection

    from .room import Room


class User:
    """Represents a PS User.

    User instances are saved in _instances if they they're contained in at least one
    room; changing `userid` removes its associated instance.

    Attributes:
        conn (Connection): Used to access the websocket.
        userstring (str): Unparsed user string without leading character rank.
        username (str): Parsed user string without leading character and status text.
        userid (UserId): Uniquely identifies a user, see utils.to_user_id.
        global_rank (str): PS global rank, defaults to " " if rank is unknown.
        idle (bool): True if user is marked as idle.
        is_administrator (bool): True if user is a bot administrator.
        rooms (set[Room]): List of rooms the user is in.
    """

    _instances: WeakKeyDictionary[
        Connection, WeakValueDictionary[UserId, User]
    ] = WeakKeyDictionary()

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
    def rooms(self) -> set[Room]:
        return {room for room in self.conn.rooms.values() if self in room}

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            raise NotImplementedError
        return self.userid == other.userid

    def __hash__(self) -> int:
        return hash(self.userid)

    def __str__(self) -> str:
        return self.username

    async def load_details(self) -> None:
        await self.conn.send(f"|/cmd userdetails {self.userid}")

    def rank(self, room: Room, consider_global: bool = False) -> str | None:
        """Retrieves user's rank.

        Args:
            room (Room): Room to check.
            consider_global (bool): Whether the global rank should be returned if it is
                higher than the room rank.

        Returns:
            str | None: Returns rank string, None if consider_global is False and user
                is not in room.
        """
        rank_orders = {
            "~": 101,
            "#": 102,
            "&": 103,
            "★": 104,
            "@": 105,
            "%": 106,
            "§": 107,
            # unrecognized symbols
            "*": 109,
            "☆": 110,
            "+": 200,
            " ": 201,
            "!": 301,
            "✖": 302,
            "‽": 303,
            None: 401,
        }
        default_rank = 108

        rank_: str | None = self.global_rank if consider_global else None
        if self in room:
            rank_ = min(
                rank_, room.users[self], key=lambda x: rank_orders.get(x, default_rank)
            )

        return rank_

    def has_role(self, role: Role, room: Room, ignore_grole: bool = False) -> bool:
        """Check if user has a PS room role or higher.

        Higher global roles ovveride room roles.

        Args:
            role (Role): PS role (i.e. "voice", "driver").
            room (Room): Room to check.
            ignore_grole (bool): True if global roles should be ignored. Default to
                False.

        Returns:
            bool: True if user meets the required criteria.
        """
        if room_rank := self.rank(room, not ignore_grole):
            return utils.has_role(role, room_rank)

        return False

    def roomname(self, room: Room) -> str | None:
        """Parses the username as it's seen in a room list (i.e.: "@Plat0").

        Args:
            room (Room): Room to check.

        Returns:
            str | None: User string, None if user is not in room.
        """
        rank_ = self.rank(room, True)
        if rank_ is None:
            return None
        if rank_ == " ":
            return self.username
        return rank_ + self.username

    def can_pminfobox_to(self) -> Room | None:
        """Finds a room that can be used to cast private infoboxes to user.

        Returns:
            Room | None: Valid room, None if no room satisfies the conditions.
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

    async def send_htmlpage(
        self, pageid: str, page_room: Room, page: int = 1, *, scroll_to_top: bool = True
    ) -> None:
        """Sends an HTML page to user.

        Args:
            pageid (str): id of the htmlpage.
            page_room (Room): Room to be passed to the function.
            page (int): Page number. Defaults to 1.
            scroll_to_top (bool): Whether the page should scroll to the top. Defaults to
                True.
        """
        if pageid not in htmlpages:
            return
        room = self.can_pminfobox_to()
        if room is None:
            simple_message = "Questo comando è disponibile in PM "
            simple_message += "solo se sei online in una room dove sono Roombot"
            await self.send(simple_message)
        else:
            stmt_func, delete_command = htmlpages[pageid]

            delete_req_rank: Role = "driver"
            if delete_command in self.conn.commands:
                cmd = self.conn.commands[delete_command]
                delete_req_rank = cmd.required_rank

                if cmd.required_rank_editable is not False:
                    command = f".{cmd.name}"
                    if isinstance(cmd.required_rank_editable, str):
                        command = cmd.required_rank_editable

                    db = Database.open()
                    with db.get_session() as session:
                        stmt_custom_rank = select(
                            d.CustomPermissions.required_rank
                        ).filter_by(roomid=page_room.roomid, command=command)
                        custom_rank: Role | None = session.scalar(stmt_custom_rank)
                        if custom_rank:
                            delete_req_rank = custom_rank

            stmt = stmt_func(self, page_room)
            if stmt is None:
                return

            db = Database.open()

            with db.get_session() as session:
                stmt_last_page = stmt.with_only_columns(func.count())
                last_page = math.ceil(session.scalar(stmt_last_page) / 100)
                page = min(page, last_page)
                stmt_rs = stmt.limit(100).offset(100 * (page - 1))

                query = session.execute(stmt_rs)
                if len(query.keys()) == 1:
                    rs = query.scalars().all()
                else:
                    rs = query.all()

                message = utils.render_template(
                    f"htmlpages/{pageid}.html",
                    rs=rs,
                    current_page=page,
                    last_page=last_page,
                    can_delete=self.has_role(delete_req_rank, page_room),
                    room=page_room,
                    botname=self.conn.username,
                    cmd_char=self.conn.command_character,
                )

                message = f'<div class="pad">{message}</div>'
                if page_room:
                    pageid += "0" + page_room.roomid

                if scroll_to_top:
                    # Ugly hack to scroll to top when changing page
                    # https://github.com/smogon/pokemon-showdown-client/pull/1645
                    await room.send(
                        f"/sendhtmlpage {self.userid}, {pageid}, <br>", False
                    )

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

        if conn not in cls._instances:
            cls._instances[conn] = WeakValueDictionary()

        userid = utils.to_user_id(userstring)
        try:
            instance = cls._instances[conn][userid]
        except KeyError:
            instance = cls._instances[conn][userid] = cls(conn, userstring)
        return instance

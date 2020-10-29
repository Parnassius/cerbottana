from __future__ import annotations

from typing import TYPE_CHECKING

from handlers import handler_wrapper
from models.room import Room
from models.user import User

if TYPE_CHECKING:
    from connection import Connection


@handler_wrapper(["pm"])
async def requestpage(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 6:
        return

    if args[2] != "" or args[3] != "requestpage":
        return

    user = User.get(conn, args[4])
    pageid = args[5].split("0")  # pageids can only contain letters and numbers

    if len(pageid) != 2:
        return

    page_room = Room.get(conn, pageid[1])
    await user.send_htmlpage(pageid[0], page_room)

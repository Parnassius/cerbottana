from __future__ import annotations

from typing import TYPE_CHECKING

from handlers import handler_wrapper
from models.room import Room
from models.user import User

if TYPE_CHECKING:
    from connection import Connection
    from models.protocol_message import ProtocolMessage


@handler_wrapper(["pm"], required_parameters=6)
async def requestpage(msg: ProtocolMessage) -> None:
    if msg.params[2] != "" or msg.params[3] != "requestpage":
        return

    user = User.get(msg.conn, msg.params[4])
    pageid = msg.params[5].split("0")  # pageids can only contain letters and numbers

    if len(pageid) != 2:
        return

    page_room = Room.get(msg.conn, pageid[1])
    await user.send_htmlpage(pageid[0], page_room)

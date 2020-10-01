from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

import utils
from handlers import handler_wrapper
from models.room import Room

if TYPE_CHECKING:
    from connection import Connection


@handler_wrapper(["init"])
async def get_roominfo(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 1:
        return

    if args[0] == "chat":
        await conn.send(f"|/cmd roominfo {room.roomid}")


@handler_wrapper(["queryresponse"])
async def queryresponse(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 2:
        return

    querytype = args[0]
    querydata = args[1]

    if querytype != "roominfo":
        return

    data = json.loads(querydata)
    if data["type"] == "chat":
        room = Room.get(conn, data["roomid"])
        room.modchat = utils.has_role("voice", data.get("modchat", None))


@handler_wrapper(["chat", "c"])
async def modchat(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 2:
        return

    message = "|".join(args[1:]).strip()

    if room.roomid in conn.rooms:
        match = re.match(r"^\/log \(.+ set modchat to (.*)\)$", message)

        if match:
            room.modchat = len(match.group(1)) == 1 and utils.has_role(
                "voice", match.group(1)
            )

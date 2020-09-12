from __future__ import annotations

import re
from typing import TYPE_CHECKING

import utils
from handlers import handler_wrapper

if TYPE_CHECKING:
    from connection import Connection
    from models.room import Room


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

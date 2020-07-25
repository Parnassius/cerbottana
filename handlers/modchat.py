from __future__ import annotations

import re
from typing import TYPE_CHECKING

import utils
from handlers import handler_wrapper
from room import Room

if TYPE_CHECKING:
    from connection import Connection


@handler_wrapper(["chat", "c"])
async def modchat(conn: Connection, roomid: str, *args: str) -> None:
    if len(args) < 2:
        return

    message = "|".join(args[1:]).strip()

    if roomid in conn.rooms:
        match = re.match(r"^\/log \(.+ set modchat to (.*)\)$", message)

        if match:
            Room.get(roomid).modchat = len(match.group(1)) == 1 and utils.is_voice(
                match.group(1)
            )

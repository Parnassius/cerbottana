from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

from plugins import plugin_wrapper
from room import Room

if TYPE_CHECKING:
    from connection import Connection


@plugin_wrapper(helpstr="Seleziona un utente a caso presente nella room.")
async def randomuser(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    if room is None:
        return
    users = Room.get(room).users
    await conn.send_reply(
        room, user, users[random.choice(list(users.keys()))]["username"]
    )

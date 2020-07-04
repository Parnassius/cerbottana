from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from connection import Connection

import random

from plugin_loader import plugin_wrapper

from room import Room


@plugin_wrapper(helpstr="Seleziona un utente a caso presente nella room.")
async def randomuser(conn: Connection, room: str, user: str, arg: str) -> None:
    users = Room.get(room).users
    await conn.send_reply(
        room, user, users[random.choice(list(users.keys()))]["username"]
    )

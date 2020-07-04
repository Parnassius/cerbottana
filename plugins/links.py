from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from connection import Connection

from plugin_loader import plugin_wrapper


@plugin_wrapper(
    helpstr="Elenca gli avatar disponibili. Per usarne uno, <code>/avatar [nome]</code>"
)
async def avatars(conn: Connection, room: str, user: str, arg: str) -> None:
    await conn.send_reply(
        room, user, "https://play.pokemonshowdown.com/sprites/trainers/"
    )

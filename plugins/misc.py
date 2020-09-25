from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

import utils
from plugins import command_wrapper, parametrize_room
from room import Room

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper(helpstr="Saluta un utente a caso presente nella room.")
async def randomcaio(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    if room is None:
        return
    users = Room.get(room).users
    await conn.send_reply(
        room, user, "caio " + users[random.choice(list(users.keys()))]["username"]
    )


@command_wrapper(helpstr="Seleziona un utente a caso presente nella room.")
async def randomuser(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    if room is None:
        return
    users = Room.get(room).users
    await conn.send_reply(
        room, user, users[random.choice(list(users.keys()))]["username"]
    )


@command_wrapper()
@parametrize_room
async def tell(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    args = arg.split(",")
    if len(args) < 2 or (len(args) == 2 and not args[1]):
        await conn.send_reply(room, user, "Cosa devo inviare?")
        return

    target_room = args[0]
    userid = utils.to_user_id(user)
    rank = Room.get(target_room).users[userid]["rank"]
    if not utils.is_driver(rank):
        await conn.send_reply(room, user, "Devi essere almeno driver")
        return

    text = ",".join(args[1:]).lstrip()
    html = (
        f"<b>{utils.to_obfuscated_html(text)}</b><br>"
        + '<div style="float: left; color: #888; font-size: 8pt">'
        + f"[inviato da {rank}{userid}]"
        + "</div>"
    )
    await conn.send_htmlbox(target_room, user, html)

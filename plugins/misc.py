from __future__ import annotations

import random
from typing import TYPE_CHECKING

import utils
from plugins import command_wrapper, parametrize_room

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(helpstr="Saluta un utente a caso presente nella room.")
async def randomcaio(msg: Message) -> None:
    if msg.room is None:
        return
    randuser = random.choice(list(msg.room.users.keys()))
    await msg.reply(f"caio {randuser}")


@command_wrapper(helpstr="Seleziona un utente a caso presente nella room.")
async def randomuser(msg: Message) -> None:
    if msg.room is None:
        return
    randuser = random.choice(list(msg.room.users.keys()))
    await msg.reply(f"{randuser}")


@command_wrapper()
@parametrize_room
async def tell(msg: Message) -> None:
    if not msg.arg:
        await msg.reply("Cosa devo inviare?")
        return

    if not msg.user.has_role("driver", msg.parametrized_room):
        await msg.reply("Devi essere almeno driver")
        return

    author = msg.user.roomname(msg.parametrized_room)
    html = (
        f"<b>{utils.to_obfuscated_html(msg.arg)}</b><br>"
        + '<div style="float: left; color: #888; font-size: 8pt">'
        + f"[inviato da {author}]"
        + "</div>"
    )
    await msg.parametrized_room.send_htmlbox(html)

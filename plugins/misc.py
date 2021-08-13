from __future__ import annotations

import random
from typing import TYPE_CHECKING

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(
    aliases=("randomcaio",),
    helpstr="Saluta un utente a caso presente nella room.",
    parametrize_room=True,
)
async def randcaio(msg: Message) -> None:
    user = random.choice(list(msg.parametrized_room.users.keys()))
    await msg.reply(f"caio {user}")


@command_wrapper(
    aliases=("randomuser",),
    helpstr="Seleziona un utente a caso presente nella room.",
    parametrize_room=True,
)
async def randuser(msg: Message) -> None:
    user = random.choice(list(msg.parametrized_room.users.keys()))
    await msg.reply(f"{user}")


@command_wrapper(required_rank="driver", parametrize_room=True)
async def tell(msg: Message) -> None:
    if not msg.arg:
        await msg.reply("Cosa devo inviare?")
        return

    author = msg.user.roomname(msg.parametrized_room)
    html = (
        f"<b>{utils.to_obfuscated_html(msg.arg)}</b><br>"
        + '<div style="display: inline-block; color: #888; font-size: 8pt">'
        + f"[inviato da {author}]"
        + "</div>"
    )
    await msg.parametrized_room.send_htmlbox(html)


@command_wrapper(helpstr="<i>[blitz]</i> Avvia una partita di UNO.", allow_pm=False)
async def uno(msg: Message) -> None:
    blitz_keywords = ("blitz", "fast", "veloce")
    timer = 5 if msg.arg.lower() in blitz_keywords else 30

    ps_commands = (
        "/uno create 100",
        "/uno autostart 45",
        f"/uno timer {timer}",
    )

    for ps_command in ps_commands:
        await msg.reply(ps_command, False)

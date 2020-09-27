from __future__ import annotations

from typing import TYPE_CHECKING

from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(
    helpstr="Elenca gli avatar disponibili. Per usarne uno, <code>/avatar [nome]</code>"
)
async def avatars(msg: Message) -> None:
    await msg.reply("https://play.pokemonshowdown.com/sprites/trainers/")


@command_wrapper(aliases=("github",))
async def git(msg: Message) -> None:
    await msg.reply("https://github.com/Parnassius/cerbottana")

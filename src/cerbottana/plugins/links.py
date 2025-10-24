from __future__ import annotations

from cerbottana.models.message import Message
from cerbottana.plugins import command_wrapper


@command_wrapper(
    helpstr="Elenca gli avatar disponibili. Per usarne uno, <code>/avatar [nome]</code>"
)
async def avatars(msg: Message) -> None:
    await msg.reply("https://play.pokemonshowdown.com/sprites/trainers/")


@command_wrapper(aliases=("tournamentrules", "tourrules"))
async def customrules(msg: Message) -> None:
    await msg.reply(
        "https://github.com/smogon/pokemon-showdown/blob/master/config/CUSTOM-RULES.md#custom-rules"
    )


@command_wrapper(aliases=("github",))
async def git(msg: Message) -> None:
    await msg.reply("https://github.com/Parnassius/cerbottana")

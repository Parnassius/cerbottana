from __future__ import annotations

import json
from typing import TYPE_CHECKING

from plugins import command_wrapper
from typedefs import JsonDict
from utils import get_ps_dex_entry, to_id

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(aliases=("icons", "userlisticon", "userlisticons"))
async def icon(msg: Message) -> None:
    if len(msg.args) < 1:
        await msg.reply(
            "You can set your Pokémon using "
            f"``{msg.conn.command_character}icon <pokemon>``, "
            "or install the userstyle (https://git.io/JuoFg) "
            "using Stylus (https://add0n.com/stylus.html)."
        )
        return

    search_query = to_id(msg.args[0])
    dex_entry = get_ps_dex_entry(search_query)
    if dex_entry is None or dex_entry["num"] < 0:
        await msg.reply("Pokémon not found.")
        return

    icons: JsonDict
    try:
        with open("./icons.json", encoding="utf-8") as f:
            icons = json.load(f)
    except FileNotFoundError:
        icons = {}
    icons[msg.user.userid] = to_id(dex_entry["dex_name"])
    with open("./icons.json", "w", encoding="utf-8") as f:
        json.dump(icons, f)

    await msg.reply("Done. Your Pokémon might take up to 24 hours to be updated.")

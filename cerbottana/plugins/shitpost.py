from __future__ import annotations

import json
import random
from typing import TYPE_CHECKING

from domify import html_elements as e

from cerbottana import utils
from cerbottana.plugins import command_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message


@command_wrapper(aliases=("say",), is_unlisted=True, allow_pm=False)
async def shitpost(msg: Message) -> None:
    if msg.room is None:
        return

    phrase = utils.remove_diacritics(msg.arg.strip())
    if len(phrase) > 50:
        await msg.reply("Testo troppo lungo")
        return

    text0 = ""
    text1 = ""
    text2 = ""

    if phrase == "":
        if not msg.room.is_private:
            return
        phrase = "SHITPOST"

    if not msg.room.is_private and ("x" in phrase or "X" in phrase):
        phrase = "lolno"

    for i in phrase:
        if i in LETTERS:
            if text0 != "":
                text0 += " "
                text1 += " "
                text2 += " "
            text0 += LETTERS[i][0]
            text1 += LETTERS[i][1]
            text2 += LETTERS[i][2]

    html = e.Pre(style="margin: 0; overflow-x: auto")
    html.add(text0 + e.Br() + text1 + e.Br() + text2)
    await msg.reply_htmlbox(html)


@command_wrapper(aliases=("meme", "memes", "mims"), is_unlisted=True, allow_pm=False)
async def memes(msg: Message) -> None:
    if msg.room is None or not msg.room.is_private:
        return

    await msg.reply(random.choice(MEMES))


with utils.get_data_file("letters.json").open(encoding="utf-8") as f:
    LETTERS: dict[str, list[str]] = json.load(f)
with utils.get_data_file("memes.json").open(encoding="utf-8") as f:
    MEMES: list[str] = json.load(f)

from __future__ import annotations

import json
import random
from typing import TYPE_CHECKING, Dict, List

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(aliases=("say",), is_unlisted=True, allow_pm=False)
async def shitpost(msg: Message) -> None:
    if msg.room is None:
        return

    phrase = utils.remove_accents(msg.arg.strip())
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

    html = '<pre style="margin: 0; overflow-x: auto">{}<br>{}<br>{}</pre>'

    await msg.reply_htmlbox(html.format(text0, text1, text2))


@command_wrapper(aliases=("meme", "memes", "mims"), is_unlisted=True, allow_pm=False)
async def memes(msg: Message) -> None:
    if msg.room is None or not msg.room.is_private:
        return

    await msg.reply(random.choice(MEMES))


with open("./data/letters.json") as f:
    LETTERS: Dict[str, List[str]] = json.load(f)
with open("./data/memes.json") as f:
    MEMES = json.load(f)

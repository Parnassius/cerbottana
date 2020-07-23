from __future__ import annotations

import json
import random
from typing import TYPE_CHECKING, Dict, List, Optional

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper(
    aliases=["meme", "memes", "mims", "say"],
    helpstr="FOR THE MIMMMSSS",
    is_unlisted=True,
)
async def shitpost(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if room is None:
        return
    message = utils.remove_accents(arg.strip())
    if len(message) > 50:
        await conn.send_reply(room, user, "Testo troppo lungo")
        return

    text0 = ""
    text1 = ""
    text2 = ""

    if message == "":
        if not utils.is_private(conn, room):
            return
        message = "SHITPOST"

    if not utils.is_private(conn, room) and ("x" in message or "X" in message):
        message = "lolno"

    for i in message:
        if i in LETTERS:
            if text0 != "":
                text0 += " "
                text1 += " "
                text2 += " "
            text0 += LETTERS[i][0]
            text1 += LETTERS[i][1]
            text2 += LETTERS[i][2]

    html = '<pre style="margin: 0; overflow-x: auto">{}<br>{}<br>{}</pre>'

    await conn.send_htmlbox(room, user, html.format(text0, text1, text2))


async def memes(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if room is None or not utils.is_private(conn, room):
        return

    await conn.send_message(room, random.choice(MEMES))


# fmt: off
LETTERS: Dict[str, List[str]] = {
    "a": [
        "┌─┐",
        "├─┤",
        "┴ ┴",
    ],
    "b": [
        "┌┐ ",
        "├┴┐",
        "└─┘",
    ],
    "c": [
        "┌─┐",
        "│  ",
        "└─┘",
    ],
    "d": [
        "┌┬┐",
        " ││",
        "─┴┘",
    ],
    "e": [
        "┌─┐",
        "├┤ ",
        "└─┘",
    ],
    "f": [
        "┌─┐",
        "├┤ ",
        "└  ",
    ],
    "g": [
        "┌─┐",
        "│ ┬",
        "└─┘",
    ],
    "h": [
        "┬ ┬",
        "├─┤",
        "┴ ┴",
    ],
    "i": [
        "┬",
        "│",
        "┴",
    ],
    "j": [
        " ┬",
        " │",
        "└┘",
    ],
    "k": [
        "┬┌─",
        "├┴┐",
        "┴ ┴",
    ],
    "l": [
        "┬  ",
        "│  ",
        "┴─┘",
    ],
    "m": [
        "┌┬┐",
        "│││",
        "┴ ┴",
    ],
    "n": [
        "┌┐┌",
        "│││",
        "┘└┘",
    ],
    "o": [
        "┌─┐",
        "│ │",
        "└─┘",
    ],
    "p": [
        "┌─┐",
        "├─┘",
        "┴  ",
    ],
    "q": [
        "┌─┐ ",
        "│─┼┐",
        "└─┘└",
    ],
    "r": [
        "┬─┐",
        "├┬┘",
        "┴└─",
    ],
    "s": [
        "┌─┐",
        "└─┐",
        "└─┘",
    ],
    "t": [
        "┌┬┐",
        " │ ",
        " ┴ ",
    ],
    "u": [
        "┬ ┬",
        "│ │",
        "└─┘",
    ],
    "v": [
        "┬  ┬",
        "└┐┌┘",
        " └┘ ",
    ],
    "w": [
        "┬ ┬",
        "│││",
        "└┴┘",
    ],
    "x": [
        "─┐ ┬",
        "┌┴┬┘",
        "┴ └─",
    ],
    "y": [
        "┬ ┬",
        "└┬┘",
        " ┴ ",
    ],
    "z": [
        "┌─┐",
        "┌─┘",
        "└─┘",
    ],
    "A": [
        "╔═╗",
        "╠═╣",
        "╩ ╩",
    ],
    "B": [
        "╔╗ ",
        "╠╩╗",
        "╚═╝",
    ],
    "C": [
        "╔═╗",
        "║  ",
        "╚═╝",
    ],
    "D": [
        "╔╦╗",
        " ║║",
        "═╩╝",
    ],
    "E": [
        "╔═╗",
        "╠╣ ",
        "╚═╝",
    ],
    "F": [
        "╔═╗",
        "╠╣ ",
        "╚  ",
    ],
    "G": [
        "╔═╗",
        "║ ╦",
        "╚═╝",
    ],
    "H": [
        "╦ ╦",
        "╠═╣",
        "╩ ╩",
    ],
    "I": [
        "╦",
        "║",
        "╩",
    ],
    "J": [
        " ╦",
        " ║",
        "╚╝",
    ],
    "K": [
        "╦╔═",
        "╠╩╗",
        "╩ ╩",
    ],
    "L": [
        "╦  ",
        "║  ",
        "╩═╝",
    ],
    "M": [
        "╔╦╗",
        "║║║",
        "╩ ╩",
    ],
    "N": [
        "╔╗╔",
        "║║║",
        "╝╚╝",
    ],
    "O": [
        "╔═╗",
        "║ ║",
        "╚═╝",
    ],
    "P": [
        "╔═╗",
        "╠═╝",
        "╩  ",
    ],
    "Q": [
        "╔═╗ ",
        "║═╬╗",
        "╚═╝╚",
    ],
    "R": [
        "╦═╗",
        "╠╦╝",
        "╩╚═",
    ],
    "S": [
        "╔═╗",
        "╚═╗",
        "╚═╝",
    ],
    "T": [
        "╔╦╗",
        " ║ ",
        " ╩ ",
    ],
    "U": [
        "╦ ╦",
        "║ ║",
        "╚═╝",
    ],
    "V": [
        "╦  ╦",
        "╚╗╔╝",
        " ╚╝ ",
    ],
    "W": [
        "╦ ╦",
        "║║║",
        "╚╩╝",
    ],
    "X": [
        "═╗ ╦",
        "╔╩╦╝",
        "╩ ╚═",
    ],
    "Y": [
        "╦ ╦",
        "╚╦╝",
        " ╩ ",
    ],
    "Z": [
        "╔═╗",
        "╔═╝",
        "╚═╝",
    ],
    "0": [
        "╔═╗",
        "║ ║",
        "╚═╝",
    ],
    "1": [
        "╗",
        "║",
        "╩",
    ],
    "2": [
        "╔═╗",
        "╔═╝",
        "╚═╝",
    ],
    "3": [
        "╔═╗",
        " ═╣",
        "╚═╝",
    ],
    "4": [
        "╦ ╦",
        "╚═╣",
        "  ╩",
    ],
    "5": [
        "╔═╗",
        "╚═╗",
        "╚═╝",
    ],
    "6": [
        "╔═╗",
        "╠═╗",
        "╚═╝",
    ],
    "7": [
        "═╗",
        " ║",
        " ╩",
    ],
    "8": [
        "╔═╗",
        "╠═╣",
        "╚═╝",
    ],
    "9": [
        "╔═╗",
        "╚═╣",
        "╚═╝",
    ],
    " ": [
        "  ",
        "  ",
        "  ",
    ],
    "!": [
        "║",
        "║",
        "▫",
    ],
    "\"": [
        "╚╚",
        "  ",
        "  ",
    ],
    "£": [
        "╔═╗",
        "╬═ ",
        "╩══",
    ],
    "$": [
        "╔╬╗",
        "╚╬╗",
        "╚╬╝",
    ],
    "%": [
        "▫ ╦ ",
        " ╔╝ ",
        " ╩ ▫",
    ],
    "\\": [
        "╦ ",
        "╚╗",
        " ╩",
    ],
    "(": [
        "╔",
        "║",
        "╚",
    ],
    ")": [
        "╗",
        "║",
        "╝",
    ],
    "=": [
        "  ",
        "══",
        "══",
    ],
    "'": [
        "╚",
        " ",
        " ",
    ],
    "?": [
        "╔═╗",
        " ╔╝",
        " ▫ ",
    ],
    "/": [
        " ╦",
        "╔╝",
        "╩ ",
    ],
    "|": [
        "║",
        "║",
        "║",
    ],
    "-": [
        "  ",
        "══",
        "  ",
    ],
    "+": [
        " ║ ",
        "═╬═",
        " ║ ",
    ],
    ":": [
        "╗",
        " ",
        "╗",
    ],
    ".": [
        " ",
        " ",
        "╗",
    ],
    "_": [
        "   ",
        "   ",
        "═══",
    ],
    "[": [
        "╔",
        "║",
        "╚",
    ],
    "]": [
        "╗",
        "║",
        "╝",
    ],
    "{": [
        "╔",
        "╣",
        "╚",
    ],
    "}": [
        "╗",
        "╠",
        "╝",
    ],
    "#": [
        "  ",
        "╬╬",
        "╬╬",
    ],
    "~": [
        "   ",
        "╔═╝",
        "   ",
    ],
    ",": [
        " ",
        " ",
        "╗",
    ],
    ";": [
        "╗",
        " ",
        "╗",
    ],
    "°": [
        "┌┐",
        "└┘",
        "  ",
    ],
}
# fmt: on


with open("./data/memes.json", "r") as f:
    MEMES = json.load(f)

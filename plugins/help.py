from __future__ import annotations

from typing import TYPE_CHECKING

from plugins import Command, command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(aliases=("help",), is_unlisted=True)
async def commands(msg: Message) -> None:
    cmd = msg.arg.lower()
    if cmd in msg.conn.commands and msg.conn.commands[cmd].helpstr:
        # asking for a specific command
        message = f"<b>{cmd}</b> {msg.conn.commands[cmd].helpstr}"
        await msg.reply_htmlbox(message)
    elif cmd == "":
        # asking for a list of every command
        helpstrings = Command.get_all_helpstrings()
        if not helpstrings:
            return

        html = ""
        for key in helpstrings:
            html += f"<b>{key}</b> {helpstrings[key]}<br>"
        await msg.reply_htmlbox(html[:-4])
    else:
        await msg.reply("Comando non trovato")

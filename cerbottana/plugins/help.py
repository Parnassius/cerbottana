from __future__ import annotations

from typing import TYPE_CHECKING

from cerbottana.html_utils import get_doc

from . import Command, command_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message


@command_wrapper(aliases=("help",), is_unlisted=True)
async def commands(msg: Message) -> None:
    cmd = msg.arg.lower()
    if cmd in msg.conn.commands and msg.conn.commands[cmd].helpstr:
        # asking for a specific command
        doc = get_doc()
        doc.line("b", cmd)
        doc.asis(f" {msg.conn.commands[cmd].helpstr}")
        await msg.reply_htmlbox(doc)
    elif cmd == "":
        # asking for a list of every command
        helpstrings = Command.get_all_helpstrings()
        if not helpstrings:
            return

        doc = get_doc()
        for key, helpstring in helpstrings.items():
            doc.line("b", key)
            doc.asis(f" {helpstring}")
            doc.stag("br")
        await msg.reply_htmlbox(doc)
    else:
        await msg.reply("Comando non trovato")

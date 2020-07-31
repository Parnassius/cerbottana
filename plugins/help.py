from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from plugins import Command, command_wrapper

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper(is_unlisted=True)
async def help(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if arg in conn.commands and conn.commands[arg].helpstr:
        # asking for a specific command
        message = "<b>{}</b> {}".format(arg, conn.commands[arg].helpstr)
        await conn.send_htmlbox(room, user, message)
    elif arg == "":
        # asking for a list of every command
        helpstrings = Command.get_all_helpstrings()
        if not helpstrings:
            return

        html = ""
        for key in helpstrings:
            html += "<b>{}</b> {}<br>".format(key, helpstrings[key])
        await conn.send_htmlbox(room, user, html[:-4])
    else:
        await conn.send_reply(room, user, "Comando non trovato")

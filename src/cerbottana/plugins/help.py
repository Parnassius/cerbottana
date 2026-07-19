from domify import html_elements as e
from domify.base_element import BaseElement

from cerbottana.models.message import Message
from cerbottana.plugins import Command, command_wrapper


@command_wrapper(aliases=("help",), is_unlisted=True)
async def commands(msg: Message) -> None:
    cmd = msg.arg.lower()
    if cmd in msg.conn.commands and msg.conn.commands[cmd].helpstr:
        # asking for a specific command
        html = e.B(cmd) + e.RawTextNode(f" {msg.conn.commands[cmd].helpstr}")
        await msg.reply_htmlbox(html)
    elif cmd == "":
        # asking for a list of every command
        helpstrings = Command.get_all_helpstrings()
        if not helpstrings:
            return

        html = BaseElement()
        for key, helpstring in helpstrings.items():
            html.add(e.B(key) + e.RawTextNode(f" {helpstring}") + e.Br())
        await msg.reply_htmlbox(html)
    else:
        await msg.reply("Comando non trovato")

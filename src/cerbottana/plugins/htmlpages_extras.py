from __future__ import annotations

from cerbottana.models.message import Message
from cerbottana.models.room import Room
from cerbottana.plugins import command_wrapper


@command_wrapper()
async def changepage(msg: Message) -> None:
    if len(msg.args) != 3:
        return

    pageid = msg.args[0]
    room = Room.get(msg.conn, msg.args[1])

    try:
        page = int(msg.args[2])
    except ValueError:
        page = 1

    await msg.reply_htmlpage(pageid, room, page)

from __future__ import annotations

from typing import TYPE_CHECKING

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(
    aliases=("cc",),
    helpstr="<i>nick1, nick2, ...</i> Visualizza i colori dei nickname elencati.",
)
async def colorcompare(msg: Message) -> None:
    # Ignore empty args: they're usually typos, i.e. "a,,b".
    args = [arg for arg in msg.args if arg]
    if not args:
        return

    html = utils.render_template("commands/colorcompare.html", usernames=args)
    await msg.reply_htmlbox(html)

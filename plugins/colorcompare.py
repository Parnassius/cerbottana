from __future__ import annotations

from typing import TYPE_CHECKING

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(
    helpstr="<i>nick1, nick2, ...</i> Visualizza i colori dei nickname elencati."
)
async def colorcompare(msg: Message) -> None:
    if msg.arg == "":
        return

    cell = (
        "<td>"
        '  <div style="background:{color};text-align:center">'
        "    <br><br>{username}<br><br><br>"
        "  </div>"
        "</td>"
    )

    html = '<table style="width:100%;table-layout:fixed">'
    html += "<tr>"
    for i in msg.args:
        html += cell.format(
            color=utils.username_color(utils.to_user_id(i)),
            username=utils.html_escape(i),
        )
    html += "</tr>"
    html += "</table>"

    await msg.reply_htmlbox(html)

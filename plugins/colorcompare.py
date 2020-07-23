from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import utils
from plugins import plugin_wrapper

if TYPE_CHECKING:
    from connection import Connection


@plugin_wrapper(
    helpstr="<i>nick1, nick2, ...</i> Visualizza i colori dei nickname elencati."
)
async def colorcompare(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    if arg == "":
        return

    cell = "<td>"
    cell += '  <div style="background:{color};text-align:center"><br><br>{username}<br><br><br></div>'
    cell += "</td>"

    html = '<table style="width:100%;table-layout:fixed">'
    html += "<tr>"
    for i in arg.split(","):
        html += cell.format(
            color=utils.username_color(utils.to_user_id(i)),
            username=utils.html_escape(i),
        )
    html += "</tr>"
    html += "</table>"

    await conn.send_htmlbox(room, user, html)

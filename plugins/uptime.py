from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Optional

from plugins import command_wrapper

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper()
async def uptime(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if conn.connection_start is None:
        return

    s = int(time() - conn.connection_start)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    days = "{} day{}, ".format(d, "" if d == 1 else "s") if d > 0 else ""
    hours = "{} hour{}, ".format(h, "" if h == 1 else "s") if h > 0 else ""
    minutes = "{} minute{}, ".format(m, "" if m == 1 else "s") if m > 0 else ""
    seconds = "{} second{}".format(s, "" if s == 1 else "s")

    await conn.send_reply(room, user, days + hours + minutes + seconds)

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING

from cerbottana.plugins import command_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message


@command_wrapper()
async def uptime(msg: Message) -> None:
    if msg.conn.connection_start is None:
        return

    s = int(time() - msg.conn.connection_start)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    uptime_ = ""
    if d > 0:
        plural = "" if d == 1 else "s"
        uptime_ += f"{d} day{plural}, "
    if h > 0:
        plural = "" if h == 1 else "s"
        uptime_ += f"{h} hour{plural}, "
    if m > 0:
        plural = "" if m == 1 else "s"
        uptime_ += f"{m} minute{plural}, "
    plural = "" if s == 1 else "s"
    uptime_ += f"{s} second{plural}"

    await msg.reply(uptime_)

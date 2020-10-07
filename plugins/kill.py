from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(aliases=("ammaz", "ammazz"))
async def kill(msg: Message) -> None:
    if msg.user.is_administrator and msg.conn.websocket is not None:
        for task in asyncio.all_tasks(loop=msg.conn.loop):
            task.cancel()
        await msg.conn.websocket.close()

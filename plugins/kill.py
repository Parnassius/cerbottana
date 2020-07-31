from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper()
async def kill(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if utils.to_user_id(user) in conn.administrators and conn.websocket is not None:
        for task in asyncio.all_tasks(loop=conn.loop):
            task.cancel()
        await conn.websocket.close()

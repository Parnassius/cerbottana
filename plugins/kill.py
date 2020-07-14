from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import utils
from plugin_loader import plugin_wrapper

if TYPE_CHECKING:
    from connection import Connection


@plugin_wrapper()
async def kill(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if utils.to_user_id(user) in conn.administrators and conn.websocket is not None:
        await conn.websocket.close()

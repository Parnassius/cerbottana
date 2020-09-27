from __future__ import annotations

from typing import TYPE_CHECKING, Dict

import utils
from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(aliases=("token",))
async def dashboard(msg: Message) -> None:
    if not msg.conn.main_room or not msg.user.has_role("driver", msg.conn.main_room):
        return
    admin_rank = msg.user.rank(msg.conn.main_room)

    rooms: Dict[str, str] = {}

    for room in msg.user.rooms:
        rooms[room.roomid] = msg.user.rank(room) or " "

    token_id = utils.create_token(rooms, 1, admin_rank)

    await msg.user.send(f"{msg.conn.domain}?token={token_id}")

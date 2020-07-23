from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

import utils
from plugins import command_wrapper
from room import Room

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper(aliases=["token"])
async def dashboard(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    userid = utils.to_user_id(user)
    for r in conn.rooms:
        users = Room.get(r).users
        if userid in users and utils.is_driver(users[userid]["rank"]):
            admin_rank = users[userid]["rank"]
            break
    else:
        return

    rooms: Dict[str, str] = dict()

    for r in conn.rooms + conn.private_rooms:
        users = Room.get(r).users
        if userid in users:
            rooms[r] = users[userid]["rank"]

    token_id = utils.create_token(rooms, 1, admin_rank)

    await conn.send_pm(
        user, "{url}?token={token}".format(url=conn.domain, token=token_id)
    )

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from connection import Connection

from plugin_loader import plugin_wrapper
import utils

from room import Room


@plugin_wrapper(aliases=["token"])
async def dashboard(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    userid = utils.to_user_id(user)
    for r in conn.rooms:
        users = Room.get(r).users
        if userid in users and utils.is_driver(users[userid]["rank"]):
            rank = users[userid]["rank"]
            break
    else:
        return

    private_rooms = [r for r in conn.private_rooms if userid in Room.get(r).users]

    token_id = utils.create_token(rank, private_rooms)

    await conn.send_pm(
        user, "{url}?token={token}".format(url=conn.domain, token=token_id)
    )

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from connection import Connection

import os

from database import Database

from plugin_loader import plugin_wrapper
import utils

from room import Room


"""
CREATE TABLE tokens (
    id INTEGER,
    token TEXT,
    rank TEXT,
    prooms TEXT,
    scadenza TEXT,
    PRIMARY KEY(id)
);

CREATE INDEX idx_tokens_token
ON tokens (
    token
);
"""


def create_token(rank: str, private_rooms: List[str]) -> str:
    token_id = os.urandom(16).hex()
    prooms = ",".join(private_rooms) if private_rooms else None

    db = Database()
    sql = "INSERT INTO tokens (token, rank, prooms, scadenza) VALUES (?, ?, ?, DATETIME('now', '+1 minute'))"
    db.executenow(sql, [token_id, rank, prooms])

    return token_id


@plugin_wrapper(aliases=["dashboard"])
async def token(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    userid = utils.to_user_id(user)
    for r in conn.rooms:
        users = Room.get(r).users
        if userid in users and utils.is_driver(users[userid]["rank"]):
            rank = users[userid]["rank"]
            break
    else:
        return

    private_rooms = [r for r in conn.private_rooms if userid in Room.get(r).users]

    token_id = create_token(rank, private_rooms)

    await conn.send_pm(
        user, "{url}?token={token}".format(url=conn.domain, token=token_id)
    )

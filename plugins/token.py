from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from connection import Connection

import os

import database

from plugin_loader import plugin_wrapper
import utils

from room import Room


"""
CREATE TABLE tokens (
    id INTEGER,
    token TEXT,
    rank TEXT,
    scadenza TEXT,
    PRIMARY KEY(id)
);

CREATE INDEX idx_tokens_token
ON tokens (
    token
);
"""


def create_token(conn: Connection, rank: str) -> str:
    token_id = os.urandom(16).hex()

    db = database.open_db()
    sql = "INSERT INTO tokens (token, rank, scadenza) VALUES (?, ?, DATETIME('now', '+1 minute'))"
    db.execute(sql, [token_id, rank])
    db.connection.commit()
    db.connection.close()

    return token_id


@plugin_wrapper(aliases=["dashboard"])
async def token(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    userid = utils.to_user_id(user)
    for room in conn.rooms:
        users = Room.get(room).users
        if userid in users and utils.is_driver(users[userid]["rank"]):
            rank = users[userid]["rank"]
            break
    else:
        return

    token_id = create_token(conn, rank)

    await conn.send_pm(
        user, "{url}?token={token}".format(url=os.environ["DOMAIN"], token=token_id)
    )

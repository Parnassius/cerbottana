from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from connection import Connection

import random

from database import Database

from inittasks import inittask_wrapper
from plugin_loader import plugin_wrapper


@inittask_wrapper()
async def create_table(conn: Connection) -> None:
    db = Database()

    sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'eightball'"
    if not db.execute(sql).fetchone():
        sql = """CREATE TABLE eightball (
            id INTEGER,
            answer TEXT,
            PRIMARY KEY(id)
        )"""
        db.execute(sql)

        sql = "INSERT INTO metadata (key, value) VALUES ('table_version_eightball', '1')"
        db.execute(sql)

        db.commit()


@plugin_wrapper(aliases=["8ball"], helpstr="Chiedi qualsiasi cosa!")
async def eightball(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    db = Database()
    answers = db.execute("SELECT answer FROM eightball").fetchall()
    if not answers:
        return
    answer = random.choice(answers)["answer"]
    await conn.send_reply(room, user, answer)

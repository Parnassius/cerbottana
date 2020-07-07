from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from connection import Connection

import random

from database import Database

from plugin_loader import plugin_wrapper


"""
CREATE TABLE eight_ball (
    id INTEGER,
    risposta TEXT,
    PRIMARY KEY(id)
);
"""


@plugin_wrapper(aliases=["8ball"], helpstr="Chiedi qualsiasi cosa!")
async def eightball(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    db = Database()
    answers = db.execute("SELECT risposta FROM eight_ball").fetchall()
    answer = random.choice(answers)["risposta"]
    await conn.send_reply(room, user, answer)

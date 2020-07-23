from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

from flask import g, render_template, request

from database import Database
from plugins import plugin_wrapper, route_wrapper
from tasks import init_task_wrapper

if TYPE_CHECKING:
    from connection import Connection


@init_task_wrapper()
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

        sql = (
            "INSERT INTO metadata (key, value) VALUES ('table_version_eightball', '1')"
        )
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


@route_wrapper("/eightball", methods=("GET", "POST"), require_driver=True)
def eightball_route() -> str:

    if request.method == "POST":

        if "answers" in request.form:
            sql = "DELETE FROM eightball"
            g.db.execute(sql)

            answers = list(
                filter(
                    None,
                    map(
                        str.strip, sorted(request.form["answers"].strip().splitlines())
                    ),
                )
            )
            sql = "INSERT INTO eightball (answer) VALUES " + ", ".join(
                ["(?)"] * len(answers)
            )
            g.db.execute(sql, answers)

            g.db.commit()

    sql = "SELECT * FROM eightball ORDER BY answer"
    rs = g.db.execute(sql).fetchall()

    return render_template("eightball.html", rs=rs)

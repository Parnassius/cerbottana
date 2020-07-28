from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

from flask import g, render_template, request

import databases.database as d
from database import Database
from plugins import command_wrapper, route_wrapper

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper(aliases=["8ball"], helpstr="Chiedi qualsiasi cosa!")
async def eightball(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    db = Database.open()

    with db.get_session() as session:
        answers = session.query(d.EightBall.answer).all()

    if not answers:
        return

    answer = random.choice(answers)[0]
    await conn.send_reply(room, user, answer)


@route_wrapper("/eightball", methods=("GET", "POST"), require_driver=True)
def eightball_route() -> str:

    with g.db.get_session() as session:
        if request.method == "POST":

            if "answers" in request.form:
                session.query(d.EightBall).delete()

                answers = set(request.form["answers"].strip().splitlines())
                session.add_all(
                    [d.EightBall(answer=answer.strip()) for answer in answers]
                )

        rs = session.query(d.EightBall).order_by(d.EightBall.answer).all()

        return render_template("eightball.html", rs=rs)

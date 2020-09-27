from __future__ import annotations

import random
from typing import TYPE_CHECKING

from flask import render_template, request

import databases.database as d
from database import Database
from plugins import command_wrapper, route_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(aliases=("8ball",), helpstr="Chiedi qualsiasi cosa!")
async def eightball(msg: Message) -> None:
    db = Database.open()

    with db.get_session() as session:
        answers = session.query(d.EightBall).all()

        if not answers:
            return

        answer = random.choice(answers).answer
        await msg.reply(answer)


@route_wrapper("/eightball", methods=("GET", "POST"), require_driver=True)
def eightball_route() -> str:
    db = Database.open()

    with db.get_session() as session:
        if request.method == "POST":

            if "answers" in request.form:
                session.query(d.EightBall).delete()

                answers = set(request.form["answers"].strip().splitlines())
                session.add_all(  # type: ignore  # sqlalchemy
                    [d.EightBall(answer=answer.strip()) for answer in answers]
                )

        rs = session.query(d.EightBall).order_by(d.EightBall.answer).all()

        return render_template("eightball.html", rs=rs)

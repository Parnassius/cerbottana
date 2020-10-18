from __future__ import annotations

import random
from typing import TYPE_CHECKING

from sqlalchemy.orm import Query
from sqlalchemy.orm.exc import ObjectDeletedError

import databases.database as d
from database import Database
from plugins import command_wrapper, htmlpage_wrapper

if TYPE_CHECKING:
    from models.message import Message
    from models.room import Room
    from models.user import User


@command_wrapper(aliases=("8ball",), helpstr="Chiedi qualsiasi cosa!")
async def eightball(msg: Message) -> None:
    db = Database.open()

    with db.get_session() as session:
        answers = session.query(d.EightBall).all()

        if not answers:
            return

        answer = random.choice(answers).answer
        await msg.reply(answer)


@command_wrapper(aliases=("8ballanswers",))
async def eightballanswers(msg: Message) -> None:
    if not msg.conn.main_room or not msg.user.has_role("driver", msg.conn.main_room):
        return

    try:
        page = int(msg.arg)
    except ValueError:
        page = 1

    await msg.user.send_htmlpage("eightball", msg.conn.main_room, page)


@command_wrapper(aliases=("add8ballanswer", "neweightballanswer", "new8ballanswer"))
async def addeightballanswer(msg: Message) -> None:
    if not msg.conn.main_room or not msg.user.has_role("driver", msg.conn.main_room):
        return

    if not msg.arg:
        await msg.reply("Cosa devo salvare?")
        return

    db = Database.open()
    with db.get_session() as session:
        result = d.EightBall(answer=msg.arg)
        session.add(result)
        session.commit()  # type: ignore  # sqlalchemy

        try:
            if result.id:
                await msg.reply("Risposta salvata.")
                return
        except ObjectDeletedError:
            pass
        await msg.reply("Risposta già esistente.")


@command_wrapper(
    aliases=(
        "remove8ballanswer",
        "deleteeightballanswer",
        "delete8ballanswer",
        "deleightballanswer",
        "del8ballanswer",
        "rmeightballanswer",
        "rm8ballanswer",
    )
)
async def removeeightballanswer(msg: Message) -> None:
    if not msg.conn.main_room or not msg.user.has_role("driver", msg.conn.main_room):
        return

    if not msg.arg:
        await msg.reply("Che risposta devo cancellare?")
        return

    db = Database.open()
    with db.get_session() as session:
        result = session.query(d.EightBall).filter_by(answer=msg.arg).delete()

        if result:
            await msg.reply("Risposta cancellata.")
        else:
            await msg.reply("Risposta inesistente.")


@command_wrapper()
async def removeeightballanswerid(msg: Message) -> None:
    if not msg.conn.main_room or not msg.user.has_role("driver", msg.conn.main_room):
        return

    if len(msg.args) != 2:
        return

    db = Database.open()
    with db.get_session() as session:
        session.query(d.EightBall).filter_by(id=msg.args[0]).delete()

    try:
        page = int(msg.args[1])
    except ValueError:
        page = 1

    await msg.user.send_htmlpage("eightball", msg.conn.main_room, page)


@htmlpage_wrapper("eightball", required_rank="driver", main_room_only=True)
def eightball_htmlpage(user: User, room: Room) -> Query:  # type: ignore[type-arg]
    return Query(d.EightBall).order_by(d.EightBall.answer)

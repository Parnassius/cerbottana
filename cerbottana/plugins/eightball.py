from __future__ import annotations

import json
import random
from typing import TYPE_CHECKING

from domify.base_element import BaseElement
from sqlalchemy import delete, select
from sqlalchemy.orm.exc import ObjectDeletedError
from sqlalchemy.sql import Select

import cerbottana.databases.database as d
from cerbottana import utils
from cerbottana.database import Database
from cerbottana.html_utils import HTMLPageCommand

from . import command_wrapper, htmlpage_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message
    from cerbottana.models.room import Room
    from cerbottana.models.user import User


@command_wrapper(
    aliases=("8ball",), helpstr="Chiedi qualsiasi cosa!", required_rank_editable=True
)
async def eightball(msg: Message) -> None:
    db = Database.open()

    with db.get_session() as session:
        language_name = msg.language
        if language_name not in DEFAULT_ANSWERS:
            language_name = "English"
        answers = DEFAULT_ANSWERS[language_name]

        if msg.room:
            stmt = select(d.EightBall.answer).filter_by(roomid=msg.room.roomid)
            answers.extend(session.execute(stmt).scalars())

        await msg.reply(random.choice(answers))


@command_wrapper(
    aliases=("add8ballanswer", "neweightballanswer", "new8ballanswer"),
    required_rank="driver",
    parametrize_room=True,
)
async def addeightballanswer(msg: Message) -> None:
    if not msg.arg:
        await msg.reply("Cosa devo salvare?")
        return

    db = Database.open()
    with db.get_session() as session:
        result = d.EightBall(answer=msg.arg, roomid=msg.parametrized_room.roomid)
        session.add(result)
        session.commit()

        try:
            if result.id:
                await msg.reply("Risposta salvata.")
                if msg.room is None:
                    await msg.parametrized_room.send_modnote(
                        "EIGHTBALL ANSWER ADDED", msg.user, msg.arg
                    )
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
    ),
    required_rank="driver",
    parametrize_room=True,
)
async def removeeightballanswer(msg: Message) -> None:
    if not msg.arg:
        await msg.reply("Che risposta devo cancellare?")
        return

    db = Database.open()
    with db.get_session() as session:
        stmt = delete(d.EightBall).filter_by(
            answer=msg.arg, roomid=msg.parametrized_room.roomid
        )
        if session.execute(stmt).rowcount:  # type: ignore[attr-defined]
            await msg.reply("Risposta cancellata.")
            if msg.room is None:
                await msg.parametrized_room.send_modnote(
                    "EIGHTBALL ANSWER REMOVED", msg.user, msg.arg
                )
        else:
            await msg.reply("Risposta inesistente.")


@command_wrapper(required_rank="driver", parametrize_room=True)
async def removeeightballanswerid(msg: Message) -> None:
    if len(msg.args) != 2:
        return

    db = Database.open()
    with db.get_session() as session:
        stmt = select(d.EightBall).filter_by(
            id=msg.args[0], roomid=msg.parametrized_room.roomid
        )
        answer: d.EightBall  # TODO: remove annotation
        if answer := session.scalar(stmt):
            if msg.room is None:
                await msg.parametrized_room.send_modnote(
                    "EIGHTBALL ANSWER REMOVED", msg.user, answer.answer
                )
            session.delete(answer)

    try:
        page = int(msg.args[1])
    except ValueError:
        page = 1

    await msg.user.send_htmlpage("eightballanswers", msg.parametrized_room, page)


@htmlpage_wrapper("eightballanswers", aliases=("8ballanswers",), required_rank="driver")
def eightball_htmlpage(user: User, room: Room, page: int) -> BaseElement:
    # TODO: remove annotation
    stmt: Select = (
        select(d.EightBall).filter_by(roomid=room.roomid).order_by(d.EightBall.answer)
    )

    html = HTMLPageCommand(
        user,
        room,
        "eightballanswers",
        stmt,
        title="8ball answers",
        fields=[("Answer", "answer")],
        actions=[
            (
                "removeeightballanswerid",
                ["_roomid", "id", "_page"],
                False,
                "trash",
                "Delete",
            )
        ],
    )

    html.load_page(page)

    return html.doc


with utils.get_data_file("eightball.json").open(encoding="utf-8") as f:
    DEFAULT_ANSWERS: dict[str, list[str]] = json.load(f)

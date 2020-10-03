from __future__ import annotations

import random
from typing import TYPE_CHECKING

from environs import Env
from flask import abort, render_template
from flask import session as web_session
from sqlalchemy.orm.exc import ObjectDeletedError
from sqlalchemy.sql import func

import databases.database as d
import utils
from database import Database
from plugins import command_wrapper, parametrize_room, route_wrapper

if TYPE_CHECKING:
    from models.message import Message


env = Env()
env.read_env()


@command_wrapper(aliases=("newquote", "quote"))
async def addquote(msg: Message) -> None:
    if msg.room is None or not msg.user.has_role("driver", msg.room):
        return

    if not msg.arg:
        await msg.room.send("Cosa devo salvare?")
        return

    maxlen = 250  # lower than the message limit to have space for metadata
    if len(msg.arg) > maxlen:
        await msg.room.send(f"Quote troppo lunga, max {maxlen} caratteri.")
        return

    db = Database.open()
    with db.get_session() as session:
        result = d.Quotes(
            message=msg.arg,
            roomid=msg.room.roomid,
            author=msg.user.userid,
            date=func.date(),
        )
        session.add(result)
        session.commit()  # type: ignore  # sqlalchemy

        try:
            if result.id:
                await msg.room.send("Quote salvata.")
                return
        except ObjectDeletedError:
            pass
        await msg.room.send("Quote già esistente.")


@command_wrapper(aliases=("q",))
@parametrize_room
async def randquote(msg: Message) -> None:
    if msg.arg:
        phrase = "Non ho capito."
        if msg.room is not None:
            phrase += (
                f" Usa ``{msg.conn.command_character}quote messaggio``"
                " per salvare una quote."
            )
        await msg.reply(phrase)
        return

    db = Database.open()
    with db.get_session() as session:
        quotes = (
            session.query(d.Quotes).filter_by(roomid=msg.parametrized_room.roomid).all()
        )

        if not quotes:
            await msg.reply("Nessuna quote registrata per questa room.")
            return

        quote = random.choice(quotes).message
        await msg.reply(quote)


@command_wrapper(aliases=("deletequote", "delquote", "rmquote"))
async def removequote(msg: Message) -> None:
    if msg.room is None or not msg.user.has_role("driver", msg.room):
        return

    if not msg.arg:
        await msg.room.send("Che quote devo cancellare?")
        return

    db = Database.open()
    with db.get_session() as session:
        result = (
            session.query(d.Quotes)
            .filter_by(message=msg.arg, roomid=msg.room.roomid)
            .delete()
        )

        if result:
            await msg.room.send("Quote cancellata.")
        else:
            await msg.room.send("Quote inesistente.")


@command_wrapper(aliases=("quotes", "quoteslist"))
@parametrize_room
async def quotelist(msg: Message) -> None:
    db = Database.open()
    with db.get_session() as session:
        quotes_n = (
            session.query(func.count(d.Quotes.id))  # type: ignore  # sqlalchemy
            .filter_by(roomid=msg.parametrized_room.roomid)
            .scalar()
        )

    if not quotes_n:
        await msg.reply("Nessuna quote da visualizzare.")
        return

    phrase = f"{msg.conn.domain}quotes/{msg.parametrized_room}"
    if msg.parametrized_room.is_private:
        token_id = utils.create_token({msg.parametrized_room.roomid: " "})
        phrase += f"?token={token_id}"

    await msg.reply(phrase)


@route_wrapper("/quotes/<room>")
def quotes_route(room: str) -> str:
    if room in env.list("PRIVATE_ROOMS"):
        if not web_session.get(room):
            abort(401)

    db = Database.open()

    with db.get_session() as session:
        rs = session.query(d.Quotes).filter_by(roomid=room).all()
        if not rs:
            abort(401)  # no quotes for this room

        return render_template("quotes.html", rs=rs, room=room)

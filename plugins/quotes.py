from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

from environs import Env
from flask import abort, g, render_template
from flask import session as web_session
from sqlalchemy.sql import func

import databases.database as d
import utils
from database import Database
from plugins import command_wrapper, parametrize_room, route_wrapper

if TYPE_CHECKING:
    from connection import Connection


env = Env()
env.read_env()


@command_wrapper(aliases=["newquote", "quote"])
async def addquote(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if room is None or not utils.is_driver(user):
        return

    if not arg:
        await conn.send_message(room, "Cosa devo salvare?")
        return

    maxlen = 250  # lower than the message limit to have space for metadata
    if len(arg) > maxlen:
        await conn.send_message(room, f"Quote troppo lunga, max {maxlen} caratteri.")
        return

    db = Database.open()
    with db.get_session() as session:
        result = session.execute(
            d.Quotes.__table__.insert().values(
                message=arg,
                roomid=room,
                author=utils.to_user_id(user),
                date=func.date(),
            )
        )

        if result.inserted_primary_key[0]:
            await conn.send_message(room, "Quote salvata.")
        else:
            await conn.send_message(room, "Quote già esistente.")


@command_wrapper(aliases=["q"])
@parametrize_room
async def randquote(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if len(arg.split(",")) > 1:  # expecting 1 parameter given by @parametrize_room
        msg = "Non ho capito."
        if room is not None:
            msg += (
                f" Usa ``{conn.command_character}quote messaggio``"
                " per salvare una quote."
            )
        await conn.send_reply(room, user, msg)
        return

    db = Database.open()
    with db.get_session() as session:
        rs = session.query(d.Quotes.message).filter_by(roomid=arg).all()

    if not rs:
        await conn.send_reply(room, user, "Nessuna quote registrata per questa room.")
        return

    quote = random.choice(rs)[0]

    parsed_quote = quote
    # if quote["date"]:  # backwards compatibility with old quotes without a date
    #   parsed_quote += "  __({})__".format(quote["date"])
    await conn.send_reply(room, user, parsed_quote)


@command_wrapper(aliases=["deletequote", "delquote", "rmquote"])
async def removequote(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    if room is None or not utils.is_driver(user):
        return

    if not arg:
        await conn.send_message(room, "Che quote devo cancellare?")
        return

    db = Database.open()
    with db.get_session() as session:
        result = session.query(d.Quotes).filter_by(message=arg, roomid=room).delete()

        if result:
            await conn.send_message(room, "Quote cancellata.")
        else:
            await conn.send_message(room, "Quote inesistente.")


@command_wrapper(aliases=["quotes", "quoteslist"])
@parametrize_room
async def quotelist(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    quoteroom = arg.split(",")[0]

    db = Database.open()
    with db.get_session() as session:
        quotes_n = (
            session.query(func.count(d.Quotes)).filter_by(roomid=quoteroom).first()
        )

    if not quotes_n:
        await conn.send_reply(room, user, "Nessuna quote da visualizzare.")
        return

    message = f"{conn.domain}quotes/{quoteroom}"
    if utils.is_private(conn, quoteroom):
        token_id = utils.create_token({quoteroom: " "})
        message += f"?token={token_id}"

    await conn.send_reply(room, user, message)


@route_wrapper("/quotes/<room>")
def quotes(room: str) -> str:
    if room in env.list("PRIVATE_ROOMS"):
        if not web_session.get(room):
            abort(401)

    with g.db.get_session() as session:
        rs = session.query(d.Quotes).filter_by(roomid=room).all()
        if not rs:
            abort(401)  # no quotes for this room

    return render_template("quotes.html", rs=rs, room=room)

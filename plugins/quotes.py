from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

from environs import Env
from flask import abort, g, render_template, session

import utils
from database import Database
from plugins import parametrize_room, plugin_wrapper, route_wrapper
from tasks import init_task_wrapper

if TYPE_CHECKING:
    from connection import Connection


env = Env()
env.read_env()


@init_task_wrapper()
async def create_table(conn: Connection) -> None:  # lgtm [py/similar-function]
    db = Database()

    sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'quotes'"
    if not db.execute(sql).fetchone():
        sql = """CREATE TABLE quotes (
            id INTEGER,
            message TEXT,
            roomid TEXT,
            author TEXT,
            date TEXT,
            PRIMARY KEY(id)
        )"""
        db.execute(sql)

        sql = """CREATE UNIQUE INDEX idx_unique_quotes_message_roomid
        ON quotes (
            message,
            roomid
        )"""
        db.execute(sql)

        sql = "INSERT INTO metadata (key, value) VALUES ('table_version_quotes', '1')"
        db.execute(sql)

        db.commit()


@plugin_wrapper(aliases=["newquote", "quote"])
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

    db = Database()
    sql = "INSERT OR IGNORE INTO quotes (message, roomid, author, date) "
    sql += "VALUES (?, ?, ?, DATE())"
    db.executenow(sql, [arg, room, utils.to_user_id(user)])
    if db.connection.total_changes:
        await conn.send_message(room, "Quote salvata.")
    else:
        await conn.send_message(room, "Quote già esistente.")


@plugin_wrapper(aliases=["q"])
@parametrize_room
async def randquote(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if len(arg.split(",")) > 1:  # expecting 1 parameter given by @parametrize_room
        msg = "Non ho capito."
        if room is not None:
            msg += f" Usa ``{conn.command_character}quote messaggio`` per salvare una quote."
        await conn.send_reply(room, user, msg)
        return

    db = Database()
    sql = "SELECT message, date "
    sql += "FROM quotes WHERE roomid = ?"
    quotes = db.execute(sql, [arg]).fetchall()

    if not quotes:
        await conn.send_reply(room, user, "Nessuna quote registrata per questa room.")
        return
    quote = random.choice(quotes)

    parsed_quote = quote["message"]
    # if quote["date"]:  # backwards compatibility with old quotes without a date
    #   parsed_quote += "  __({})__".format(quote["date"])
    await conn.send_reply(room, user, parsed_quote)


@plugin_wrapper(aliases=["deletequote", "delquote", "rmquote"])
async def removequote(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    if room is None or not utils.is_driver(user):
        return

    if not arg:
        await conn.send_message(room, "Che quote devo cancellare?")
        return

    db = Database()
    db.executenow("DELETE FROM quotes WHERE message = ? AND roomid = ?", [arg, room])
    if db.connection.total_changes:
        await conn.send_message(room, "Quote cancellata.")
    else:
        await conn.send_message(room, "Quote inesistente.")


@plugin_wrapper(aliases=["quotes", "quoteslist"])
@parametrize_room
async def quotelist(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    quoteroom = arg.split(",")[0]

    db = Database()
    quotes_n = db.execute(
        "SELECT COUNT(*) FROM quotes WHERE roomid = ?", [quoteroom]
    ).fetchone()
    if not quotes_n[0]:
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
        if not session.get(room):
            abort(401)

    sql = "SELECT message, date "
    sql += "FROM quotes WHERE roomid = ?"
    rs = g.db.execute(sql, [room]).fetchall()
    if not rs:
        abort(401)  # no quotes for this room

    return render_template("quotes.html", rs=rs, room=room)

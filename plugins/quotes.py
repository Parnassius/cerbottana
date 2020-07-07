from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from connection import Connection

import random

from plugin_loader import plugin_wrapper

from database import Database
import utils


"""
CREATE TABLE quotes (
    id INTEGER,
    message TEXT,
    roomid TEXT,
    author TEXT,
    date TEXT,
    PRIMARY KEY(id)
);

CREATE UNIQUE INDEX idx_unique_quotes_message_roomid
ON QUOTES (
    message,
    roomid
);
"""


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
async def randquote(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if room is None:
        return

    if arg:
        conn.send_message(
            room, f"Usa ``{conn.command_character}addquote`` per aggiungere una quote."
        )
        return

    db = Database()
    sql = "SELECT message, date "
    sql += "FROM quotes WHERE roomid = ?"
    quotes = db.execute(sql, [room]).fetchall()

    if not quotes:
        await conn.send_message(room, "Nessuna quote registrata per questa room.")
        return
    quote = random.choice(quotes)

    parsed_quote = quote["message"]
    # if quote["date"]:  # backwards compatibility with old quotes without a date
    #   parsed_quote += "  __({})__".format(quote["date"])
    await conn.send_message(room, parsed_quote)


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

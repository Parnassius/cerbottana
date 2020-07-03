import random

from plugin_loader import plugin_wrapper

import database
import utils


"""
This plugin uses data from a table in the database.sqlite resource.
To create such table:
CREATE TABLE quotes (
    id INTEGER,
    message TEXT,
    roomid TEXT,
    author TEXT,
    date TEXT,
    PRIMARY KEY(id),
    UNIQUE(message, roomid)
)
"""


@plugin_wrapper(aliases=["newquote", "quote"])
async def addquote(self, room: str, user: str, arg: str) -> None:
    if room is None or not utils.is_driver(user):
        return

    if not arg:
        await self.send_message(room, "Cosa devo salvare?")
        return

    maxlen = 250  # lower than the message limit to have space for metadata
    if len(arg) > maxlen:
        await self.send_message(room, f"Quote troppo lunga, max {maxlen} caratteri.")
        return

    db = database.open_db()
    sql = "INSERT OR IGNORE INTO quotes (message, roomid, author, date) "
    sql += "VALUES (?, ?, ?, DATE())"
    db.execute(sql, [arg, room, utils.to_user_id(user)])
    db.connection.commit()
    if db.connection.total_changes:
        await self.send_message(room, "Quote salvata.")
    else:
        await self.send_message(room, "Quote già esistente.")
    db.connection.close()


@plugin_wrapper(aliases=["q"])
async def randquote(self, room: str, user: str, arg: str) -> None:
    if arg:
        self.send_message(
            f"Usa ``{self.command_character}addquote`` per aggiungere una quote."
        )
        return

    db = database.open_db()
    sql = "SELECT message, date "
    sql += "FROM quotes WHERE roomid = ?"
    quotes = db.execute(sql, [room]).fetchall()
    db.connection.close()

    if not quotes:
        await self.send_message(room, "Nessuna quote registrata per questa room.")
        return
    quote = random.choice(quotes)

    parsed_quote = " " + quote["message"]
    # if quote["date"]:  # backwards compatibility with old quotes without a date
    #   parsed_quote += "  __({})__".format(quote["date"])
    await self.send_message(room, parsed_quote)


@plugin_wrapper(aliases=["deletequote", "delquote", "rmquote"])
async def removequote(self, room: str, user: str, arg: str) -> None:
    if room is None or not utils.is_driver(user):
        return

    if not arg:
        await self.send_message(room, "Che quote devo cancellare?")
        return

    db = database.open_db()
    db.execute("DELETE FROM quotes WHERE message = ? AND roomid = ?", [arg, room])
    db.connection.commit()
    if db.connection.total_changes:
        await self.send_message(room, "Quote cancellata.")
    else:
        await self.send_message(room, "Quote inesistente.")
    db.connection.close()

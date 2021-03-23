from __future__ import annotations

import re
import string
from typing import TYPE_CHECKING

from sqlalchemy.orm import Query
from sqlalchemy.orm.exc import ObjectDeletedError
from sqlalchemy.sql import func

import databases.database as d
import utils
from database import Database
from plugins import command_wrapper, htmlpage_wrapper

if TYPE_CHECKING:
    from models.message import Message
    from models.room import Room
    from models.user import User


def to_html_quotebox(quote: str) -> str:
    """Generates HTML that shows a quote.

    Args:
        quote (str): Raw quote string, added through `.addquote`.

    Raises:
        BaseException: quote is empty.

    Returns:
        str: htmlbox.
    """
    if not quote:
        # This shouldn't happen because empty quotes are ignored by `.addquote`.
        raise BaseException("Trying to create quotebox for empty quote.")

    # Valid timestamp formats: [xx:xx], [xx:xx:xx]
    timestamp_regex = r"(\[\d{2}:\d{2}(?::\d{2})?\])"
    splitted = re.split(timestamp_regex, quote)

    # Return the quote unparsed if it has a custom format, aka one of these conditions
    # applies:
    # (1) Quote doesn't start with a timestamp.
    # (2) Quote only has timestamps.
    if splitted[0] or not any(part.lstrip() for part in splitted[::2]):
        return utils.linkify(quote)

    lines: list[str] = []
    for timestamp, phrase in zip(splitted[1::2], splitted[2::2]):
        # Wrap every line in a <div class="chat"></div> and if it is a regular chat
        # message format it accordingly.

        phrase = phrase.lstrip()
        if not phrase:
            # Timestamp with an empty phrase.
            # Append the timestamp to the previous phrase, it was probably part of it.
            if not lines:
                lines.append(timestamp)
            else:
                lines[-1] += timestamp
        elif ": " in phrase and phrase[0] != "(":
            # phrase is a chat message.
            # Example: "[03:56] @Plat0: Hi"

            # userstring: Username, optionally preceded by its rank.
            # body: Content of the message sent by the user.
            userstring, body = phrase.split(": ", 1)

            # rank: Character rank or "" (not " ") in case of a regular user.
            # username: userstring variable stripped of the character rank.
            if userstring[0] not in string.ascii_letters + string.digits:
                rank = userstring[0]
                username = userstring[1:]
            else:
                rank = ""
                username = userstring

            # Escape special characters: needs to be done last.
            # Timestamp doesn't need to be escaped.
            rank = utils.html_escape(rank)
            username = utils.html_escape(username)
            body = utils.linkify(body)

            lines.append(
                f"<small>{timestamp} {rank}</small>"
                f"<username>{username}:</username> "
                f"<em>{body}</em>"
            )
        else:
            # phrase is a PS message that may span over multiple lines.
            # Example: "[14:20:43] (plat0 forcibly ended a tournament.)"

            # Text contained within round parentheses is considered a separated line.
            # This is true for most use-cases but it's still euristic.
            sublines = re.split(r"(\(.*\))", phrase)
            sublines = [utils.linkify(s) for s in sublines if s.strip()]

            # The timestamp is written only on the first subline.
            sublines[0] = f"<small>{timestamp}</small> <em>{sublines[0]}</em>"
            lines += sublines
    # Merge lines
    html = '<div class="message-log" style="display: inline-block">'
    for line in lines:
        html += f'<div class="chat">{line}</div>'
    html += "</div>"
    return html


@command_wrapper(aliases=("newquote", "quote"), parametrize_room=True)
async def addquote(msg: Message) -> None:
    # Permissions for this command are temporarily lowered to voice level.

    if not msg.arg:
        await msg.reply("Cosa devo salvare?")
        return

    db = Database.open()
    with db.get_session() as session:
        result = d.Quotes(
            message=msg.arg,
            roomid=msg.parametrized_room.roomid,
            author=msg.user.userid,
            date=func.date(),
        )
        session.add(result)
        session.commit()

        try:
            if result.id:
                await msg.reply("Quote salvata.")
                if msg.room is None:
                    await msg.parametrized_room.send_modnote(
                        "QUOTE ADDED", msg.user, msg.arg
                    )
                return
        except ObjectDeletedError:
            pass
        await msg.reply("Quote già esistente.")


@command_wrapper(aliases=("q", "randomquote"), parametrize_room=True)
async def randquote(msg: Message) -> None:
    db = Database.open()
    with db.get_session() as session:
        query_ = session.query(d.Quotes).filter_by(roomid=msg.parametrized_room.roomid)
        if msg.arg:
            # LIKE wildcards are supported and "*" is considered an alias for "%".
            keyword = msg.arg.replace("*", "%")
            query_ = query_.filter(d.Quotes.message.ilike(f"%{keyword}%"))

        quote_row = query_.order_by(func.random()).first()
        if not quote_row:
            await msg.reply("Nessuna quote trovata.")
            return
        await msg.reply_htmlbox(to_html_quotebox(quote_row.message))


@command_wrapper(aliases=("deletequote", "delquote", "rmquote"), parametrize_room=True)
async def removequote(msg: Message) -> None:
    # Permissions for this command are temporarily lowered to voice level.

    if not msg.arg:
        await msg.reply("Che quote devo cancellare?")
        return

    db = Database.open()
    with db.get_session() as session:
        result = (
            session.query(d.Quotes)
            .filter_by(message=msg.arg, roomid=msg.parametrized_room.roomid)
            .delete()
        )

        if result:
            await msg.reply("Quote cancellata.")
            if msg.room is None:
                await msg.parametrized_room.send_modnote(
                    "QUOTE REMOVED", msg.user, msg.arg
                )
        else:
            await msg.reply("Quote inesistente.")


@command_wrapper(required_rank="driver", parametrize_room=True)
async def removequoteid(msg: Message) -> None:
    room = msg.parametrized_room

    if len(msg.args) != 2:
        return

    db = Database.open()
    with db.get_session() as session:
        quote = (
            session.query(d.Quotes)
            .filter_by(id=msg.args[0], roomid=room.roomid)
            .first()
        )
        if quote:
            await msg.parametrized_room.send_modnote(
                "QUOTE REMOVED", msg.user, quote.message
            )
            session.query(d.Quotes).filter_by(id=quote.id).delete()

    try:
        page = int(msg.args[1])
    except ValueError:
        page = 1

    await msg.user.send_htmlpage("quotelist", room, page)


@command_wrapper(aliases=("quotes", "quoteslist"), parametrize_room=True)
async def quotelist(msg: Message) -> None:
    room = msg.parametrized_room

    db = Database.open()
    with db.get_session() as session:
        quotes_n = session.query(d.Quotes).filter_by(roomid=room.roomid).count()

    if not quotes_n:
        await msg.reply("Nessuna quote da visualizzare.")
        return

    try:
        page = int(msg.arg)
    except ValueError:
        page = 1

    await msg.reply_htmlpage("quotelist", room, page)


@htmlpage_wrapper("quotelist")
def quotelist_htmlpage(user: User, room: Room) -> Query:  # type: ignore[type-arg]
    return (
        Query(d.Quotes)
        .filter_by(roomid=room.roomid)
        .order_by(d.Quotes.date.desc(), d.Quotes.id.desc())
    )

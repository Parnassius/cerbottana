from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select, update
from sqlalchemy.sql import Select

import cerbottana.databases.database as d
from cerbottana import utils
from cerbottana.database import Database

from . import command_wrapper, htmlpage_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message
    from cerbottana.models.room import Room
    from cerbottana.models.user import User


@command_wrapper(aliases=("profilo",), helpstr="Visualizza il tuo profilo.")
async def profile(msg: Message) -> None:
    userid = utils.to_user_id(msg.arg.strip())
    if userid == "":
        userid = msg.user.userid

    db = Database.open()
    with db.get_session() as session:
        stmt = select(d.Users).filter_by(userid=userid)
        # TODO: remove annotation
        userdata: d.Users = session.scalar(stmt)

        if userdata and userdata.userid and userdata.avatar:
            stmt = (
                select(d.Badges).filter_by(userid=userdata.userid).order_by(d.Badges.id)
            )
            badges: list[d.Badges] = session.execute(stmt).scalars().all()

            if userdata.avatar[0] == "#":
                avatar_dir = "trainers-custom"
                avatar_name = userdata.avatar[1:]
            else:
                avatar_dir = "trainers"
                avatar_name = userdata.avatar

            html = utils.render_template(
                "commands/profile.html",
                avatar_dir=avatar_dir,
                avatar_name=avatar_name,
                username=userdata.username,
                badges=badges,
                description=userdata.description,
                pokemon_icon=userdata.icon,
            )

            await msg.reply_htmlbox(html)


@command_wrapper(
    aliases=("setprofilo",), helpstr="Imposta una tua frase personalizzata."
)
async def setprofile(msg: Message) -> None:
    if not msg.arg:
        await msg.reply("Specifica una frase da inserire nel tuo profilo")
        return

    if len(msg.arg) > 250:
        await msg.reply("Errore: lunghezza massima 250 caratteri")
        return

    # authorized: True if msg.user can approve new descriptions.
    authorized = msg.user.has_role("driver", msg.conn.main_room)

    db = Database.open()
    with db.get_session() as session:
        userid = msg.user.userid
        session.add(d.Users(userid=userid))
        stmt = update(d.Users).filter_by(userid=userid)
        if authorized:
            # Authorized users skip the validation process.
            stmt = stmt.values(description=msg.arg, description_pending="")
        else:
            stmt = stmt.values(description_pending=msg.arg)
        session.execute(stmt)

    await msg.reply("Salvato")

    if not authorized:
        username = utils.html_escape(msg.user.username)
        botname = msg.conn.username
        cmd = f"{msg.conn.command_character}pendingdescriptions"
        message = (
            f"{username} ha aggiornato la sua frase del profilo.<br>"
            f'Usa <button name="send" value="/pm {botname}, {cmd}">{cmd}</button> '
            "per approvarla o rifiutarla"
        )
        await msg.conn.main_room.send_rankhtmlbox("%", message)


@command_wrapper(
    aliases=("clearprofilo", "resetprofile", "resetprofilo"),
    helpstr="Rimuovi la frase personalizzata dal profilo.",
)
async def clearprofile(msg: Message) -> None:
    db = Database.open()
    with db.get_session() as session:
        userid = msg.user.userid
        session.add(d.Users(userid=userid))
        stmt = (
            update(d.Users)
            .filter_by(userid=userid)
            .values(description="", description_pending="")
        )
        session.execute(stmt)

    await msg.reply("Frase rimossa")


@command_wrapper(required_rank="driver", main_room_only=True)
async def approvaprofilo(msg: Message) -> None:
    db = Database.open()

    with db.get_session() as session:
        parts = msg.arg.split(",")
        stmt = (
            update(d.Users)
            .filter_by(id=parts[0], description_pending=",".join(parts[1:]))
            .values(description=d.Users.description_pending, description_pending="")
        )
        session.execute(stmt)

    await msg.user.send_htmlpage("pendingdescriptions", msg.conn.main_room)


@command_wrapper(required_rank="driver", main_room_only=True)
async def rifiutaprofilo(msg: Message) -> None:
    db = Database.open()

    with db.get_session() as session:
        parts = msg.arg.split(",")
        stmt = (
            update(d.Users)
            .filter_by(id=parts[0], description_pending=",".join(parts[1:]))
            .values(description_pending="")
        )
        session.execute(stmt)

    await msg.user.send_htmlpage("pendingdescriptions", msg.conn.main_room)


@htmlpage_wrapper("pendingdescriptions", required_rank="driver", main_room_only=True)
def pendingdescriptions_htmlpage(user: User, room: Room) -> Select:
    # TODO: remove annotation
    stmt: Select = (
        select(d.Users)
        .where(d.Users.description_pending != "")
        .order_by(d.Users.userid)
    )
    return stmt

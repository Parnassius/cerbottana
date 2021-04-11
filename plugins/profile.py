from __future__ import annotations

from typing import TYPE_CHECKING

from flask import render_template, request
from sqlalchemy import delete, select, update
from sqlalchemy.sql import Select

import databases.database as d
import utils
from database import Database
from plugins import command_wrapper, htmlpage_wrapper, route_wrapper

if TYPE_CHECKING:
    from models.message import Message
    from models.room import Room
    from models.user import User


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


@command_wrapper(aliases=("badges",), required_rank="driver", main_room_only=True)
async def badge(msg: Message) -> None:
    admin_rank = msg.user.rank(msg.conn.main_room)

    rooms: dict[str, str] = {}

    for room in msg.user.rooms:
        rooms[room.roomid] = msg.user.rank(room) or " "

    token_id = utils.create_token(rooms, 1, admin_rank)
    userid = utils.to_user_id(msg.arg or msg.user.userid)

    await msg.user.send(f"{msg.conn.domain}badges/{userid}?token={token_id}")


@route_wrapper("/badges/<userid>", methods=("GET", "POST"), required_rank="driver")
def badges_route(userid: str) -> str:
    db = Database.open()

    with db.get_session() as session:
        userid = utils.to_user_id(userid)

        if request.method == "POST":

            if "labelnew" in request.form:
                row_image = request.form.get("imagenew")
                row_label = request.form.get("labelnew", "")
                if row_image:
                    session.add(
                        d.Badges(userid=userid, image=row_image, label=row_label)
                    )

                for i in request.form:
                    if i[:5] != "label" or i == "labelnew":
                        continue
                    row_id = i[5:]
                    row_image = request.form.get(f"image{row_id}")
                    row_label = request.form.get(f"label{row_id}", "")
                    row_delete = request.form.get(f"delete{row_id}")
                    if row_delete:
                        stmt_del = delete(d.Badges).filter_by(id=row_id)
                        session.execute(stmt_del)
                    elif row_image:
                        stmt_img = (
                            update(d.Badges)
                            .filter_by(id=row_id)
                            .values(image=row_image, label=row_label)
                        )
                        session.execute(stmt_img)

        stmt = select(d.Users).filter_by(userid=userid)
        # TODO: remove annotation
        user: d.Users = session.scalar(stmt)

        stmt = select(d.Badges).filter_by(userid=userid).order_by(d.Badges.id)
        # TODO: remove annotation
        badges: list[d.Badges] = session.execute(stmt).scalars().all()

        return render_template("badges.html", user=user, badges=badges)


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

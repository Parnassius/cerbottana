from __future__ import annotations

from typing import TYPE_CHECKING

from flask import render_template, request

import databases.database as d
import utils
from database import Database
from plugins import command_wrapper, route_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(aliases=("profilo",), helpstr="Visualizza il tuo profilo.")
async def profile(msg: Message) -> None:
    userid = utils.to_user_id(msg.arg.strip())
    if userid == "":
        userid = msg.user.userid

    db = Database.open()
    with db.get_session() as session:

        userdata = session.query(d.Users).filter_by(userid=userid).first()

        if userdata and userdata.userid and userdata.avatar:
            badges = (
                session.query(d.Badges)
                .filter_by(userid=userdata.userid)
                .order_by(d.Badges.id)
                .all()
            )

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

    if len(msg.arg) > 200:
        await msg.reply("Errore: lunghezza massima 200 caratteri")
        return

    # authorized: True if msg.user can approve new descriptions.
    authorized = msg.conn.main_room is not None and msg.user.has_role(
        "driver", msg.conn.main_room
    )

    db = Database.open()
    with db.get_session() as session:
        userid = msg.user.userid
        session.add(d.Users(userid=userid))
        query_ = session.query(d.Users).filter_by(userid=userid)
        if authorized:
            # Authorized users skip the validation process.
            query_.update({"description": msg.arg, "description_pending": ""})
        else:
            query_.update({"description_pending": msg.arg})

    await msg.reply("Salvato")

    if msg.conn.main_room is not None and not authorized:
        message = "Qualcuno ha aggiornato la sua frase del profilo. "
        message += (
            'Usa <button name="send" value="/pm '
            + msg.conn.username
            + ', .dashboard">.dashboard</button> per approvarla o rifiutarla'
        )
        await msg.conn.main_room.send_rankhtmlbox("%", message)


@route_wrapper("/profile", methods=("GET", "POST"), require_driver=True)
def profile_route() -> str:
    db = Database.open()

    with db.get_session() as session:
        userid = utils.to_user_id(request.args.get("userid", ""))

        if request.method == "POST":

            if "description" in request.form:
                session.query(d.Users).filter_by(
                    id=request.form.get("id"), userid=userid
                ).update({"description": request.form.get("description")})

            if "labelnew" in request.form:
                image = request.form.get("imagenew")
                label = request.form.get("labelnew", "")
                if image:
                    session.add(d.Badges(userid=userid, image=image, label=label))

                for i in request.form:
                    if i[:5] != "label" or i == "labelnew":
                        continue
                    row_id = i[5:]
                    image = request.form.get(f"image{row_id}")
                    label = request.form.get(f"label{row_id}", "")
                    if image:
                        session.query(d.Badges).filter_by(id=row_id).update(
                            {"image": image, "label": label}
                        )

        user = session.query(d.Users).filter_by(userid=userid).first()

        badges = (
            session.query(d.Badges).filter_by(userid=userid).order_by(d.Badges.id).all()
        )

        return render_template("profile.html", user=user, badges=badges)

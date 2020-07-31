from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from flask import g, render_template, request

import databases.database as d
import utils
from database import Database
from plugins import command_wrapper, route_wrapper

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper(aliases=["profilo"], helpstr="Visualizza il tuo profilo.")
async def profile(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    # pylint: disable=too-many-locals
    if arg.strip() == "":
        arg = user

    arg = utils.to_user_id(arg)

    db = Database.open()
    with db.get_session() as session:

        userdata = session.query(d.Users).filter_by(userid=arg).first()

        if userdata:
            user_badges = (
                session.query(d.Badges)
                .filter_by(userid=userdata.userid)
                .order_by(d.Badges.id)
                .all()
            )

            html = "<div>"
            html += (
                '  <div style="display: table-cell; width: 80px; vertical-align: top">'
            )
            html += '    <img src="https://play.pokemonshowdown.com/sprites/{avatar_dir}/{avatar_name}.png"'
            html += '    width="80" height="80">'
            html += "  </div>"
            html += (
                '  <div style="display: table-cell; width: 100%; vertical-align: top">'
            )
            html += '    <b style="color: {name_color}">{username}</b><br>{badges}'
            if userdata.description and userdata.description.strip() != "":
                html += '  <hr style="margin: 4px 0">'
                html += '  <div style="text-align: justify">{description}</div>'
            html += "  </div>"
            html += "</div>"

            if userdata.avatar[0] == "#":
                avatar_dir = "trainers-custom"
                avatar_name = userdata.avatar[1:]
            else:
                avatar_dir = "trainers"
                avatar_name = userdata.avatar

            username = userdata.username

            name_color = utils.username_color(utils.to_user_id(username))

            badges = ""
            badge = '<img src="{image}" width="13" height="13" title="{title}"'
            badge += (
                ' style="border: 1px solid; border-radius: 2px; margin: 2px 1px 0 0">'
            )
            for i in user_badges:
                print(i)
                badges += badge.format(image=i.image, title=utils.html_escape(i.label))

            description = utils.html_escape(userdata.description)

            await conn.send_htmlbox(
                room,
                user,
                html.format(
                    avatar_dir=avatar_dir,
                    avatar_name=avatar_name,
                    name_color=name_color,
                    username=username,
                    badges=badges,
                    description=description,
                ),
            )


@command_wrapper(
    aliases=["setprofilo"], helpstr="Imposta una tua frase personalizzata."
)
async def setprofile(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    if len(arg) > 200:
        await conn.send_reply(room, user, "Errore: lunghezza massima 200 caratteri")
        return

    userid = utils.to_user_id(user)

    db = Database.open()
    with db.get_session() as session:
        session.add(d.Users(userid=userid))
        session.query(d.Users).filter_by(userid=userid).update(
            {"description_pending": arg}
        )

    await conn.send_reply(room, user, "Salvato")

    message = "Qualcuno ha aggiornato la sua frase del profilo. "
    message += (
        'Usa <button name="send" value="/pm '
        + conn.username
        + ', .dashboard">.dashboard</button> per approvarla o rifiutarla'
    )
    for r in conn.rooms:
        await conn.send_rankhtmlbox("%", r, message)


@route_wrapper("/profile", methods=("GET", "POST"), require_driver=True)
def profile_route() -> str:

    with g.db.get_session() as session:
        userid = utils.to_user_id(request.args.get("userid", ""))

        if request.method == "POST":

            if "description" in request.form:
                session.query(d.Users).filter_by(
                    id=request.form.get("id"), userid=userid
                ).update({"description": request.form.get("description")})

            if "labelnew" in request.form:
                image = request.form.get("imagenew")
                label = request.form.get("labelnew")
                if label and image:
                    session.add(d.Badges(userid=userid, image=image, label=label))

                for i in request.form:
                    if i[:5] != "label" or i == "labelnew":
                        continue
                    row_id = i[5:]
                    image = request.form.get(f"image{row_id}")
                    label = request.form.get(f"label{row_id}")
                    if label and image:
                        session.query(d.Badges).filter_by(id=row_id).update(
                            {"image": image, "label": label}
                        )

        user = session.query(d.Users).filter_by(userid=userid).first()

        badges = (
            session.query(d.Badges).filter_by(userid=userid).order_by(d.Badges.id).all()
        )

        return render_template("profile.html", user=user, badges=badges)

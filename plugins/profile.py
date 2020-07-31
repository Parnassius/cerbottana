from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from flask import g, render_template, request

import utils
from database import Database
from plugins import command_wrapper, route_wrapper
from tasks import init_task_wrapper

if TYPE_CHECKING:
    from connection import Connection


@init_task_wrapper()
async def create_table(conn: Connection) -> None:  # lgtm [py/similar-function]
    db = Database()

    sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'badges'"
    if not db.execute(sql).fetchone():
        sql = """CREATE TABLE badges (
            id INTEGER,
            userid TEXT,
            image TEXT,
            label TEXT,
            PRIMARY KEY(id)
        )"""
        db.execute(sql)

        sql = """CREATE INDEX idx_badges_userid
        ON badges (
            userid
        )"""
        db.execute(sql)

        sql = "INSERT INTO metadata (key, value) VALUES ('table_version_badges', '1')"
        db.execute(sql)

        db.commit()


@command_wrapper(aliases=["profilo"], helpstr="Visualizza il tuo profilo.")
async def profile(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    # pylint: disable=too-many-locals
    if arg.strip() == "":
        arg = user

    arg = utils.to_user_id(arg)

    db = Database()
    sql = "SELECT * FROM users WHERE userid = ?"
    body = db.execute(sql, [arg]).fetchone()

    if body:
        body = dict(body)

        sql = "SELECT image, label "
        sql += " FROM badges "
        sql += " WHERE userid = ? ORDER BY id"
        body["badges"] = db.execute(sql, [body["userid"]]).fetchall()

        html = "<div>"
        html += '  <div style="display: table-cell; width: 80px; vertical-align: top">'
        html += '    <img src="https://play.pokemonshowdown.com/sprites/{avatar_dir}/{avatar_name}.png"'
        html += '    width="80" height="80">'
        html += "  </div>"
        html += '  <div style="display: table-cell; width: 100%; vertical-align: top">'
        html += '    <b style="color: {name_color}">{username}</b><br>{badges}'
        if body["description"] and body["description"].strip() != "":
            html += '  <hr style="margin: 4px 0">'
            html += '  <div style="text-align: justify">{description}</div>'
        html += "  </div>"
        html += "</div>"

        if body["avatar"][0] == "#":
            avatar_dir = "trainers-custom"
            avatar_name = body["avatar"][1:]
        else:
            avatar_dir = "trainers"
            avatar_name = body["avatar"]

        username = body["username"]

        name_color = utils.username_color(utils.to_user_id(username))

        badges = ""
        badge = '<img src="{image}" width="13" height="13" title="{title}"'
        badge += ' style="border: 1px solid; border-radius: 2px; margin: 2px 1px 0 0">'
        for i in body["badges"]:
            badges += badge.format(
                image=i["image"], title=utils.html_escape(i["label"])
            )

        description = utils.html_escape(body["description"])

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

    db = Database()
    sql = "INSERT INTO users (userid, description_pending) VALUES (?, ?) "
    sql += " ON CONFLICT (userid) DO UPDATE SET description_pending = excluded.description_pending"
    db.executenow(sql, [utils.to_user_id(user), arg])

    await conn.send_reply(room, user, "Salvato")

    message = "Qualcuno ha aggiornato la sua frase del profilo. "
    message += (
        'Usa <button name="send" value="/pm '
        + conn.username
        + ', .dashboard">.dashboard</button> per approvarla o rifiutarla'
    )
    for room in conn.rooms:
        await conn.send_rankhtmlbox("%", room, message)


@route_wrapper("/profile", methods=("GET", "POST"), require_driver=True)
def profile_route() -> str:

    userid = utils.to_user_id(request.args.get("userid", ""))

    if request.method == "POST":

        if "description" in request.form:
            sql = "UPDATE users SET description = ? WHERE id = ? AND userid = ?"
            g.db.executenow(
                sql, [request.form["description"], request.form["id"], userid]
            )

        if "labelnew" in request.form:
            image = request.form.get("imagenew")
            label = request.form.get("labelnew")
            if label and image:
                sql = "INSERT INTO badges (userid, image, label) VALUES (?, ?, ?)"
                g.db.execute(sql, [userid, image, label])

            for i in request.form:
                if i[:5] != "label" or i == "labelnew":
                    continue
                row_id = i[5:]
                image = request.form.get(f"image{row_id}")
                label = request.form.get(f"label{row_id}")
                if label and image:
                    sql = "UPDATE badges SET image = ?, label = ? WHERE id = ?"
                    g.db.execute(sql, [image, label, row_id])
            g.db.commit()

    sql = "SELECT * FROM users WHERE userid = ?"
    user = g.db.execute(sql, [userid]).fetchone()

    sql = "SELECT * FROM badges WHERE userid = ? ORDER BY id"
    badges = g.db.execute(sql, [userid]).fetchall()

    return render_template("profile.html", user=user, badges=badges)

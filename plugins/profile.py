from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from connection import Connection

from database import Database

from inittasks import inittask_wrapper
from plugin_loader import plugin_wrapper
import utils


@inittask_wrapper()
async def create_table(conn: Connection) -> None:
    db = Database()

    sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'utenti'"
    if not db.execute(sql).fetchone():
        sql = """CREATE TABLE utenti (
            id INTEGER,
            userid TEXT,
            nome TEXT,
            avatar TEXT,
            descrizione TEXT,
            descrizione_daapprovare TEXT,
            PRIMARY KEY(id)
        )"""
        db.execute(sql)

        sql = """CREATE UNIQUE INDEX idx_unique_utenti_userid
        ON utenti (
            userid
        )"""
        db.execute(sql)

        sql = """CREATE INDEX idx_utenti_descrizione_daapprovare
        ON utenti (
            descrizione_daapprovare
        )"""
        db.execute(sql)

        db.commit()

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


@plugin_wrapper(aliases=["profilo"], helpstr="Visualizza il tuo profilo.")
async def profile(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    # pylint: disable=too-many-locals
    if arg.strip() == "":
        arg = user

    arg = utils.to_user_id(arg)

    db = Database()
    sql = "SELECT * FROM utenti WHERE userid = ?"
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
        html += '    <b style="color: {name_color}">{nome}</b><br>{badges}'
        if body["descrizione"].strip() != "":
            html += '  <hr style="margin: 4px 0">'
            html += '  <div style="text-align: justify">{descrizione}</div>'
        html += "  </div>"
        html += "</div>"

        if body["avatar"][0] == "#":
            avatar_dir = "trainers-custom"
            avatar_name = body["avatar"][1:]
        else:
            avatar_dir = "trainers"
            avatar_name = body["avatar"]

        nome = body["nome"]

        name_color = utils.username_color(utils.to_user_id(nome))

        badges = ""
        badge = '<img src="{image}" width="12" height="12" title="{title}"'
        badge += ' style="border: 1px solid; border-radius: 2px; margin: 2px 1px 0 0">'
        for i in body["badges"]:
            badges += badge.format(
                image=i["image"], title=utils.html_escape(i["label"])
            )

        descrizione = body["descrizione"].replace("<", "&lt;")

        await conn.send_htmlbox(
            room,
            user,
            html.format(
                avatar_dir=avatar_dir,
                avatar_name=avatar_name,
                name_color=name_color,
                nome=nome,
                badges=badges,
                descrizione=descrizione,
            ),
        )


@plugin_wrapper(aliases=["setprofilo"], helpstr="Imposta una tua frase personalizzata.")
async def setprofile(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    if len(arg) > 200:
        await conn.send_reply(room, user, "Errore: lunghezza massima 200 caratteri")
        return

    db = Database()
    sql = "INSERT INTO utenti (userid, descrizione_daapprovare) VALUES (?, ?) "
    sql += " ON CONFLICT (userid) DO UPDATE SET descrizione_daapprovare = excluded.descrizione_daapprovare"
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

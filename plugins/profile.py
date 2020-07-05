from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from connection import Connection

import database

from plugin_loader import plugin_wrapper
import utils


"""
CREATE TABLE utenti (
    id INTEGER,
    userid TEXT,
    nome TEXT,
    avatar TEXT,
    descrizione TEXT,
    descrizione_daapprovare TEXT,
    PRIMARY KEY(id),
);

CREATE UNIQUE INDEX idx_unique_utenti_userid
ON utenti (
    userid
);

CREATE INDEX idx_utenti_descrizione_daapprovare
ON utenti (
    descrizione_daapprovare
);
"""


@plugin_wrapper(aliases=["profilo"], helpstr="Visualizza il tuo profilo.")
async def profile(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    # pylint: disable=too-many-locals
    if arg.strip() == "":
        arg = user

    arg = utils.to_user_id(arg)

    db = database.open_db()
    sql = "SELECT * FROM utenti WHERE userid = ?"
    body = db.execute(sql, [arg]).fetchone()

    if body:
        body = dict(body)

        sql = "SELECT immagine, sfondo, label "
        sql += " FROM altre_badge "
        sql += " WHERE utente = ? ORDER BY id"
        body["altrebadge"] = db.execute(sql, [body["id"]]).fetchall()

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
        badge = '<img src="{immagine}" width="12" height="12" title="{title}"'
        badge += ' style="border: 1px solid; border-radius: 2px; margin: 2px 1px 0 0;'
        badge += ' background: {sfondo}{opacity}">'
        for i in body["altrebadge"]:
            badges += badge.format(
                immagine=i["immagine"],
                title=utils.html_escape(i["label"]),
                sfondo=utils.html_escape(i["sfondo"]),
                opacity="",
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

    db.connection.close()


@plugin_wrapper(aliases=["setprofilo"], helpstr="Imposta una tua frase personalizzata.")
async def setprofile(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    if len(arg) > 200:
        await conn.send_reply(room, user, "Errore: lunghezza massima 200 caratteri")
        return

    db = database.open_db()
    sql = "INSERT INTO utenti (userid, descrizione_daapprovare) VALUES (?, ?) "
    sql += " ON CONFLICT (userid) DO UPDATE SET descrizione_daapprovare = excluded.descrizione_daapprovare"
    db.execute(sql, [utils.to_user_id(user), arg])
    db.connection.commit()
    db.connection.close()

    await conn.send_reply(room, user, "Salvato")

    message = "Qualcuno ha aggiornato la sua frase del profilo. "
    message += (
        'Usa <button name="send" value="/pm '
        + conn.username
        + ', .dashboard">.dashboard</button> per approvarla o rifiutarla'
    )
    for room in conn.rooms:
        await conn.send_rankhtmlbox("%", room, message)

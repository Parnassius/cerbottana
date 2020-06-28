import database

from plugin_loader import plugin_wrapper
import utils


@plugin_wrapper(aliases=["profilo"], helpstr="Visualizza il tuo profilo.")
async def profile(
    self, room: str, user: str, arg: str, from_elitefour: bool = False
) -> None:
    # pylint: disable=too-many-locals
    if arg.strip() == "":
        arg = user

    simple_message = ""
    if from_elitefour:
        simple_message = arg

    arg = utils.to_user_id(arg)

    db = database.open_db()
    sql = "SELECT * FROM utenti WHERE userid = ?"
    body = db.execute(sql, [arg]).fetchone()

    if body:
        body = dict(body)

        sql = "SELECT t.descrizione AS tier, t.immagine, t.sfondo, e.data, "
        sql += " (SELECT data FROM elitefour "
        sql += " WHERE tier = e.tier AND data >= e.data AND (CASE WHEN data = e.data THEN id > e.id ELSE TRUE END) "
        sql += " ORDER BY data LIMIT 1) AS datafine "
        sql += " FROM elitefour AS e "
        sql += " LEFT JOIN elitefour_tiers AS t ON t.id = e.tier "
        sql += " WHERE e.utente = ? ORDER BY e.data DESC LIMIT 10"
        body["elitefour"] = db.execute(sql, [body["id"]]).fetchall()

        sql = "SELECT s.descrizione AS seasonal, v.anno, s.immagine, s.sfondo "
        sql += " FROM seasonal_vincitori AS v "
        sql += " LEFT JOIN seasonals AS s ON s.id = v.seasonal "
        sql += " WHERE v.utente = ? ORDER BY v.anno DESC, s.ordine DESC"
        body["seasonal"] = db.execute(sql, [body["id"]]).fetchall()

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
        title = "Vincitore {seasonal} {anno}"
        for i in body["seasonal"]:
            badges += badge.format(
                immagine=i["immagine"],
                title=title.format(seasonal=i["seasonal"], anno=i["anno"]),
                sfondo=i["sfondo"],
                opacity="",
            )
        for i in body["altrebadge"]:
            badges += badge.format(
                immagine=i["immagine"],
                title=utils.html_escape(i["label"]),
                sfondo=utils.html_escape(i["sfondo"]),
                opacity="",
            )
        title = "{tier}:{dal}{al}"
        for i in body["elitefour"]:
            opacity = ""
            if i["datafine"] is not None:
                opacity = "; opacity: .5"
            dal = " dal {}".format(utils.date_format(i["data"]))
            al = ""
            if i["datafine"] is not None:
                al = " al {}".format(utils.date_format(i["datafine"]))
            badges += badge.format(
                immagine=i["immagine"],
                title=title.format(tier=i["tier"], dal=dal, al=al),
                sfondo=i["sfondo"],
                opacity=opacity,
            )

        descrizione = body["descrizione"].replace("<", "&lt;")

        await self.send_htmlbox(
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
            simple_message,
        )

    db.connection.close()


@plugin_wrapper(aliases=["setprofilo"], helpstr="Imposta una tua frase personalizzata.")
async def setprofile(self, room: str, user: str, arg: str) -> None:
    if len(arg) > 200:
        await self.send_reply(room, user, "Errore: lunghezza massima 200 caratteri")
        return

    db = database.open_db()
    sql = "INSERT INTO utenti (userid, descrizione_daapprovare) VALUES (?, ?) "
    sql += " ON CONFLICT (userid) DO UPDATE SET descrizione_daapprovare = excluded.descrizione_daapprovare"
    db.execute(sql, [utils.to_user_id(user), arg])
    db.connection.commit()
    db.connection.close()

    await self.send_reply(room, user, "Salvato")

    message = "Qualcuno ha aggiornato la sua frase del profilo. "
    message += (
        'Usa <button name="send" value="/pm '
        + self.username
        + ', .dashboard">.dashboard</button> per approvarla o rifiutarla'
    )
    for room in self.rooms:
        await self.send_rankhtmlbox("%", room, message)

import os
from datetime import date

from flask import Flask, render_template, session, abort, request, g
from waitress import serve

import database
import utils


class Server(Flask):
    def serve_forever(self):
        serve(self, listen="*:{}".format(os.environ["PORT"]))


SERVER = Server(__name__)

SERVER.secret_key = os.environ["FLASK_SECRET_KEY"]


@SERVER.template_filter("format_date")
def format_date(value: str) -> str:
    return date.fromisoformat(value).strftime("%d/%m/%Y")


@SERVER.before_request
def before():
    g.db = database.open_db()

    token = request.args.get("token")

    if token is not None:
        sql = "SELECT rank, julianday('now'), julianday(scadenza) FROM tokens WHERE token = ? AND JULIANDAY('NOW') - JULIANDAY(scadenza) < 0"
        rank = g.db.execute(sql, [token]).fetchone()
        if rank:
            session["user"] = rank["rank"]

    user = session.get("user")

    if "user" not in session:
        abort(401)


@SERVER.after_request
def after(res):
    db = g.pop("db", None)

    if db is not None:
        db.connection.close()
    return res


@SERVER.route("/", methods=("GET", "POST"))
def dashboard():

    if request.method == "POST":

        if "approva" in request.form:
            parts = request.form["approva"].split(",")
            sql = "UPDATE utenti SET descrizione = descrizione_daapprovare, descrizione_daapprovare = '' "
            sql += " WHERE id = ? AND descrizione_daapprovare = ?"
            g.db.execute(sql, [parts[0], ",".join(parts[1:])])

        if "rifiuta" in request.form:
            parts = request.form["rifiuta"].split(",")
            sql = "UPDATE utenti SET descrizione_daapprovare = '' "
            sql += " WHERE id = ? AND descrizione_daapprovare = ?"
            g.db.execute(sql, [parts[0], ",".join(parts[1:])])

        g.db.connection.commit()

    sql = "SELECT * FROM utenti WHERE descrizione_daapprovare != '' ORDER BY userid"
    descrizioni_daapprovare = g.db.execute(sql).fetchall()

    sql = "SELECT *, "
    sql += " (SELECT (SELECT nome FROM utenti WHERE id = e.utente) FROM elitefour AS e WHERE tier = t.id ORDER BY data DESC LIMIT 1) AS utente "
    sql += " FROM elitefour_tiers AS t ORDER BY ordine"
    elitefour_tiers = g.db.execute(sql).fetchall()

    sql = "SELECT id, descrizione FROM seasonals WHERE (',' || mesi || ',') LIKE ('%,' || STRFTIME('%m', DATE()) || ',%')"
    seasonal = g.db.execute(sql).fetchall()

    return render_template(
        "dashboard.html",
        descrizioni_daapprovare=descrizioni_daapprovare,
        elitefour_tiers=elitefour_tiers,
        seasonal=seasonal,
    )


@SERVER.route("/profilo", methods=("GET", "POST"))
def profilo():

    userid = utils.to_user_id(request.args.get("userid", ""))

    if request.method == "POST":

        print(request.form)

        if "descrizione" in request.form:
            sql = "UPDATE utenti SET descrizione = ? WHERE id = ? AND userid = ?"
            g.db.execute(sql, [request.form["descrizione"], request.form["id"], userid])

        if "tier" in request.form and "data" in request.form:
            sql = "INSERT INTO elitefour (utente, tier, data) VALUES (?, ?, ?)"
            g.db.execute(
                sql, [request.form["id"], request.form["tier"], request.form["data"]]
            )

        if "seasonal" in request.form:
            sql = "INSERT INTO seasonal_vincitori (seasonal, anno, utente) VALUES (?, STRFTIME('%Y', DATE()), ?)"
            g.db.execute(sql, [request.form["seasonal"], request.form["id"]])

        g.db.connection.commit()

    sql = "SELECT * FROM utenti WHERE userid = ?"
    utente = g.db.execute(sql, [utils.to_user_id(userid)]).fetchone()

    sql = "SELECT *, "
    sql += " (SELECT (SELECT userid FROM utenti WHERE id = e.utente) FROM elitefour AS e WHERE tier = t.id ORDER BY data DESC LIMIT 1) AS userid "
    sql += " FROM elitefour_tiers AS t ORDER BY ordine"
    elitefour_tiers = g.db.execute(sql).fetchall()

    sql = "SELECT *, "
    sql += " (SELECT id FROM seasonal_vincitori WHERE seasonal = s.id AND anno = STRFTIME('%Y', DATE())) AS disabled "
    sql += " FROM seasonals AS s ORDER BY ordine"
    seasonals = g.db.execute(sql).fetchall()

    return render_template(
        "profilo.html",
        utente=utente,
        elitefour_tiers=elitefour_tiers,
        seasonals=seasonals,
        today=date.today(),
    )


@SERVER.route("/elitefour")
def elitefour():

    tier = request.args.get("tier")

    sql = "SELECT u.nome, e.data "
    sql += " FROM elitefour AS e "
    sql += " LEFT JOIN utenti AS u ON u.id = e.utente "
    sql += " WHERE e.tier = :tier "
    sql += " ORDER BY e.data DESC"
    rs = g.db.execute(sql, [tier]).fetchall()

    return render_template("elitefour.html", rs=rs)


@SERVER.route("/eightball", methods=("GET", "POST"))
def eightball():

    if request.method == "POST":

        if "risposte" in request.form:
            sql = "DELETE FROM eight_ball"
            g.db.execute(sql)

            risposte = list(
                filter(
                    None,
                    map(
                        str.strip, sorted(request.form["risposte"].strip().splitlines())
                    ),
                )
            )
            sql = "INSERT INTO eight_ball (risposta) VALUES " + ", ".join(
                ["(?)"] * len(risposte)
            )
            g.db.execute(sql, risposte)

        g.db.connection.commit()

    sql = "SELECT * FROM eight_ball ORDER BY risposta"
    rs = g.db.execute(sql).fetchall()

    return render_template("eightball.html", rs=rs)

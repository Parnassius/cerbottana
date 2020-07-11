from datetime import date
from functools import wraps
from typing import Callable

from environs import Env
from flask import Flask, render_template, session, abort, request, g
from waitress import serve

from database import Database
import utils


env = Env()
env.read_env()


class Server(Flask):
    def serve_forever(self) -> None:
        serve(self, listen="*:{}".format(env("PORT")))


SERVER = Server(__name__)

SERVER.secret_key = env("FLASK_SECRET_KEY")


@SERVER.template_filter("format_date")
def format_date(value: str) -> str:
    return date.fromisoformat(value).strftime("%d/%m/%Y")


@SERVER.before_request
def before() -> None:
    g.db = Database()

    token = request.args.get("token")

    if token is not None:
        sql = "SELECT rank, prooms FROM tokens WHERE token = ? AND JULIANDAY() - JULIANDAY(scadenza) < 0"
        data = g.db.execute(sql, [token]).fetchone()
        if not data:  # invalid token
            abort(401)
        session.update(data)


def require_driver(func: Callable[[], str]) -> Callable[[], str]:
    @wraps(func)
    def wrapper() -> str:
        if "rank" not in session or not utils.is_driver(session["rank"]):
            abort(401)
        return func()

    return wrapper


@SERVER.route("/", methods=("GET", "POST"))
@require_driver
def dashboard() -> str:

    if request.method == "POST":

        if "approva" in request.form:
            parts = request.form["approva"].split(",")
            sql = "UPDATE utenti SET descrizione = descrizione_daapprovare, descrizione_daapprovare = '' "
            sql += " WHERE id = ? AND descrizione_daapprovare = ?"
            g.db.executenow(sql, [parts[0], ",".join(parts[1:])])

        if "rifiuta" in request.form:
            parts = request.form["rifiuta"].split(",")
            sql = "UPDATE utenti SET descrizione_daapprovare = '' "
            sql += " WHERE id = ? AND descrizione_daapprovare = ?"
            g.db.executenow(sql, [parts[0], ",".join(parts[1:])])

    sql = "SELECT * FROM utenti WHERE descrizione_daapprovare != '' ORDER BY userid"
    descrizioni_daapprovare = g.db.execute(sql).fetchall()

    return render_template(
        "dashboard.html", descrizioni_daapprovare=descrizioni_daapprovare
    )


@SERVER.route("/profilo", methods=("GET", "POST"))
@require_driver
def profilo() -> str:

    userid = utils.to_user_id(request.args.get("userid", ""))

    if request.method == "POST":

        if "descrizione" in request.form:
            sql = "UPDATE utenti SET descrizione = ? WHERE id = ? AND userid = ?"
            g.db.executenow(
                sql, [request.form["descrizione"], request.form["id"], userid]
            )

    sql = "SELECT * FROM utenti WHERE userid = ?"
    utente = g.db.execute(sql, [utils.to_user_id(userid)]).fetchone()

    return render_template("profilo.html", utente=utente, today=date.today())


@SERVER.route("/eightball", methods=("GET", "POST"))
@require_driver
def eightball() -> str:

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


@SERVER.route("/quotes/<room>")
def quotes(room: str) -> str:
    if room in env.list("PRIVATE_ROOMS"):
        private_rooms = session.get("prooms")
        if not private_rooms or room not in private_rooms.split(","):
            abort(401)

    sql = "SELECT message, date "
    sql += "FROM quotes WHERE roomid = ?"
    rs = g.db.execute(sql, [room]).fetchall()
    if not rs:
        abort(401)  # no quotes for this room

    return render_template("quotes.html", rs=rs, room=room)

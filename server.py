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
            sql = "UPDATE users SET description = description_pending, description_pending = '' "
            sql += " WHERE id = ? AND description_pending = ?"
            g.db.executenow(sql, [parts[0], ",".join(parts[1:])])

        if "rifiuta" in request.form:
            parts = request.form["rifiuta"].split(",")
            sql = "UPDATE users SET description_pending = '' "
            sql += " WHERE id = ? AND description_pending = ?"
            g.db.executenow(sql, [parts[0], ",".join(parts[1:])])

    sql = "SELECT * FROM users WHERE description_pending != '' ORDER BY userid"
    descriptions_pending = g.db.execute(sql).fetchall()

    return render_template(
        "dashboard.html", descriptions_pending=descriptions_pending
    )


@SERVER.route("/profilo", methods=("GET", "POST"))
@require_driver
def profilo() -> str:

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
    utente = g.db.execute(sql, [userid]).fetchone()

    sql = "SELECT * FROM badges WHERE userid = ? ORDER BY id"
    badges = g.db.execute(sql, [userid]).fetchall()

    return render_template("profilo.html", utente=utente, badges=badges)


@SERVER.route("/eightball", methods=("GET", "POST"))
@require_driver
def eightball() -> str:

    if request.method == "POST":

        if "answers" in request.form:
            sql = "DELETE FROM eightball"
            g.db.execute(sql)

            answers = list(
                filter(
                    None,
                    map(
                        str.strip, sorted(request.form["answers"].strip().splitlines())
                    ),
                )
            )
            sql = "INSERT INTO eightball (answer) VALUES " + ", ".join(
                ["(?)"] * len(answers)
            )
            g.db.execute(sql, answers)

            g.db.commit()

    sql = "SELECT * FROM eightball ORDER BY answer"
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

from __future__ import annotations

import queue
from datetime import date
from functools import wraps
from typing import Callable, Optional

from environs import Env
from flask import Flask, abort, current_app, g, render_template, request, session
from waitress import serve

import utils
from database import Database
from plugins import routes

env = Env()
env.read_env()


class Server(Flask):
    def __init__(self, *args, **kwargs) -> None:  # type:ignore
        super().__init__(*args, **kwargs)
        self.queue: Optional[queue.SimpleQueue[str]] = None

    def serve_forever(self, queue: queue.SimpleQueue[str]) -> None:
        self.queue = queue
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
        sql = "SELECT room, rank, expiry FROM tokens "
        sql += " WHERE token = ? AND JULIANDAY() - JULIANDAY(expiry) < 0"
        data = g.db.execute(sql, [token]).fetchall()
        if not data:  # invalid token
            abort(401)
        for row in data:
            if row["room"] is None:
                session["_rank"] = row["rank"]
            else:
                session[row["room"]] = row["rank"]


def require_driver(func: Callable[[], str]) -> Callable[[], str]:
    @wraps(func)
    def wrapper() -> str:
        if not utils.is_driver(session.get("_rank")):
            abort(401)
        return func()

    return wrapper


@SERVER.route("/", methods=("GET", "POST"))
@require_driver
def dashboard() -> str:

    current_app.queue.put("aaa", False)

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

    return render_template("dashboard.html", descriptions_pending=descriptions_pending)


for func, rule, methods in routes:
    SERVER.add_url_rule(rule, view_func=func, methods=methods)

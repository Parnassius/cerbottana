from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from flask import Flask, request
from flask import session as web_session
from sqlalchemy import select
from waitress import serve

import databases.database as d
from database import Database
from plugins import routes

if TYPE_CHECKING:
    from connection import Connection


class Server(Flask):
    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        super().__init__(*args, **kwargs)
        self.conn: Connection | None = None

    def serve_forever(self, port: int, conn: Connection) -> None:
        self.conn = conn
        serve(self, listen="*:{}".format(str(port)))


def initialize_server(secret_key: str) -> Server:
    # pylint: disable=unused-variable
    server = Server(__name__)

    server.secret_key = secret_key

    @server.before_request
    def before() -> None:
        token = request.args.get("token")

        if token is not None:
            db = Database.open()
            with db.get_session() as session:
                stmt = (
                    select(d.Tokens)
                    .filter_by(token=token)
                    .where(d.Tokens.expiry > str(datetime.utcnow()))
                )
                # TODO: remove annotation
                row: d.Tokens
                for row in session.execute(stmt).scalars():
                    if row.room is None:
                        web_session["_rank"] = row.rank
                    else:
                        web_session[row.room] = row.rank

    for view_func, rule, methods in routes:
        server.add_url_rule(rule, view_func=view_func, methods=methods)

    return server

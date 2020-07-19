from __future__ import annotations

import asyncio
import datetime
from typing import TYPE_CHECKING

from flask import abort, render_template, request, session
from lxml.html import fromstring

import utils
from database import Database
from handlers import handler_wrapper
from plugins import route_wrapper
from tasks import init_task_wrapper, recurring_task_wrapper

if TYPE_CHECKING:
    from connection import Connection


@init_task_wrapper()
async def create_table(conn: Connection) -> None:
    db = Database("logs")

    sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'metadata'"
    if not db.execute(sql).fetchone():
        sql = """CREATE TABLE metadata (
            id INTEGER,
            key TEXT,
            value TEXT,
            PRIMARY KEY(id)
        )"""
        db.execute(sql)

        sql = """CREATE UNIQUE INDEX idx_unique_metadata_key
        ON metadata (
            key
        )"""
        db.execute(sql)

        sql = "INSERT INTO metadata (key, value) VALUES ('table_version_metadata', '1')"
        db.execute(sql)

        db.commit()

    sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'logs'"
    if not db.execute(sql).fetchone():
        sql = """CREATE TABLE logs (
            id INTEGER,
            roomid TEXT,
            date TEXT,
            time TEXT,
            userrank TEXT,
            userid TEXT,
            message TEXT,
            PRIMARY KEY(id)
        )"""
        db.execute(sql)

        sql = """CREATE INDEX idx_logs_roomid_userid_date
        ON logs (
            roomid,
            userid,
            date
        )"""
        db.execute(sql)

        sql = """CREATE INDEX idx_logs_roomid_userrank_date
        ON logs (
            roomid,
            userrank,
            date
        )"""
        db.execute(sql)

        sql = """CREATE INDEX idx_logs_date
        ON logs (
            date
        )"""
        db.execute(sql)

        sql = "INSERT INTO metadata (key, value) VALUES ('table_version_logs', '1')"
        db.execute(sql)

        db.commit()


@recurring_task_wrapper()
async def logger_task(conn: Connection) -> None:
    while True:
        db = Database("logs")

        yesterday = datetime.date.today() - datetime.timedelta(days=1)

        for room in conn.rooms + conn.private_rooms:
            last_date = db.execute(
                "SELECT MAX(date) AS date FROM logs WHERE roomid = ?", [room]
            ).fetchone()

            if last_date and last_date["date"]:
                date = datetime.date.fromisoformat(
                    last_date["date"]
                ) + datetime.timedelta(days=1)
            else:
                date = yesterday - datetime.timedelta(days=2)

            while date < yesterday:
                await asyncio.sleep(30)
                await conn.send_message(
                    "", f"/join view-chatlog-{room}--{date.isoformat()}", False
                )
                date += datetime.timedelta(days=1)

        del db

        await asyncio.sleep(12 * 60 * 60)


@handler_wrapper(["pagehtml"])
async def logger(conn: Connection, roomid: str, *args: str) -> None:
    if roomid[:13] != "view-chatlog-":
        return

    room, date = roomid[13:].split("--")
    chatlog = "|".join(args).strip()

    html = fromstring(chatlog)

    db = Database("logs")

    db.execute("DELETE FROM logs WHERE date = ? AND roomid = ?", [date, room])

    for el in html.xpath('div[@class="message-log"]/div[@class="chat"]'):
        time = el.xpath("small")
        user = el.xpath("strong")
        message = el.xpath("q")
        if time and user and message:
            userrank = user[0].xpath("small")
            db.execute(
                """INSERT INTO logs (roomid, date, time, userrank, userid, message)
                VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    room,
                    date,
                    time[0].text.strip("[] "),
                    userrank[0].text if len(userrank) else None,
                    utils.to_user_id(user[0].text_content()),
                    message[0].text,
                ],
            )

    db.commit()


@route_wrapper("/linecounts/<room>")
def linecounts_route(room: str) -> str:
    if not utils.is_driver(session.get(room)):
        abort(401)

    return render_template("linecounts.html", room=room)


@route_wrapper("/linecounts/<room>/data")
def linecounts_data(room: str) -> str:
    if not utils.is_driver(session.get(room)):
        abort(401)

    db = Database("logs")

    if request.args.get("users"):

        users = [utils.to_user_id(i) for i in request.args["users"].split(",")]

        sql = "SELECT date"
        sql += " || ',' || SUM(CASE WHEN userid = ? THEN 1 ELSE 0 END) " * len(users)
        sql += " AS data "
        sql += " FROM logs "
        sql += " WHERE roomid = ? "
        sql += " AND userid IN(" + ", ".join(list("?" * len(users))) + ") "
        sql += " GROUP BY date"
        data = db.execute(sql, users + [room] + users)

        result = "\n".join([row["data"] for row in data])

        return result

    else:

        sql = """SELECT date
                 || ',' || COUNT(*)  -- total
                 || ',' || SUM(CASE WHEN userrank = ' ' THEN 1 ELSE 0 END)  -- regular
                 || ',' || SUM(CASE WHEN userrank != ' ' THEN 1 ELSE 0 END)  -- auth
                 || ',' || SUM(CASE WHEN userrank NOT IN(' ', '+') THEN 1 ELSE 0 END)  -- staff
                 || ',' || SUM(CASE WHEN userrank = '+' THEN 1 ELSE 0 END)  -- voice
                 || ',' || SUM(CASE WHEN userrank = '%' THEN 1 ELSE 0 END)  -- driver
                 || ',' || SUM(CASE WHEN userrank = '@' THEN 1 ELSE 0 END)  -- mod
                 || ',' || SUM(CASE WHEN userrank = '*' THEN 1 ELSE 0 END)  -- bot
                 || ',' || SUM(CASE WHEN userrank IN('&', '~') THEN 1 ELSE 0 END)  -- leader/admin
                 || ',' || SUM(CASE WHEN userrank = '#' THEN 1 ELSE 0 END)  -- owner
                 AS data
                 FROM logs WHERE roomid = ? GROUP BY date"""

        data = db.execute(sql, [room])

        result = "\n".join([row["data"] for row in data])

        return result

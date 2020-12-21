from __future__ import annotations

import asyncio
import datetime
from typing import TYPE_CHECKING, Dict, Iterator, List, Optional, Union, cast

from flask import abort, render_template, request
from flask import session as web_session
from lxml.html import fromstring  # type: ignore
from sqlalchemy.sql import func

import databases.logs as l
import utils
from database import Database
from handlers import handler_wrapper
from models.room import Room
from plugins import command_wrapper, route_wrapper
from tasks import recurring_task_wrapper

if TYPE_CHECKING:
    from connection import Connection
    from models.message import Message


@recurring_task_wrapper()
async def logger_task(conn: Connection) -> None:
    db = Database.open("logs")
    while True:
        with db.get_session() as session:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)

            for room in list(conn.rooms.keys()):
                if not Room.get(conn, room).roombot:
                    continue

                last_date = (
                    session.query(func.max(l.Logs.date))  # type: ignore  # sqlalchemy
                    .filter_by(roomid=room)
                    .scalar()
                )

                if last_date:
                    date = datetime.date.fromisoformat(last_date) + datetime.timedelta(
                        days=1
                    )
                else:
                    date = yesterday - datetime.timedelta(days=2)

                while date < yesterday:
                    await asyncio.sleep(30)
                    await conn.send(f"|/join view-chatlog-{room}--{date.isoformat()}")
                    date += datetime.timedelta(days=1)

        await asyncio.sleep(12 * 60 * 60)


@handler_wrapper(["pagehtml"])
async def logger(conn: Connection, room: Room, *args: str) -> None:
    if room.roomid[:13] != "view-chatlog-":
        return

    logsroom, date = room.roomid[13:].split("--")
    chatlog = "|".join(args).strip()

    html = fromstring(chatlog)

    values = []

    for el in html.xpath('//div[@class="chat"]'):
        time = el.xpath("small")
        user = el.xpath("strong")
        message = el.xpath("q")
        if time and user and message:
            userrank = user[0].xpath("small")
            values.append(
                {
                    "roomid": logsroom,
                    "date": date,
                    "time": time[0].text.strip("[] "),
                    "userrank": userrank[0].text if userrank else " ",
                    "userid": utils.to_user_id(user[0].text_content()),
                    "message": message[0].text_content(),
                }
            )

    if not values:
        values.append({"roomid": logsroom, "date": date})

    db = Database.open("logs")
    with db.get_session() as session:
        session.query(l.Logs).filter_by(date=date, roomid=logsroom).delete(
            synchronize_session=False
        )
        session.bulk_insert_mappings(l.Logs, values)

        session.query(l.DailyTotalsPerRank).filter_by(
            date=date, roomid=logsroom
        ).delete(synchronize_session=False)
        session.execute(
            "INSERT INTO daily_totals_per_rank (roomid, date, userrank, messages) "
            "SELECT roomid, date, userrank, COUNT(*) "
            "FROM logs "
            "WHERE roomid=:roomid AND date=:date "
            "GROUP BY userrank "
            "HAVING userrank IS NOT NULL",
            {"roomid": logsroom, "date": date},
        )

        session.query(l.DailyTotalsPerUser).filter_by(
            date=date, roomid=logsroom
        ).delete(synchronize_session=False)
        session.execute(
            "INSERT INTO daily_totals_per_user (roomid, date, userid, messages) "
            "SELECT roomid, date, userid, COUNT(*) "
            "FROM logs "
            "WHERE roomid=:roomid AND date=:date "
            "GROUP BY userid "
            "HAVING userid IS NOT NULL",
            {"roomid": logsroom, "date": date},
        )


@command_wrapper(parametrize_room=True)
async def getlogs(msg: Message) -> None:
    if msg.user.userid in msg.conn.administrators:
        logsroom = msg.parametrized_room.roomid
        date = msg.arg.strip()
        await msg.conn.send(f"|/join view-chatlog-{logsroom}--{date}")


@command_wrapper(aliases=("linecount",), required_rank="driver", parametrize_room=True)
async def linecounts(msg: Message) -> None:
    logsroom = msg.parametrized_room.roomid

    rank = msg.parametrized_room.users[msg.user]

    token_id = utils.create_token({logsroom: rank}, 1)

    message = f"{msg.conn.domain}linecounts/{logsroom}?token={token_id}"
    if msg.arg:
        search = ",".join([utils.to_user_id(u) for u in msg.args])
        message += f"&search={search}"

    await msg.user.send(message)


@command_wrapper(required_rank="driver", parametrize_room=True)
async def topusers(msg: Message) -> None:
    logsroom = msg.parametrized_room.roomid

    rank = msg.parametrized_room.users[msg.user]

    token_id = utils.create_token({logsroom: rank}, 1)

    message = f"{msg.conn.domain}linecounts/{logsroom}?token={token_id}&topusers=1"

    await msg.user.send(message)


@route_wrapper("/linecounts/<room>")
def linecounts_route(room: str) -> str:
    if not utils.has_role("driver", web_session.get(room)):
        abort(401)

    return render_template("linecounts.html", room=room)


@route_wrapper("/linecounts/<room>/data")
def linecounts_data(room: str) -> str:
    if not utils.has_role("driver", web_session.get(room)):
        abort(401)

    out = ""
    data: Dict[str, Dict[str, int]] = {}

    date: Optional[datetime.date] = None
    date_str: str

    db = Database.open("logs")

    with db.get_session() as session:

        columns: List[str]
        results: Union[List[l.DailyTotalsPerUser], List[l.DailyTotalsPerRank]]
        if request.args.get("topusers"):
            min_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
            query = (
                session.query(l.DailyTotalsPerUser)
                .filter_by(roomid=room)
                .filter(l.DailyTotalsPerUser.date >= min_date)
            )
            columns = [
                utils.to_user_id(row.userid)
                for row in query.group_by(l.DailyTotalsPerUser.userid)
                .order_by(func.sum(l.DailyTotalsPerUser.messages).desc())
                .limit(20)
                .all()
            ]
            results = (
                query.filter(l.DailyTotalsPerUser.userid.in_(columns))
                .order_by(l.DailyTotalsPerUser.date)
                .all()
            )
            out += ",".join(columns) + "\n"
        elif request.args.get("users"):
            columns = [
                utils.to_user_id(user) for user in request.args["users"].split(",")
            ]
            results = (
                session.query(l.DailyTotalsPerUser)
                .filter_by(roomid=room)
                .filter(l.DailyTotalsPerUser.userid.in_(columns))
                .order_by(l.DailyTotalsPerUser.date)
                .all()
            )
        else:
            columns = [" ", "+", "%", "@", "*", "&", "~", "#"]
            results = (
                session.query(l.DailyTotalsPerRank)
                .filter_by(roomid=room)
                .order_by(
                    l.DailyTotalsPerRank.date,
                    func.instr(" +%@*&~#", l.DailyTotalsPerRank.userrank),
                )
                .all()
            )

        if results:
            results_iter: Union[
                Iterator[l.DailyTotalsPerUser], Iterator[l.DailyTotalsPerRank]
            ]
            if request.args.get("topusers") or request.args.get("users"):
                results = cast(List[l.DailyTotalsPerUser], results)
                results_iter = iter(results)
            else:
                results = cast(List[l.DailyTotalsPerRank], results)
                results_iter = iter(results)

            while True:
                row = next(results_iter, None)

                if row is None:
                    break

                while True:
                    if date is None:
                        date = datetime.date.fromisoformat(row.date)
                        date_str = date.isoformat()

                    if date_str not in data:
                        data[date_str] = {column: 0 for column in columns}

                    if date_str < row.date:
                        date += datetime.timedelta(days=1)
                        date_str = date.isoformat()
                    else:
                        break

                if request.args.get("topusers") or request.args.get("users"):
                    row = cast(l.DailyTotalsPerUser, row)
                    column = row.userid
                else:
                    row = cast(l.DailyTotalsPerRank, row)
                    column = row.userrank

                if column in data[date_str]:
                    data[date_str][column] += row.messages

            if request.args.get("topusers") or request.args.get("users"):
                out_urow = "{date},{values}\n"
                for d in data:
                    out += out_urow.format(
                        date=d, values=",".join([str(i) for i in data[d].values()])
                    )
            else:
                out_rrow = (
                    "{date},{total},{regular},{auth},{staff},"
                    "{voice},{driver},{moderator},{bot},{administrator},{owner}\n"
                )
                for d in data:
                    staff = (
                        data[d]["%"]
                        + data[d]["@"]
                        + data[d]["*"]
                        + data[d]["&"]
                        + data[d]["~"]
                        + data[d]["#"]
                    )
                    auth = staff + data[d]["+"]
                    total = auth + data[d][" "]

                    out += out_rrow.format(
                        date=d,
                        total=total,
                        regular=str(data[d][" "]),
                        auth=auth,
                        staff=staff,
                        voice=str(data[d]["+"]),
                        driver=str(data[d]["%"]),
                        moderator=str(data[d]["@"]),
                        bot=str(data[d]["*"]),
                        administrator=str(data[d]["&"] + data[d]["~"]),
                        owner=str(data[d]["#"]),
                    )

    return out

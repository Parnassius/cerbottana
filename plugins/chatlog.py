from __future__ import annotations

import asyncio
import datetime
from typing import TYPE_CHECKING, Dict, Optional

from flask import abort, render_template, request
from flask import session as web_session
from lxml.html import fromstring
from sqlalchemy.sql import func

import databases.logs as l
import utils
from database import Database
from handlers import handler_wrapper
from plugins import command_wrapper, parametrize_room, route_wrapper
from room import Room
from tasks import recurring_task_wrapper

if TYPE_CHECKING:
    from connection import Connection


@recurring_task_wrapper()
async def logger_task(conn: Connection) -> None:
    db = Database.open("logs")
    while True:
        with db.get_session() as session:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)

            for room in conn.rooms + conn.private_rooms:
                last_date = (
                    session.query(func.max(l.Logs.date)).filter_by(roomid=room).scalar()
                )

                if last_date:
                    date = datetime.date.fromisoformat(last_date) + datetime.timedelta(
                        days=1
                    )
                else:
                    date = yesterday - datetime.timedelta(days=2)

                while date < yesterday:
                    await asyncio.sleep(30)
                    await conn.send_message(
                        "", f"/join view-chatlog-{room}--{date.isoformat()}", False
                    )
                    date += datetime.timedelta(days=1)

        await asyncio.sleep(12 * 60 * 60)


@handler_wrapper(["pagehtml"])
async def logger(conn: Connection, roomid: str, *args: str) -> None:
    if roomid[:13] != "view-chatlog-":
        return

    room, date = roomid[13:].split("--")
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
                    "roomid": room,
                    "date": date,
                    "time": time[0].text.strip("[] "),
                    "userrank": userrank[0].text if userrank else " ",
                    "userid": utils.to_user_id(user[0].text_content()),
                    "message": message[0].text_content(),
                }
            )

    if not values:
        values.append({"roomid": room, "date": date})

    db = Database.open("logs")
    with db.get_session() as session:
        session.query(l.Logs).filter_by(date=date, roomid=room).delete(
            synchronize_session=False
        )
        session.bulk_insert_mappings(l.Logs, values)

        session.query(l.DailyTotalsPerRank).filter_by(date=date, roomid=room).delete(
            synchronize_session=False
        )
        session.execute(
            "INSERT INTO daily_totals_per_rank (roomid, date, userrank, messages) "
            "SELECT roomid, date, userrank, COUNT(*) "
            "FROM logs "
            "WHERE roomid=:roomid AND date=:date "
            "GROUP BY userrank "
            "HAVING userrank IS NOT NULL",
            {"roomid": room, "date": date},
        )

        session.query(l.DailyTotalsPerUser).filter_by(date=date, roomid=room).delete(
            synchronize_session=False
        )
        session.execute(
            "INSERT INTO daily_totals_per_user (roomid, date, userid, messages) "
            "SELECT roomid, date, userid, COUNT(*) "
            "FROM logs "
            "WHERE roomid=:roomid AND date=:date "
            "GROUP BY userid "
            "HAVING userid IS NOT NULL",
            {"roomid": room, "date": date},
        )


@command_wrapper()
@parametrize_room
async def getlogs(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if utils.to_user_id(user) in conn.administrators:
        args = arg.split(",")
        logsroom = utils.to_room_id(args[0])
        date = args[1].strip()
        await conn.send_message("", f"/join view-chatlog-{logsroom}--{date}", False)


@command_wrapper(aliases=("linecount",))
@parametrize_room
async def linecounts(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    userid = utils.to_user_id(user)
    args = arg.split(",")
    logsroom = utils.to_room_id(args[0])

    users = Room.get(logsroom).users
    if userid not in users:
        return

    rank = users[userid]["rank"]

    token_id = utils.create_token({logsroom: rank}, 1)

    message = f"{conn.domain}linecounts/{logsroom}?token={token_id}"
    if len(args) > 1:
        search = ",".join([utils.to_user_id(u) for u in args[1:]])
        message += f"&search={search}"

    await conn.send_pm(user, message)


@route_wrapper("/linecounts/<room>")
def linecounts_route(room: str) -> str:
    if not utils.is_driver(web_session.get(room)):
        abort(401)

    return render_template("linecounts.html", room=room)


@route_wrapper("/linecounts/<room>/data")
def linecounts_data(room: str) -> str:
    if not utils.is_driver(web_session.get(room)):
        abort(401)

    out = ""
    data: Dict[str, Dict[str, int]] = {}

    date: Optional[datetime.date] = None
    date_str: str

    db = Database.open("logs")

    with db.get_session() as session:
        if request.args.get("users"):

            users = [
                utils.to_user_id(user) for user in request.args["users"].split(",")
            ]

            results_per_user = (
                session.query(l.DailyTotalsPerUser)
                .filter(
                    l.DailyTotalsPerUser.roomid == room,
                    l.DailyTotalsPerUser.userid.in_(users),
                )
                .order_by(l.DailyTotalsPerUser.date)
                .all()
            )

            if results_per_user:
                results_per_user_iter = iter(results_per_user)

                while True:
                    urow = next(results_per_user_iter, None)

                    if urow is None:
                        break

                    while True:
                        if date is None:
                            date = datetime.date.fromisoformat(urow.date)
                            date_str = date.isoformat()

                        if date_str not in data:
                            data[date_str] = {user: 0 for user in users}

                        if date_str < urow.date:
                            date += datetime.timedelta(days=1)
                            date_str = date.isoformat()
                        else:
                            break

                    if urow.userid in data[date_str]:
                        data[date_str][urow.userid] += urow.messages

                out_urow = "{date},{values}\n"
                for d in data:
                    out += out_urow.format(
                        date=d, values=",".join([str(i) for i in data[d].values()])
                    )

        else:

            results_per_rank = (
                session.query(l.DailyTotalsPerRank)
                .filter(l.DailyTotalsPerRank.roomid == room)
                .order_by(
                    l.DailyTotalsPerRank.date,
                    func.instr(" +%@*&~#", l.DailyTotalsPerRank.userrank),
                )
                .all()
            )

            if results_per_rank:
                results_per_rank_iter = iter(results_per_rank)

                while True:
                    rrow = next(results_per_rank_iter, None)

                    if rrow is None:
                        break

                    while True:
                        if date is None:
                            date = datetime.date.fromisoformat(rrow.date)
                            date_str = date.isoformat()

                        if date_str not in data:
                            data[date_str] = {
                                " ": 0,
                                "+": 0,
                                "%": 0,
                                "@": 0,
                                "*": 0,
                                "&": 0,
                                "~": 0,
                                "#": 0,
                            }

                        if date_str < rrow.date:
                            date += datetime.timedelta(days=1)
                            date_str = date.isoformat()
                        else:
                            break

                    if rrow.userrank in data[date_str]:
                        data[date_str][rrow.userrank] += rrow.messages

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

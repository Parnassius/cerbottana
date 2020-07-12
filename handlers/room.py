from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from connection import Connection

import json

from inittasks import inittask_wrapper
from handlers import handler_wrapper
import utils

from room import Room

from database import Database


@inittask_wrapper()
async def create_table(conn: Connection) -> None:
    db = Database()

    sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'users'"
    if not db.execute(sql).fetchone():
        sql = """CREATE TABLE users (
            id INTEGER,
            userid TEXT,
            username TEXT,
            avatar TEXT,
            description TEXT,
            description_pending TEXT,
            PRIMARY KEY(id)
        )"""
        db.execute(sql)

        sql = """CREATE UNIQUE INDEX idx_unique_users_userid
        ON users (
            userid
        )"""
        db.execute(sql)

        sql = """CREATE INDEX idx_users_description_pending
        ON users (
            description_pending
        )"""
        db.execute(sql)

        sql = "INSERT INTO metadata (key, value) VALUES ('table_version_users', '1')"
        db.execute(sql)

        db.commit()


async def add_user(
    conn: Connection, roomid: str, user: str, skip_avatar_check: bool = False
) -> None:
    rank = user[0]
    username = user[1:].split("@")[0]
    userid = utils.to_user_id(username)
    idle = user[-2:] == "@!"

    room = Room.get(roomid)

    room.add_user(userid, rank, username, idle)

    if userid == utils.to_user_id(conn.username):
        room.roombot = rank == "*"

    db = Database()
    sql = "INSERT INTO users (userid, username) VALUES (?, ?) "
    sql += " ON CONFLICT (userid) DO UPDATE SET username = excluded.username"
    db.executenow(sql, [userid, username])

    if not skip_avatar_check or rank != " ":
        await conn.send_message("", "/cmd userdetails {}".format(username), False)


async def remove_user(conn: Connection, roomid: str, user: str) -> None:
    Room.get(roomid).remove_user(utils.to_user_id(user))


@handler_wrapper(["title"])
async def title(conn: Connection, roomid: str, *args: str) -> None:
    if len(args) < 1:
        return

    roomtitle = args[0]

    Room.get(roomid).title = roomtitle


@handler_wrapper(["users"])
async def users(conn: Connection, roomid: str, *args: str) -> None:
    if len(args) < 1:
        return

    userlist = args[0]

    for user in userlist.split(",")[1:]:
        await add_user(conn, roomid, user, True)


@handler_wrapper(["join", "j", "J"])
async def join(conn: Connection, roomid: str, *args: str) -> None:
    if len(args) < 1:
        return

    user = args[0]

    await add_user(conn, roomid, user)


@handler_wrapper(["leave", "l", "L"])
async def leave(conn: Connection, roomid: str, *args: str) -> None:
    if len(args) < 1:
        return

    user = args[0]

    await remove_user(conn, roomid, user)


@handler_wrapper(["name", "n", "N"])
async def name(conn: Connection, roomid: str, *args: str) -> None:
    if len(args) < 2:
        return

    user = args[0]
    oldid = args[1]

    await remove_user(conn, roomid, oldid)
    await add_user(conn, roomid, user)


@handler_wrapper(["queryresponse"])
async def queryresponse(conn: Connection, roomid: str, *args: str) -> None:
    if len(args) < 2:
        return

    querytype = args[0]
    querydata = args[1]

    if querytype != "userdetails":
        return

    data = json.loads(querydata)
    userid = data["userid"]
    avatar = str(data["avatar"])
    if avatar in utils.AVATAR_IDS:
        avatar = utils.AVATAR_IDS[avatar]

    db = Database()
    sql = "INSERT INTO users (userid, avatar) VALUES (?, ?) "
    sql += " ON CONFLICT (userid) DO UPDATE SET avatar = excluded.avatar"
    db.executenow(sql, [userid, avatar])

    if data["rooms"] is not False:
        global_rank = data["group"]
        for roomid in data["rooms"]:
            room = Room.get(utils.to_room_id(roomid))
            room_rank = roomid[0] if utils.is_voice(roomid[0]) else " "
            room.set_global_and_room_rank(userid, global_rank, room_rank)

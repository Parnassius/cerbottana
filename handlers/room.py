from __future__ import annotations

import json
from typing import TYPE_CHECKING

import databases.database as d
import utils
from database import Database
from handlers import handler_wrapper
from models.room import Room
from models.user import User

if TYPE_CHECKING:
    from connection import Connection


async def add_user(
    conn: Connection,
    room: Room,
    userstring: str,
    skip_avatar_check: bool = False,
) -> None:
    rank = userstring[0]
    user = User.get(conn, userstring[1:])  # Strip leading character rank
    room.add_user(user)  # Rank will be retrieved from userdetails, if necessary

    if user.userid == utils.to_user_id(conn.username):
        room.roombot = rank == "*"

    db = Database.open()
    with db.get_session() as session:
        session.add(d.Users(userid=user.userid, username=user.username))

    if not skip_avatar_check or rank != " ":
        await conn.send(f"|/cmd userdetails {user.username}")


async def remove_user(conn: Connection, room: Room, userstring: str) -> None:
    user = User.get(conn, userstring)
    room.remove_user(user)


@handler_wrapper(["init"])
async def init(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 1:
        return

    if args[0] == "chat":
        await conn.send(f"|/cmd roominfo {room.roomid}")
        await room.send("/roomlanguage", False)


@handler_wrapper(["title"])
async def title(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 1:
        return

    room.title = args[0]


@handler_wrapper(["users"])
async def users(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 1:
        return

    userlist = args[0]

    for user in userlist.split(",")[1:]:
        await add_user(conn, room, user, True)


@handler_wrapper(["join", "j", "J"])
async def join(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 1:
        return

    user = args[0]

    await add_user(conn, room, user)


@handler_wrapper(["leave", "l", "L"])
async def leave(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 1:
        return

    user = args[0]

    await remove_user(conn, room, user)


@handler_wrapper(["name", "n", "N"])
async def name(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 2:
        return

    userstring = args[0]
    oldid = args[1]

    # If the nick change changes userid, treat the new user as unrelated
    if utils.to_user_id(userstring) != utils.to_user_id(oldid):
        await remove_user(conn, room, oldid)

    await add_user(conn, room, userstring)


@handler_wrapper(["queryresponse"])
async def queryresponse(conn: Connection, room: Room, *args: str) -> None:
    if len(args) < 2:
        return

    querytype = args[0]
    querydata = args[1]

    if querytype != "userdetails":
        return

    data = json.loads(querydata)
    user = User.get(conn, data["name"])
    avatar = str(data["avatar"])
    if avatar in utils.AVATAR_IDS:
        avatar = utils.AVATAR_IDS[avatar]

    db = Database.open()
    with db.get_session() as session:
        session.add(d.Users(userid=user.userid))
        session.query(d.Users).filter_by(userid=user.userid).update({"avatar": avatar})

    if data["rooms"] is not False:
        user.global_rank = data["group"]
        for r in data["rooms"]:
            room = Room.get(conn, utils.to_room_id(r))
            room_rank = r[0] if utils.has_role("voice", r[0]) else " "
            room.add_user(user, room_rank)

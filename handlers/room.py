from __future__ import annotations

import json
import string
from typing import TYPE_CHECKING, Set

import databases.database as d
import utils
from database import Database
from handlers import handler_wrapper
from models.room import Room
from models.user import User
from typedefs import JsonDict

if TYPE_CHECKING:
    from connection import Connection


async def add_user(
    conn: Connection,
    room: Room,
    userstring: str,
    from_userlist: bool = False,
) -> None:
    rank = userstring[0]
    user = User.get(conn, userstring[1:])  # Strip leading character rank

    if not from_userlist:
        user.userstring = userstring[1:]  # Always update userstring on |j| and |n|

    room.add_user(user)  # Rank will be retrieved from userdetails, if necessary

    if user.userid == utils.to_user_id(conn.username):
        room.roombot = rank == "*"

    db = Database.open()
    with db.get_session() as session:
        session.add(d.Users(userid=user.userid, username=user.username))

    if not from_userlist or rank != " ":
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

    parsers = {
        "rooms": _parse_rooms,
        "userdetails": _parse_userdetails,
    }

    if querytype in parsers:
        jsondata = json.loads(querydata)
        await parsers[querytype](conn, room, jsondata)


async def _parse_rooms(conn: Connection, room: Room, jsondata: JsonDict) -> None:
    """|queryresponse|rooms| sub-handler"""
    public_roomids: Set[str] = set()
    for roomgroup in jsondata.values():
        # Skip node if it isn't a roomgroup
        if not isinstance(roomgroup, list):
            continue

        # Save roomids for public rooms and subrooms
        for room_ in roomgroup:
            roomid = utils.to_room_id(room_["title"])
            public_roomids.add(roomid)

            if "subRooms" in room_:
                for subroom in room_["subRooms"]:
                    roomid = utils.to_room_id(subroom)
                    public_roomids.add(roomid)

    # For future reference, reassigning `conn.public_roomids` instead of adding elements
    # directly is better because it removes deleted rooms. As of now the difference is
    # irrelevant because `|/rooms` is called only once.
    conn.public_roomids = public_roomids


async def _parse_userdetails(conn: Connection, room: Room, jsondata: JsonDict) -> None:
    """|queryresponse|userdetails| sub-handler"""
    user = User.get(conn, jsondata["name"])
    avatar = str(jsondata["avatar"])
    if avatar in utils.AVATAR_IDS:
        avatar = utils.AVATAR_IDS[avatar]

    db = Database.open()
    with db.get_session() as session:
        session.add(d.Users(userid=user.userid))
        session.query(d.Users).filter_by(userid=user.userid).update({"avatar": avatar})

    if jsondata["rooms"] is not False:
        user.global_rank = jsondata["group"]
        for r in jsondata["rooms"]:
            room = Room.get(conn, utils.to_room_id(r))
            room_rank = (
                r[0] if r[0] not in string.ascii_letters + string.digits else " "
            )
            room.add_user(user, room_rank)

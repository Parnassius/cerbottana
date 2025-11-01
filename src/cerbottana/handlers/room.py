import json
import string
from typing import TYPE_CHECKING

from sqlalchemy import update

import cerbottana.databases.database as d
from cerbottana import utils
from cerbottana.database import Database
from cerbottana.handlers import handler_wrapper
from cerbottana.models.protocol_message import ProtocolMessage
from cerbottana.models.room import Room
from cerbottana.models.user import User
from cerbottana.typedefs import JsonDict

if TYPE_CHECKING:
    from cerbottana.connection import Connection


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
        session.add(d.Users(userid=user.userid))
        stmt = (
            update(d.Users).filter_by(userid=user.userid).values(username=user.username)
        )
        session.execute(stmt)

    if not from_userlist or rank != " ":
        await user.load_details()


async def remove_user(conn: Connection, room: Room, userstring: str) -> None:
    user = User.get(conn, userstring)
    room.remove_user(user)


@handler_wrapper(["init"], required_parameters=1)
async def init(msg: ProtocolMessage) -> None:
    msg.conn.rooms[msg.room.roomid] = msg.room

    if msg.params[0] == "chat":
        await msg.conn.send(f"|/cmd roominfo {msg.room.roomid}")
        await msg.room.send("/roomlanguage", False)


@handler_wrapper(["deinit"])
async def deinit(msg: ProtocolMessage) -> None:
    del msg.conn.rooms[msg.room.roomid]


@handler_wrapper(["title"], required_parameters=1)
async def title(msg: ProtocolMessage) -> None:
    msg.room.title = msg.params[0]


@handler_wrapper(["users"], required_parameters=1)
async def users(msg: ProtocolMessage) -> None:
    userlist = msg.params[0]

    for user in userlist.split(",")[1:]:
        await add_user(msg.conn, msg.room, user, True)


@handler_wrapper(["join", "j", "J"], required_parameters=1)
async def join(msg: ProtocolMessage) -> None:
    user = msg.params[0]

    await add_user(msg.conn, msg.room, user)


@handler_wrapper(["leave", "l", "L"], required_parameters=1)
async def leave(msg: ProtocolMessage) -> None:
    user = msg.params[0]

    await remove_user(msg.conn, msg.room, user)


@handler_wrapper(["name", "n", "N"], required_parameters=2)
async def name(msg: ProtocolMessage) -> None:
    userstring = msg.params[0]
    oldid = msg.params[1]

    # If the nick change changes userid, treat the new user as unrelated
    if utils.to_user_id(userstring) != utils.to_user_id(oldid):
        await remove_user(msg.conn, msg.room, oldid)

    await add_user(msg.conn, msg.room, userstring)


@handler_wrapper(["queryresponse"], required_parameters=2)
async def queryresponse(msg: ProtocolMessage) -> None:
    querytype = msg.params[0]
    querydata = msg.params[1]

    parsers = {
        "rooms": _parse_rooms,
        "userdetails": _parse_userdetails,
    }

    if querytype in parsers:
        jsondata = json.loads(querydata)
        await parsers[querytype](msg, jsondata)


async def _parse_rooms(msg: ProtocolMessage, jsondata: JsonDict) -> None:
    """|queryresponse|rooms| sub-handler"""
    public_roomids: set[str] = set()
    # Save roomids for public rooms and subrooms
    for room in jsondata["chat"]:
        roomid = utils.to_room_id(room["title"])
        public_roomids.add(roomid)

        if "subRooms" in room:
            for subroom in room["subRooms"]:
                roomid = utils.to_room_id(subroom)
                public_roomids.add(roomid)

    # For future reference, reassigning `conn.public_roomids` instead of adding elements
    # directly is better because it removes deleted rooms. As of now the difference is
    # irrelevant because `|/rooms` is called only once.
    msg.conn.public_roomids = public_roomids


async def _parse_userdetails(msg: ProtocolMessage, jsondata: JsonDict) -> None:
    """|queryresponse|userdetails| sub-handler"""
    user = User.get(msg.conn, jsondata["name"])
    avatar = str(jsondata["avatar"])
    if avatar in utils.AVATAR_IDS:
        avatar = utils.AVATAR_IDS[avatar]

    db = Database.open()
    with db.get_session() as session:
        session.add(d.Users(userid=user.userid))
        stmt = update(d.Users).filter_by(userid=user.userid).values(avatar=avatar)
        session.execute(stmt)

    if jsondata["rooms"] is not False:
        user.global_rank = jsondata["group"]
        for r in jsondata["rooms"]:
            room = Room.get(msg.conn, utils.to_room_id(r))
            room_rank = (
                r[0] if r[0] not in string.ascii_letters + string.digits else " "
            )
            room.add_user(user, room_rank)

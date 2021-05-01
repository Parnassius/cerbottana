from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select, update

import databases.database as d
import utils
from database import Database
from handlers import handler_wrapper
from models.room import Room
from plugins import command_wrapper
from tasks import recurring_task_wrapper

if TYPE_CHECKING:
    from connection import Connection
    from models.message import Message


@command_wrapper(
    required_rank="disabled", required_rank_editable=True, parametrize_room=True
)
async def tempvoice(msg: Message) -> None:
    if msg.parametrized_room.roombot and msg.user.rank(msg.parametrized_room) == " ":
        await msg.parametrized_room.send(f"/roomvoice {msg.user.userid}", False)
        db = Database.open()
        with db.get_session() as session:
            session.add(
                d.TemporaryVoices(
                    roomid=msg.parametrized_room.roomid,
                    userid=msg.user.userid,
                    date=str(datetime.utcnow()),
                )
            )


@recurring_task_wrapper()
async def demote_old_temporary_voices(conn: Connection) -> None:
    await asyncio.sleep(3 * 60 * 60)

    db = Database.open()
    while True:

        with db.get_session() as session:
            stmt = select(d.TemporaryVoices).filter(
                d.TemporaryVoices.date < datetime.utcnow() - timedelta(days=30)
            )
            user: d.TemporaryVoices | None = session.scalar(stmt)

            if user:
                room = Room.get(conn, user.roomid)
                if room.roombot:
                    await room.send(f"/roomdeauth {user.userid}", False)
                session.delete(user)
                # sleep for a minute, then try to deauth another user
                wait_time = 60
            else:
                # sleep for a day if there are no more users to deauth
                wait_time = 24 * 60 * 60

        await asyncio.sleep(wait_time)


@handler_wrapper(["join", "j", "J", "leave", "l", "L", "name", "n", "N"])
async def join_leave_name(conn: Connection, room: Room, *args: str) -> None:
    db = Database.open()
    with db.get_session() as session:
        for user in args:
            stmt = (
                update(d.TemporaryVoices)
                .filter_by(roomid=room.roomid, userid=utils.to_user_id(user))
                .values(date=str(datetime.utcnow()))
            )
            session.execute(stmt)

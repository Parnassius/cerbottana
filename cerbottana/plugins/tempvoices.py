from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select, update

import cerbottana.databases.database as d
from cerbottana import utils
from cerbottana.database import Database
from cerbottana.handlers import handler_wrapper
from cerbottana.models.room import Room
from cerbottana.plugins import command_wrapper
from cerbottana.tasks import recurring_task_wrapper

if TYPE_CHECKING:
    from cerbottana.connection import Connection
    from cerbottana.models.message import Message
    from cerbottana.models.protocol_message import ProtocolMessage


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
                    date=str(datetime.now(UTC)),
                )
            )


@recurring_task_wrapper()
async def demote_old_temporary_voices(conn: Connection) -> None:
    await asyncio.sleep(3 * 60 * 60)

    db = Database.open()
    while True:
        with db.get_session() as session:
            stmt = select(d.TemporaryVoices).filter(
                d.TemporaryVoices.date < datetime.now(UTC) - timedelta(days=30)
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
async def join_leave_name(msg: ProtocolMessage) -> None:
    db = Database.open()
    with db.get_session() as session:
        for user in msg.params:
            stmt = (
                update(d.TemporaryVoices)
                .filter_by(roomid=msg.room.roomid, userid=utils.to_user_id(user))
                .values(date=str(datetime.now(UTC)))
            )
            session.execute(stmt)

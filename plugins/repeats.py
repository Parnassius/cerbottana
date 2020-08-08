from __future__ import annotations

import asyncio
import math
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from dateutil.parser import parse
from environs import Env
from flask import abort, render_template
from flask import session as web_session
from sqlalchemy.sql import func

import databases.database as d
import utils
from database import Database
from plugins import command_wrapper, parametrize_room, route_wrapper
from room import Room
from tasks import init_task_wrapper

if TYPE_CHECKING:
    from connection import Connection


env = Env()
env.read_env()


class Repeat:
    """
    Implements an active record pattern to interact with the SQL database;
    also registers a task to the base asyncio loop of the Connection param.
    """

    _instances: Dict[Tuple[str, str], Repeat] = dict()  # record of active instances

    def __init__(
        self,
        conn: Connection,
        message: str,
        room: str,
        delta_minutes: int,
        initial_dt: Optional[datetime] = None,  # if None, then it's a new task
        expire_dt: Optional[datetime] = None,
        max_iters: Optional[int] = None,
    ) -> None:
        now = datetime.now()  # fixes the time for calculations within this method

        self.conn = conn
        self.message = message
        self.room = Room.get(room)

        self.delta = timedelta(minutes=delta_minutes)
        self.delta_minutes = delta_minutes  # kept only as an external property

        self.initial_dt = initial_dt if initial_dt else now

        self.expire_dt = expire_dt
        if max_iters:
            max_iters_dt = self.delta * (max_iters - 1) + now
            self.expire_dt = max(expire_dt, max_iters_dt) if expire_dt else max_iters_dt

        # is_new: True if the repeat has just been created with a chat command
        self.is_new = not initial_dt

        self.offset = timedelta(0)  # waiting time before the first repeat
        if not self.is_new:
            # make old repeats fire at the scheduled time, not instantly
            offline_period = now - self.initial_dt
            shift = self.delta * math.ceil(offline_period / self.delta)
            self.offset += shift - offline_period

        self.task: Optional[asyncio.Future[None]] = None

        log = [
            "----- REPEAT -----",
            f"message: {self.message}",
            f"room: {self.room.roomid}",
            f"delta: {self.delta}",
            f"initial_dt: {self.initial_dt}",
            f"expire_dt: {self.expire_dt}",
            f"now: {now}",
            f"offset: {self.offset}",
            "------------------",
        ]
        print("\n".join(log))

    @property
    def expired(self) -> bool:
        if self.expire_dt:
            return self.expire_dt + timedelta(seconds=1) < datetime.now()
        return False

    @property
    def key(self) -> Tuple[str, str]:
        return (self.message, self.room.roomid)

    async def coro(self) -> None:
        await asyncio.sleep(self.offset.total_seconds())

        while not self.expired:
            start = datetime.now()
            if (
                # conditions that cause a repeat to skip a call but not to stop forever
                not self.room.modchat  # don't send if modchat is active
                and self.message not in self.room.buffer  # throttling
            ):
                await self.conn.send_message(self.room.roomid, self.message, False)
            else:
                print(f"Not sending {self.message}")
            sleep_interval = self.delta - (datetime.now() - start)
            await asyncio.sleep(sleep_interval.total_seconds())

        self._unlist()

    def start(self) -> bool:
        if self.expired:
            if not self.is_new:
                self._unlist()
            return False

        if self.key in self._instances:  # this instance updates a previous one
            previous = self._instances[self.key]
            if previous.task:  # safety check: should never fail
                previous.task.cancel()
                # no need to previous._unlist(), we'll just update the SQL row
        self._instances[self.key] = self

        self.task = asyncio.ensure_future(self.coro(), loop=self.conn.loop)

        if self.is_new:
            # if the task has just been created, register it into the SQL db
            print(f"Registering {self.message} into db.")
            db = Database.open()
            with db.get_session() as session:
                session.add(
                    d.Repeats(
                        message=self.message,
                        roomid=self.room.roomid,
                        delta_minutes=self.delta_minutes,
                        initial_dt=str(self.initial_dt),
                        expire_dt=str(self.expire_dt),
                    )
                )

        return True

    def stop(self) -> None:
        if self.task:  # safety check: should never fail
            self.task.cancel()
        self._unlist()

    def _unlist(self) -> None:
        # remove corresponding SQL row
        db = Database.open()
        with db.get_session() as session:
            session.query(d.Repeats).filter_by(
                message=self.message, roomid=self.room.roomid
            ).delete()

        # remove from _instances dict
        self._instances.pop(self.key, None)

    @classmethod
    def get(cls, room: str, message: Optional[str] = None) -> List[Repeat]:
        if message:
            key = (message, room)
            return [cls._instances[key]] if key in cls._instances else []

        instances = [
            inst for inst in cls._instances.values() if inst.room.roomid == room
        ]
        return sorted(instances, key=lambda instance: instance.message)

    @classmethod
    def pull_db(cls, conn: Connection) -> None:
        """
        In a future implementation that supports changes via a Flask webpage, this
        method could be called multiple times to sync Repeat._instances with the
        modified SQL db.
        """

        db = Database.open()
        with db.get_session() as session:
            rows = session.query(d.Repeats).all()
            for row in rows:
                instance = cls(
                    conn,
                    row.message,
                    row.roomid,
                    row.delta_minutes,
                    initial_dt=parse(row.initial_dt),
                    expire_dt=parse(row.expire_dt) if row.expire_dt else None,
                )
                if not instance.start():
                    print(f"Failed to start {instance.message}")


@init_task_wrapper(priority=4)
async def load_old_repeats(conn: Connection) -> None:
    Repeat.pull_db(conn)


@command_wrapper(aliases=("addrepeat", "ripeti"))
async def repeat(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    if room is None or not utils.is_driver(user):
        return

    errmsg = "Sintassi: "
    errmsg += f"``{conn.command_character}repeat testo, distanza in minuti, scadenza`` "
    errmsg += "La scadenza può essere una data o il numero totale di ripetizioni."

    # parse command args
    args = [a.strip() for a in arg.split(",")]
    if len(args) > 3 or len(args) < 2:
        await conn.send_message(room, errmsg)
        return

    message = args[0]
    if message.lower() == "all":
        await conn.send_message(room, "Testo del repeat non valido.")
        return

    if not args[1].isdigit():
        await conn.send_message(room, errmsg)
        return
    delta_minutes = int(args[1])

    if len(args) == 2:  # no third param: repeat never expires
        instance = Repeat(conn, message, room, delta_minutes)
    elif args[2].isdigit():
        instance = Repeat(conn, message, room, delta_minutes, max_iters=int(args[2]))
    else:
        try:  # is the third param an expire date string?
            expire_dt = parse(args[2], default=datetime.now(), dayfirst=True)
            instance = Repeat(conn, message, room, delta_minutes, expire_dt=expire_dt)
        except ValueError:
            await conn.send_message(room, errmsg)
            return

    # start repeat and report result
    if not instance.start():
        await conn.send_message(room, errmsg)


@command_wrapper(aliases=("clearrepeat", "deleterepeat", "rmrepeat"))
async def stoprepeat(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    if room is None or not utils.is_driver(user) or not arg:
        return

    query = None if arg.lower().strip() == "all" else arg
    instances = Repeat.get(room, query)

    if not instances:
        await conn.send_message(room, "Nessun repeat da cancellare.")
        return

    for instance in instances:
        instance.stop()

    await conn.send_message(room, "Fatto.")


@command_wrapper(aliases=("repeats",))
@parametrize_room
async def showrepeats(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    repeats_room = arg.split(",")[0]
    userid = utils.to_user_id(user)
    users = Room.get(repeats_room).users
    rank = users[userid]["rank"]

    if not utils.is_driver(rank):
        await conn.send_pm(user, f"Devi essere almeno driver in {repeats_room}.")
        return

    db = Database.open()
    with db.get_session() as session:
        repeats_n = (
            session.query(func.count(d.Repeats.id))
            .filter_by(roomid=repeats_room)
            .first()
        )
    if not repeats_n:
        await conn.send_pm(user, "Nessun repeat attivo.")
        return

    token_id = utils.create_token({repeats_room: rank}, 1)
    url = f"{conn.domain}repeats/{repeats_room}?token={token_id}"
    await conn.send_pm(user, url)


@route_wrapper("/repeats/<room>")
def repeats(room: str) -> str:
    if not utils.is_driver(web_session.get(room)):
        abort(401)

    db = Database.open()

    with db.get_session() as session:
        rs = (
            session.query(d.Repeats)
            .filter_by(roomid=room)
            .order_by(d.Repeats.message)
            .all()
        )

        return render_template("repeats.html", rs=rs, room=room)

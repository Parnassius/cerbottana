from __future__ import annotations

import asyncio
import math
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from connection import Connection

from dateutil.parser import parse

import utils
from database import Database
from plugin_loader import plugin_wrapper
from room import Room
from tasks import init_task_wrapper


@init_task_wrapper(priority=3)
async def create_table(conn: Connection) -> None:  # lgtm [py/similar-function]
    db = Database()

    sql = "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'repeats'"
    if not db.execute(sql).fetchone():
        sql = """CREATE TABLE repeats (
            id INTEGER,
            message TEXT,
            roomid TEXT,
            delta_minutes INTEGER,
            initial_dt TEXT,
            expire_dt TEXT,
            PRIMARY KEY(id)
        )"""
        db.execute(sql)

        sql = """CREATE UNIQUE INDEX idx_unique_repeats_message_roomid
        ON repeats (
            message,
            roomid
        )"""
        db.execute(sql)

        sql = "INSERT INTO metadata (key, value) VALUES ('table_version_repeats', '1')"
        db.execute(sql)

        db.commit()


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
        self.is_new = False if initial_dt else True

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
                await self.conn.send_message(self.room.roomid, self.message)
            else:
                print(f"Not sending {self.message}")
            sleep_interval = self.delta - (datetime.now() - start)
            await asyncio.sleep(sleep_interval.total_seconds())

        self._unlist()

    def start(self) -> bool:
        if self.expired:
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
            db = Database()
            sql = "REPLACE INTO repeats (message, roomid, delta_minutes, initial_dt, expire_dt) "
            sql += "VALUES (?, ?, ?, ?, ?)"
            db.executenow(
                sql,
                [
                    self.message,
                    self.room.roomid,
                    self.delta_minutes,
                    self.initial_dt,
                    self.expire_dt,
                ],
            )

        return True

    def stop(self) -> None:
        if self.task:  # safety check: should never fail
            self.task.cancel()
        self._unlist()

    def _unlist(self) -> None:
        # remove corresponding SQL row
        db = Database()
        sql = "DELETE FROM repeats "
        sql += "WHERE message = ? AND roomid = ?"
        db.executenow(sql, [self.message, self.room.roomid])

        # remove from _instances dict
        self._instances.pop(self.key)

    def __lt__(self, other: Repeat) -> bool:
        # alphabetical order (for printing purposes)
        return (self.room.roomid, self.message) < (other.room.roomid, other.message)

    @classmethod
    def get(cls, room: str, message: Optional[str] = None) -> List[Repeat]:
        if message:
            key = (message, room)
            return [cls._instances[key]] if key in cls._instances else []

        instances = [
            inst for inst in cls._instances.values() if inst.room.roomid == room
        ]
        return sorted(instances)

    @classmethod
    def pull_db(cls, conn: Connection) -> None:
        """
        In a future implementation that supports changes via a Flask webpage, this
        method could be called multiple times to sync Repeat._instances with the
        modified SQL db.
        """

        db = Database()
        rows = db.execute("SELECT * FROM repeats").fetchall()
        for row in rows:
            instance = cls(
                conn,
                row["message"],
                row["roomid"],
                row["delta_minutes"],
                initial_dt=parse(row["initial_dt"]),
                expire_dt=parse(row["expire_dt"]) if row["expire_dt"] else None,
            )
            if not instance.start():
                print(f"Failed to start {instance.message}")


@init_task_wrapper(priority=4)
async def load_old_repeats(conn: Connection) -> None:
    Repeat.pull_db(conn)


@plugin_wrapper(aliases=["addrepeat", "ripeti"])
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


@plugin_wrapper(aliases=["deleterepeat", "rmrepeat"])
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


@plugin_wrapper(aliases=["repeats"])
async def showrepeats(
    conn: Connection, room: Optional[str], user: str, arg: str
) -> None:
    # TODO: Implement on Flask

    if room is None or not utils.is_driver(user):
        return

    html = (
        '<table style="width:100%">'
        + '<tr style="text-align:left">'
        + "<th>Messaggio</th>"
        + "<th>Intervallo</th>"
        + "<th>Scadenza</th>"
        + "</tr>"
    )

    for instance in Repeat.get(room):  # TODO: truncate instance.message with HTML
        html += "<tr>"
        for cell in [instance.message, instance.delta_minutes, instance.expire_dt]:
            html += f"<td>{cell}</td>"
        html += "</tr>"

    html += "</table>"

    await conn.send_htmlbox(room, user, html)

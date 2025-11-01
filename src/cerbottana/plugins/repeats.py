# Author: Plato (palt0)


import asyncio
import math
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, ClassVar

from dateutil.parser import parse
from domify import html_elements as e
from domify.base_element import BaseElement
from sqlalchemy import delete, select

import cerbottana.databases.database as d
from cerbottana.database import Database
from cerbottana.html_utils import HTMLPageCommand
from cerbottana.models.message import Message
from cerbottana.models.room import Room
from cerbottana.plugins import command_wrapper, htmlpage_wrapper
from cerbottana.tasks import init_task_wrapper

if TYPE_CHECKING:
    from cerbottana.connection import Connection
    from cerbottana.models.user import User


# WHITELISTED_CMD: List of commands that are broadcastable in a repeat. We don't have a
# validity check for the command syntax.
WHITELISTED_CMD = (
    "announce",
    "wall",
    "daily",
    "events",
    "roomevent",
    "roomevents",
    "rfaq",
    "roomfaq",
    "viewfaq",
    "show",
)


class Repeat:
    """Implements an active record pattern to interact with the SQL database;
    also registers a task to the base asyncio loop of the Connection param.
    """

    _instances: ClassVar[
        dict[tuple[str, Room], Repeat]
    ] = {}  # Record of active instances

    def __init__(
        self,
        message: str,
        room: Room,
        delta_minutes: int,
        *,
        initial_dt: datetime | None = None,  # If None, then it's a new task.
        expire_dt: datetime | None = None,
        max_iters: int | None = None,
    ) -> None:
        now = datetime.now(UTC)  # Fixes the time for calculations within this method.

        self.message = message
        self.room = room

        self.delta = timedelta(minutes=delta_minutes)
        self.delta_minutes = delta_minutes  # Kept only as an external property

        self.initial_dt = initial_dt if initial_dt else now

        self.expire_dt = expire_dt
        if max_iters:
            max_iters_dt = self.delta * (max_iters - 1) + now
            self.expire_dt = max(expire_dt, max_iters_dt) if expire_dt else max_iters_dt

        # is_new: True if the repeat has just been created with a chat command.
        self.is_new = not initial_dt

        self.offset = timedelta(0)  # Waiting time before the first repeat
        if not self.is_new:
            # Make old repeats fire at the scheduled time, not instantly.
            offline_period = now - self.initial_dt
            shift = self.delta * math.ceil(offline_period / self.delta)
            self.offset += shift - offline_period

        self.task: asyncio.Task[None] | None = None

        print(self)

    @property
    def expired(self) -> bool:
        if self.expire_dt:
            return self.expire_dt + timedelta(seconds=1) < datetime.now(UTC)
        return False

    @property
    def key(self) -> tuple[str, Room]:
        return (self.message, self.room)

    def __str__(self) -> str:
        return "\n".join(
            [
                "----- REPEAT -----",
                f"message: {self.message}",
                f"room: {self.room.roomid}",
                f"delta: {self.delta}",
                f"initial_dt: {self.initial_dt}",
                f"expire_dt: {self.expire_dt}",
                f"offset: {self.offset}",
                "------------------",
            ]
        )

    async def coro(self) -> None:
        await asyncio.sleep(self.offset.total_seconds())

        while not self.expired:
            start = datetime.now(UTC)
            if self.message not in self.room.buffer:  # Throttling
                await self.room.send(self.message, False)
            else:
                print(f"Not sending {self.message}")
            sleep_interval = self.delta - (datetime.now(UTC) - start)
            await asyncio.sleep(sleep_interval.total_seconds())

        self._unlist()

    def start(self) -> bool:
        if self.expired:
            if not self.is_new:
                self._unlist()
            return False

        if self.key in self._instances:  # This instance updates a previous one.
            previous = self._instances[self.key]
            if previous.task:  # Safety check: should never fail.
                previous.task.cancel()
                # No need to previous._unlist(), we'll just update the SQL row.
        self._instances[self.key] = self

        self.task = asyncio.create_task(self.coro())

        if self.is_new:
            # If the task has just been created, register it into the SQL db.
            print(f"Registering {self.message} into db.")
            db = Database.open()
            with db.get_session() as session:
                session.add(
                    d.Repeats(
                        message=self.message,
                        roomid=self.room.roomid,
                        delta_minutes=self.delta_minutes,
                        initial_dt=str(self.initial_dt),
                        expire_dt=str(self.expire_dt) if self.expire_dt else None,
                    )
                )

        return True

    def stop(self) -> None:
        if self.task:  # Safety check: should never fail.
            self.task.cancel()
        self._unlist()

    def _unlist(self) -> None:
        # Remove corresponding SQL row
        db = Database.open()
        with db.get_session() as session:
            stmt = delete(d.Repeats).filter_by(
                message=self.message, roomid=self.room.roomid
            )
            session.execute(stmt)

        # Remove from _instances dict
        self._instances.pop(self.key, None)

    @classmethod
    def get(cls, room: Room, message: str | None = None) -> list[Repeat]:
        if message:
            key = (message, room)
            return [cls._instances[key]] if key in cls._instances else []

        instances = [inst for inst in cls._instances.values() if inst.room == room]
        return sorted(instances, key=lambda instance: instance.message)

    @classmethod
    def pull_db(cls, conn: Connection) -> None:
        """In a future implementation that supports changes via a Flask webpage, this
        method could be called multiple times to sync Repeat._instances with the
        modified SQL db.
        """

        db = Database.open()
        with db.get_session() as session:
            stmt = select(d.Repeats)
            for row in session.execute(stmt).scalars():
                instance = cls(
                    row.message,
                    Room.get(conn, row.roomid),
                    row.delta_minutes,
                    initial_dt=parse(row.initial_dt),
                    expire_dt=parse(row.expire_dt) if row.expire_dt else None,
                )
                if not instance.start():
                    print(f"Failed to start {instance.message}")


@init_task_wrapper(priority=4)
async def load_old_repeats(conn: Connection) -> None:
    Repeat.pull_db(conn)


@command_wrapper(
    aliases=("addrepeat", "ripeti"), required_rank="driver", parametrize_room=True
)
async def repeat(msg: Message) -> None:
    ch = msg.conn.command_character
    errmsg = "Sintassi: "
    errmsg += f"``{ch}repeat testo, distanza in minuti, scadenza`` "
    errmsg += "La scadenza può essere una data o il numero totale di ripetizioni."

    # Parse command args
    if len(msg.args) > 3 or len(msg.args) < 2:
        await msg.reply(errmsg)
        return

    phrase = msg.args[0]
    if (
        # Reserved keyword for `.stoprepeat` command.
        phrase.lower() == "all"
        # Whitelisted commands
        or (phrase[0] in "/!" and phrase.split()[0][1:].lower() not in WHITELISTED_CMD)
    ):
        await msg.reply("Testo del repeat non valido.")
        return

    if not msg.args[1].isdigit():
        await msg.reply(errmsg)
        return
    delta_minutes = int(msg.args[1])

    if len(msg.args) == 2:  # No third param: repeat never expires.
        instance = Repeat(phrase, msg.parametrized_room, delta_minutes)
    elif msg.args[2].isdigit():
        instance = Repeat(
            phrase, msg.parametrized_room, delta_minutes, max_iters=int(msg.args[2])
        )
    else:
        try:  # Is the third param an expire date string?
            expire_dt = parse(msg.args[2], default=datetime.now(UTC), dayfirst=True)
            instance = Repeat(
                phrase, msg.parametrized_room, delta_minutes, expire_dt=expire_dt
            )
        except ValueError:
            await msg.reply(errmsg)
            return

    # Start repeat and report result
    if instance.start():
        if msg.room is None:
            await msg.parametrized_room.send_modnote("REPEAT ADDED", msg.user, phrase)
    else:
        await msg.reply(errmsg)


@command_wrapper(
    aliases=("clearrepeat", "deleterepeat", "rmrepeat"),
    required_rank="driver",
    parametrize_room=True,
)
async def stoprepeat(msg: Message) -> None:
    if not msg.arg:
        return

    query = None if msg.arg.lower().strip() == "all" else msg.arg
    instances = Repeat.get(msg.parametrized_room, query)

    if not instances:
        await msg.reply("Nessun repeat da cancellare.")
        return

    for instance in instances:
        instance.stop()

    await msg.reply("Fatto.")
    if msg.room is None:
        if query is None:
            await msg.parametrized_room.send_modnote("REPEATS CLEARED", msg.user)
        else:
            await msg.parametrized_room.send_modnote("REPEAT REMOVED", msg.user, query)


@htmlpage_wrapper("repeats", aliases=("showrepeats",), required_rank="driver")
def repeats_htmlpage(user: User, room: Room, page: int) -> BaseElement:
    stmt = select(d.Repeats).filter_by(roomid=room.roomid).order_by(d.Repeats.message)

    html = HTMLPageCommand(
        user,
        room,
        "repeats",
        stmt,
        title=f"Repeats for {room.title}",
        fields=[
            ("Phrase", lambda row: e.Div(row.Repeats.message)),
            ("Interval (minutes)", "delta_minutes"),
            ("Expiry", lambda row: str(row.Repeats.expire_dt or "Nope")),
        ],
    )

    html.load_page(page)

    return html.doc

from __future__ import annotations

import glob
import importlib
from functools import wraps
from os.path import basename, dirname, isfile, join
from typing import (
    TYPE_CHECKING,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)

from flask import abort, session

import utils
from room import Room

if TYPE_CHECKING:
    from connection import Connection

    CommandFunc = Callable[[Connection, Optional[str], str, str], Awaitable[None]]
    RouteFunc = Union[Callable[[], str], Callable[[str], str]]


# --- Command logic and complementary decorators ---


class Command:
    _instances: Dict[str, Command] = dict()

    def __init__(
        self,
        func: CommandFunc,
        aliases: List[str] = [],
        helpstr: str = "",
        is_unlisted: bool = False,
    ) -> None:
        self.name = func.__name__
        self.callback = func
        self.aliases = [self.name] + aliases  # needs to be a new binding
        self.helpstr = helpstr
        self.is_unlisted = is_unlisted
        self._instances[func.__name__] = self

    @property
    def splitted_aliases(self) -> Dict[str, Command]:
        return {alias: self for alias in self.aliases}

    @classmethod
    def get_all_aliases(cls) -> Dict[str, Command]:
        d: Dict[str, Command] = {}
        for command in cls._instances.values():
            d.update(command.splitted_aliases)
        return d

    @classmethod
    def get_all_helpstrings(cls) -> Dict[str, str]:
        d: Dict[str, str] = {}
        for command in cls._instances.values():
            if command.helpstr and not command.is_unlisted:
                d[command.name] = command.helpstr
        return {k: d[k] for k in sorted(d)}  # python 3.7+


def scope_checker(func: CommandFunc) -> CommandFunc:
    @wraps(func)
    async def scope_wrapper(
        conn: Connection, room: Optional[str], user: str, arg: str
    ) -> None:
        if room is not None and not utils.is_voice(user):
            return
        await func(conn, room, user, arg)

    return scope_wrapper


def command_wrapper(
    aliases: List[str] = [], helpstr: str = "", is_unlisted: bool = False
) -> Callable[[CommandFunc], Command]:
    def cls_wrapper(func: CommandFunc) -> Command:
        func = scope_checker(func)  # manual decorator binding
        return Command(func, aliases, helpstr, is_unlisted)

    return cls_wrapper


def parametrize_room(func: CommandFunc) -> CommandFunc:
    """
    Changes the syntax of a command depending on its context:
    (1) If it's used in a room, it automatically adds its roomid at the
        beginning of arg.
    (2) If it's used in PM, it requires to specify an additional parameter
        at the beginning of arg representing a roomid.

    This way, room-dependant commands can be used in PM too without coding
    any additional logic. An example is randquote (quotes.py).
    """

    @wraps(func)
    async def wrapper(
        conn: Connection, room: Optional[str], user: str, arg: str
    ) -> None:
        if room:  # (1) command used in a room: just add the roomid param to arg
            args = arg.split(",") if arg else []
            args.insert(0, room)
        else:  # (2) command used in PM: check perms
            if not arg:
                await conn.send_pm(user, "Specifica il nome della room.")
                return

            args = arg.split(",")
            args[0] = utils.to_room_id(args[0], fallback="")  # target room
            if not args[0]:
                await conn.send_pm(user, "Specifica il nome della room.")
                return

            if (
                args[0] not in conn.rooms + conn.private_rooms  # bot in room
                or utils.to_user_id(user) not in Room.get(args[0]).users  # user in room
            ):
                # Send the same message for both errors to avoid leaking private rooms
                await conn.send_pm(user, "Sei nella room?")
                return

        arg = ",".join(args)  # update original arg
        await func(conn, room, user, arg)

    return wrapper


# --- Flask implementation ---


routes: List[Tuple[RouteFunc, str, Optional[Iterable[str]]]] = list()


def route_require_driver(func: RouteFunc) -> RouteFunc:
    @wraps(func)
    def wrapper(*args: str) -> str:
        if not utils.is_driver(session.get("_rank")):
            abort(401)
        return func(*args)

    return wrapper


def route_wrapper(
    rule: str, methods: Optional[Iterable[str]] = None, require_driver: bool = False
) -> Callable[[RouteFunc], RouteFunc]:
    def wrapper(func: RouteFunc) -> RouteFunc:
        if require_driver:
            func = route_require_driver(func)  # manual decorator binding
        routes.append((func, rule, methods))
        return func

    return wrapper


# --- Module loading and post-loading objects ---


modules = glob.glob(join(dirname(__file__), "*.py"))

for f in modules:
    if isfile(f) and not f.endswith("__init__.py"):
        name = basename(f)[:-3]
        importlib.import_module("plugins." + name)

commands = Command.get_all_aliases()

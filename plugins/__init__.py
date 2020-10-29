from __future__ import annotations

import glob
import importlib
from functools import wraps
from os.path import basename, dirname, isfile, join
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)

from flask import abort
from flask import session as web_session
from sqlalchemy.orm import Query

import utils
from models.room import Room
from typedefs import Role, RoomId

if TYPE_CHECKING:
    from connection import Connection
    from models.message import Message
    from models.user import User

    CommandFunc = Callable[[Message], Awaitable[None]]
    HTMLPageFunc = Callable[[User, Room], Optional[Query[Any]]]  # type: ignore[misc]  # pylint: disable=unsubscriptable-object
    RouteFunc = Callable[..., str]  # type: ignore[misc]


# --- Command logic and complementary decorators ---


class Command:
    _instances: Dict[str, Command] = {}

    def __init__(
        self,
        func: CommandFunc,
        aliases: Tuple[str, ...] = (),
        helpstr: str = "",
        is_unlisted: bool = False,
    ) -> None:
        self.name = func.__name__
        self.callback = func
        self.aliases = (self.name,) + aliases
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
    async def scope_wrapper(msg: Message) -> None:
        if msg.room is not None and not msg.user.has_role("voice", msg.room):
            return
        await func(msg)

    return scope_wrapper


def command_wrapper(
    aliases: Tuple[str, ...] = (), helpstr: str = "", is_unlisted: bool = False
) -> Callable[[CommandFunc], Command]:
    def cls_wrapper(func: CommandFunc) -> Command:
        func = scope_checker(func)  # manual decorator binding
        return Command(func, aliases, helpstr, is_unlisted)

    return cls_wrapper


def parametrize_room(func: CommandFunc) -> CommandFunc:
    """
    Enriches a command depending on its context:
    (1) If it's used in a room, it saves such room in msg.parametrized_room.
    (2) If it's used in PM, it requires to specify a temporary parameter representing
        a room that'll be saved in msg.parametrized_room.

    This way, room-dependant commands can be used in PM too without coding any
    additional logic. An example is randquote (quotes.py).
    """

    @wraps(func)
    async def wrapper(msg: Message) -> None:
        if msg.room:  # (1)
            msg.parametrized_room = msg.room
        else:  # (2)
            # User didn't supply any parameters
            if not msg.arg:
                await msg.user.send("Specifica il nome della room")
                return

            # Check if user supplied a non-empty roomid
            target_roomid = utils.to_room_id(msg.args[0], fallback=RoomId(""))
            msg.args = msg.args[1:]
            if not target_roomid:
                await msg.user.send("Specifica il nome della room")
                return
            msg.parametrized_room = Room.get(msg.conn, target_roomid)

            # Check if the room is valid
            if (
                target_roomid not in msg.conn.rooms  # bot in room
                or msg.user not in msg.parametrized_room  # user in room
            ):
                # Send the same message for both errors to avoid leaking private rooms
                await msg.user.send("Sei nella room?")
                return

        # Every check passed: wrap the original function
        await func(msg)

    return wrapper


# --- HTML pages ---


htmlpages: Dict[str, HTMLPageFunc] = {}


def htmlpage_check_permission(
    func: HTMLPageFunc, required_rank: Optional[Role], main_room_only: bool
) -> HTMLPageFunc:
    @wraps(func)
    def wrapper(  # type: ignore[misc]
        user: User, room: Room
    ) -> Optional[Query[Any]]:  # pylint: disable=unsubscriptable-object
        if main_room_only and (
            not room.conn.main_room or room is not room.conn.main_room
        ):
            return None

        if required_rank is None:
            if user not in room:
                return None
        elif not user.has_role(required_rank, room):
            return None

        return func(user, room)

    return wrapper


def htmlpage_wrapper(
    pageid: str, required_rank: Optional[Role] = None, main_room_only: bool = False
) -> Callable[[HTMLPageFunc], HTMLPageFunc]:
    def wrapper(func: HTMLPageFunc) -> HTMLPageFunc:
        func = htmlpage_check_permission(func, required_rank, main_room_only)
        htmlpages[pageid] = func
        return func

    return wrapper


# --- Flask implementation ---


routes: List[Tuple[RouteFunc, str, Optional[Iterable[str]]]] = []


def route_require_driver(func: RouteFunc) -> RouteFunc:
    @wraps(func)
    def wrapper(**kwargs: str) -> str:
        if not utils.has_role("driver", web_session.get("_rank")):
            abort(401)
        return func(**kwargs)

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

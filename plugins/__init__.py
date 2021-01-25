from __future__ import annotations

import glob
import importlib
from collections.abc import Awaitable, Callable, Iterable
from functools import wraps
from os.path import basename, dirname, isfile, join
from typing import TYPE_CHECKING, Any, Optional

from flask import abort
from flask import session as web_session
from sqlalchemy.orm import Query

import utils
from models.room import Room
from typedefs import Role, RoomId

if TYPE_CHECKING:
    from models.message import Message
    from models.user import User

    CommandFunc = Callable[[Message], Awaitable[None]]
    HTMLPageFunc = Callable[[User, Room], Optional[Query[Any]]]  # type: ignore[misc]
    RouteFunc = Callable[..., str]  # type: ignore[misc]


# --- Command logic and complementary decorators ---


class Command:
    _instances: dict[str, Command] = {}

    def __init__(
        self,
        func: CommandFunc,
        aliases: tuple[str, ...],
        helpstr: str,
        is_unlisted: bool,
    ) -> None:
        self.name = func.__name__
        self.callback = func
        self.aliases = (self.name,) + aliases
        self.helpstr = helpstr
        self.is_unlisted = is_unlisted
        self._instances[func.__name__] = self

    @property
    def splitted_aliases(self) -> dict[str, Command]:
        return {alias: self for alias in self.aliases}

    @classmethod
    def get_all_aliases(cls) -> dict[str, Command]:
        d: dict[str, Command] = {}
        for command in cls._instances.values():
            d.update(command.splitted_aliases)
        return d

    @classmethod
    def get_all_helpstrings(cls) -> dict[str, str]:
        d: dict[str, str] = {}
        for command in cls._instances.values():
            if command.helpstr and not command.is_unlisted:
                d[command.name] = command.helpstr
        return {k: d[k] for k in sorted(d)}  # python 3.7+


def command_check_permission(
    func: CommandFunc,
    required_rank: Role,
    allow_pm: bool,
    main_room_only: bool,
    parametrize_room: bool,
) -> CommandFunc:
    @wraps(func)
    async def wrapper(msg: Message) -> None:
        if main_room_only and not msg.user.has_role(required_rank, msg.conn.main_room):
            return

        if not allow_pm and msg.room is None:
            return

        if parametrize_room:
            if msg.user not in msg.parametrized_room.users or not msg.user.has_role(
                required_rank, msg.parametrized_room
            ):
                return
        elif msg.room is not None and not msg.user.has_role(required_rank, msg.room):
            return

        await func(msg)

    return wrapper


def command_wrapper(
    *,
    aliases: tuple[str, ...] = (),
    helpstr: str = "",
    is_unlisted: bool = False,
    required_rank: Role = "voice",
    allow_pm: bool = True,
    main_room_only: bool = False,
    parametrize_room: bool = False,
) -> Callable[[CommandFunc], Command]:
    """Decorates a function to generate a Command instance.

    Args:
        aliases (tuple[str, ...]): List of aliases for the command, besides the function
            name. Defaults to ().
        helpstr (str): Short description of the command. Defaults to "".
        is_unlisted (bool): Whether the command should be listed in the `.help` summary.
            Defaults to False.
        required_rank (Role): Minimum PS rank required to trigger the command. Defaults
            to "voice".
        allow_pm (bool): True if the command can be used in PM (and not only in a room).
            Defaults to True.
        main_room_only (bool): Whether the main room should be used to check if the user
            has relevant auth. Defaults to False.
        parametrize_room (bool): Allows room-dependent commands to be used in PM. See
            the docstring of `parametrize_room_wrapper`. Defaults to False.

    Returns:
        Callable[[CommandFunc], Command]: Wrapper.
    """

    def cls_wrapper(func: CommandFunc) -> Command:
        func = command_check_permission(
            func, required_rank, allow_pm, main_room_only, parametrize_room
        )
        if parametrize_room:
            func = parametrize_room_wrapper(func)
        return Command(func, aliases, helpstr, is_unlisted)

    return cls_wrapper


def parametrize_room_wrapper(func: CommandFunc) -> CommandFunc:
    """Enriches a command depending on its context:
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


htmlpages: dict[str, HTMLPageFunc] = {}


def htmlpage_check_permission(
    func: HTMLPageFunc, required_rank: Role | None, main_room_only: bool
) -> HTMLPageFunc:
    @wraps(func)
    def wrapper(user: User, room: Room) -> Query[Any] | None:  # type: ignore[misc]
        if main_room_only and room is not room.conn.main_room:
            return None

        if required_rank is None:
            if user not in room:
                return None
        elif not user.has_role(required_rank, room):
            return None

        return func(user, room)

    return wrapper


def htmlpage_wrapper(
    pageid: str, *, required_rank: Role | None = None, main_room_only: bool = False
) -> Callable[[HTMLPageFunc], HTMLPageFunc]:
    def wrapper(func: HTMLPageFunc) -> HTMLPageFunc:
        func = htmlpage_check_permission(func, required_rank, main_room_only)
        htmlpages[pageid] = func
        return func

    return wrapper


# --- Flask implementation ---


routes: list[tuple[RouteFunc, str, Iterable[str] | None]] = []


def route_check_permission(func: RouteFunc, required_rank: Role | None) -> RouteFunc:
    @wraps(func)
    def wrapper(**kwargs: str) -> str:
        rank_check = kwargs.get("room", "_rank")
        if required_rank is None:
            if rank_check not in web_session:
                abort(401)
        elif not utils.has_role(required_rank, web_session.get(rank_check)):
            abort(401)

        return func(**kwargs)

    return wrapper


def route_wrapper(
    rule: str,
    *,
    methods: Iterable[str] | None = None,
    required_rank: Role | None = None,
) -> Callable[[RouteFunc], RouteFunc]:
    def wrapper(func: RouteFunc) -> RouteFunc:
        func = route_check_permission(func, required_rank)
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

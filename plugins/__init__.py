from __future__ import annotations

import glob
import importlib
from collections.abc import Awaitable, Callable, Iterable
from functools import wraps
from os.path import basename, dirname, isfile, join
from typing import TYPE_CHECKING, Optional

from sqlalchemy import select
from sqlalchemy.sql import Select

import databases.database as d
import utils
from database import Database
from models.room import Room
from typedefs import Role, RoomId

if TYPE_CHECKING:
    from models.message import Message
    from models.user import User

    CommandFunc = Callable[[Message], Awaitable[None]]
    HTMLPageFunc = Callable[[User, Room], Optional[Select]]
    RouteFunc = Callable[..., str]  # type: ignore[misc]


# --- Command logic and complementary decorators ---


class Command:
    _instances: dict[str, Command] = {}

    def __init__(  # pylint: disable=too-many-arguments
        self,
        func: CommandFunc,
        aliases: tuple[str, ...],
        helpstr: str,
        is_unlisted: bool,
        required_rank: Role,
        required_rank_editable: bool | str,
    ) -> None:
        self.name = func.__name__
        self.module = func.__module__
        self.callback = func
        self.aliases = (self.name,) + aliases
        self.helpstr = helpstr
        self.is_unlisted = is_unlisted
        self.required_rank = required_rank
        self.required_rank_editable = required_rank_editable
        self._instances[func.__name__] = self

    @property
    def splitted_aliases(self) -> dict[str, Command]:
        return {alias: self for alias in self.aliases}

    @classmethod
    def get_all_aliases(cls) -> dict[str, Command]:
        aliases: dict[str, Command] = {}
        for command in cls._instances.values():
            aliases.update(command.splitted_aliases)
        return aliases

    @classmethod
    def get_all_helpstrings(cls) -> dict[str, str]:
        helpstrings: dict[str, str] = {}
        for command in cls._instances.values():
            if command.helpstr and not command.is_unlisted:
                helpstrings[command.name] = command.helpstr
        return {k: helpstrings[k] for k in sorted(helpstrings)}

    @classmethod
    def get_rank_editable_commands(cls) -> set[str]:
        return {
            (
                v.required_rank_editable
                if isinstance(v.required_rank_editable, str)
                else f".{k}"
            )
            for k, v in cls._instances.items()
            if v.required_rank_editable is not False and k == v.name
        }


def command_check_permission(  # pylint: disable=too-many-arguments
    func: CommandFunc,
    required_rank: Role,
    allow_pm: bool | Role,
    required_rank_editable: bool | str,
    main_room_only: bool,
    parametrize_room: bool,
) -> CommandFunc:
    @wraps(func)
    async def wrapper(msg: Message) -> None:
        req_rank = required_rank

        if required_rank_editable is not False:
            roomid = ""
            if parametrize_room:
                roomid = msg.parametrized_room.roomid
            elif msg.room:
                roomid = msg.room.roomid

            if roomid:
                command = f".{func.__name__}"
                if isinstance(required_rank_editable, str):
                    command = required_rank_editable

                db = Database.open()
                with db.get_session() as session:
                    stmt = select(d.CustomPermissions.required_rank).filter_by(
                        roomid=roomid, command=command
                    )
                    custom_rank: Role | None = session.scalar(stmt)
                    if custom_rank:
                        req_rank = custom_rank

        if msg.room is None and isinstance(allow_pm, str):
            req_rank = allow_pm

        if main_room_only and not msg.user.has_role(req_rank, msg.conn.main_room):
            return

        if not allow_pm and msg.room is None:
            return

        if parametrize_room:
            if msg.user not in msg.parametrized_room.users or not msg.user.has_role(
                req_rank, msg.parametrized_room
            ):
                return
        elif msg.room is not None and not msg.user.has_role(req_rank, msg.room):
            return

        await func(msg)

    return wrapper


def command_wrapper(
    *,
    aliases: tuple[str, ...] = (),
    helpstr: str = "",
    is_unlisted: bool = False,
    required_rank: Role = "voice",
    allow_pm: bool | Role = True,
    required_rank_editable: bool | str = False,
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
        allow_pm (bool | Role): True if the command can be used in PM (and not only in a
            room). A role can be specified if using this command in PM should have a
            different required rank. Defaults to True.
        required_rank_editable (bool | str): Whether the default required rank should be
            editable on a per-room basis. A string can be used to group similar commands
            together. Defaults to False.
        main_room_only (bool): Whether the main room should be used to check if the user
            has relevant auth. Defaults to False.
        parametrize_room (bool): Allows room-dependent commands to be used in PM. See
            the docstring of `parametrize_room_wrapper`. Defaults to False.

    Returns:
        Callable[[CommandFunc], Command]: Wrapper.
    """

    def cls_wrapper(func: CommandFunc) -> Command:
        func = command_check_permission(
            func,
            required_rank,
            allow_pm,
            required_rank_editable,
            main_room_only,
            parametrize_room,
        )
        if parametrize_room:
            func = parametrize_room_wrapper(func)
        return Command(
            func, aliases, helpstr, is_unlisted, required_rank, required_rank_editable
        )

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


htmlpages: dict[str, tuple[HTMLPageFunc, str | None]] = {}


def htmlpage_check_permission(
    func: HTMLPageFunc, required_rank: Role | None, main_room_only: bool
) -> HTMLPageFunc:
    @wraps(func)
    def wrapper(user: User, room: Room) -> Select | None:
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
    pageid: str,
    *,
    aliases: tuple[str, ...] = (),
    required_rank: Role = "voice",
    allow_pm: bool | Role = True,
    delete_command: str | None = None,
    main_room_only: bool = False,
) -> Callable[[HTMLPageFunc], HTMLPageFunc]:
    # Register a command sending a link to the htmlpage
    async def cmd_func(msg: Message) -> None:
        room = msg.conn.main_room if main_room_only else msg.parametrized_room
        if allow_pm == "regularuser":
            await msg.reply_htmlpage(pageid, room)
        else:
            await msg.user.send_htmlpage(pageid, room)

    cmd_wrapper = command_wrapper(
        aliases=aliases,
        required_rank=required_rank,
        allow_pm=allow_pm,
        main_room_only=main_room_only,
        parametrize_room=not main_room_only,
    )

    cmd_func.__name__ = pageid
    cmd_wrapper(cmd_func)

    # Register the htmlpage
    req_rank = required_rank
    if isinstance(allow_pm, str):
        req_rank = allow_pm

    def wrapper(func: HTMLPageFunc) -> HTMLPageFunc:
        func = htmlpage_check_permission(func, req_rank, main_room_only)
        htmlpages[pageid] = func, delete_command
        return func

    return wrapper


# --- Module loading and post-loading objects ---


modules = glob.glob(join(dirname(__file__), "*.py"))

for f in modules:
    if isfile(f) and not f.endswith("__init__.py"):
        name = basename(f)[:-3]
        importlib.import_module("plugins." + name)

commands = Command.get_all_aliases()

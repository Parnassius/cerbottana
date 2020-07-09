from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Callable, Awaitable, List, Dict

from functools import wraps
import re

from room import Room
import utils

if TYPE_CHECKING:
    from connection import Connection

    PluginFunc = Callable[[Connection, Optional[str], str, str], Awaitable[None]]


class Plugin:
    _instances = dict()  # type: Dict[str, Plugin]

    def __init__(
        self,
        func: PluginFunc,
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
    def commands(self) -> Dict[str, Plugin]:
        return {alias: self for alias in self.aliases}

    @classmethod
    def get_all_commands(cls) -> Dict[str, Plugin]:
        d: Dict[str, Plugin] = {}
        for plugin in cls._instances.values():
            d.update(plugin.commands)
        return d

    @classmethod
    def get_all_helpstrings(cls) -> Dict[str, str]:
        d: Dict[str, str] = {}
        for plugin in cls._instances.values():
            if plugin.helpstr and not plugin.is_unlisted:
                d[plugin.name] = plugin.helpstr
        return {k: d[k] for k in sorted(d)}  # python 3.7+


def scope_checker(func: PluginFunc) -> PluginFunc:
    @wraps(func)
    async def scope_wrapper(
        conn: Connection, room: Optional[str], user: str, arg: str
    ) -> None:
        if room is not None and not utils.is_voice(user):
            return
        await func(conn, room, user, arg)

    return scope_wrapper


def plugin_wrapper(
    aliases: List[str] = [], helpstr: str = "", is_unlisted: bool = False
) -> Callable[[PluginFunc], Plugin]:
    def cls_wrapper(func: PluginFunc) -> Plugin:
        func = scope_checker(func)  # manual decorator binding
        return Plugin(func, aliases, helpstr, is_unlisted)

    return cls_wrapper


# Other plugin decorators
def parametrize_room(func: PluginFunc) -> PluginFunc:
    """
    Changes the syntax of a command depending on its context:
    (1) If it's used in PM, it requires to specify an additional parameter
        at the beginning of arg representing a roomid.
    (2) If it's used in a room, it automatically adds its roomid at the
        beginning of arg.
    
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
            arg = ",".join(args)
        else:  # (2) command used in PM: check perms
            if not arg:
                await conn.send_pm(user, "Specifica il nome della room.")
                return

            troom = re.sub(r"[^a-z0-9-]", "", arg.split(",")[0].lower())  # target room
            # this defaults to "", utils.to_room_id defaults to "lobby"

            if not troom:
                await conn.send_pm(user, "Specifica il nome della room.")
                return

            if (
                troom not in conn.rooms + conn.private_rooms  # bot in room?
                or utils.to_user_id(user) not in Room.get(troom).users  # user in room?
            ):
                # Send the same message for both errors to avoid leaking private rooms
                await conn.send_pm(user, "Sei nella room?")
                return
        await func(conn, room, user, arg)

    return wrapper

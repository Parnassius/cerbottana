from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Callable, List, Dict

if TYPE_CHECKING:
    from connection import Connection

from functools import wraps

import utils


class Plugin:
    _instances = dict()  # type: Dict[str, Plugin]

    def __init__(
        self,
        func: Callable,
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


def scope_checker(func: Callable) -> Callable:
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
) -> Callable:
    def cls_wrapper(func: Callable) -> Plugin:
        func = scope_checker(func)  # manual decorator binding
        return Plugin(func, aliases, helpstr, is_unlisted)

    return cls_wrapper

from typing import Callable, Dict, List
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
        setattr(self.callback, "helpstr", helpstr)  # enables aliases in '.help foo'
        self._instances[func.__name__] = self

    @property
    def commands(self) -> Dict[str, Callable]:
        return {alias: self.callback for alias in self.aliases}

    @classmethod
    def get_all_commands(cls) -> Dict[str, Callable]:
        d: Dict[str, Callable] = {}
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


def scope_checker(func):
    @wraps(func)
    async def scope_wrapper(self, room: str, user: str, arg: str):
        if room is not None and not utils.is_voice(user):
            return
        return await func(self, room, user, arg)

    return scope_wrapper


def plugin_wrapper(**kwargs):
    def cls_wrapper(func):
        func = scope_checker(func)  # manual decorator binding
        return Plugin(func, **kwargs)

    return cls_wrapper

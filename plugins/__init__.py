import glob
import importlib
from functools import wraps
from os.path import basename, dirname, isfile, join
from typing import TYPE_CHECKING, Any, Callable, Iterable, List, Optional, Tuple, Union

from flask import abort, session

import utils
from plugin_loader import Plugin

RouteFunc = Union[Callable[[], str], Callable[[str], str]]


routes = list()  # type: List[Tuple[RouteFunc, str, Optional[Iterable[str]]]]


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


modules = glob.glob(join(dirname(__file__), "*.py"))

for f in modules:
    if isfile(f) and not f.endswith("__init__.py"):
        name = basename(f)[:-3]
        importlib.import_module("plugins." + name)

plugins = Plugin.get_all_commands()

from __future__ import annotations

import glob
import importlib
from collections.abc import Awaitable, Callable
from os.path import basename, dirname, isfile, join
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from connection import Connection

    InitTaskFunc = Callable[[Connection], Awaitable[None]]


init_tasks: list[tuple[int, InitTaskFunc, bool]] = []


def init_task_wrapper(
    priority: int = 3, skip_unittesting: bool = False
) -> Callable[[InitTaskFunc], InitTaskFunc]:
    def wrapper(func: InitTaskFunc) -> InitTaskFunc:
        init_tasks.append((priority, func, skip_unittesting))
        return func

    return wrapper


modules = glob.glob(join(dirname(__file__), "*.py"))

for f in modules:
    if isfile(f) and not f.endswith("__init__.py"):
        name = basename(f)[:-3]
        importlib.import_module("tasks." + name)

from __future__ import annotations

import glob
import importlib
from os.path import basename, dirname, isfile, join
from typing import TYPE_CHECKING, Awaitable, Callable, List, Tuple

if TYPE_CHECKING:
    from connection import Connection

    InitTaskFunc = Callable[[Connection], Awaitable[None]]

    RecurringTaskFunc = Callable[[Connection], Awaitable[None]]


init_tasks: List[Tuple[int, InitTaskFunc, bool]] = []


def init_task_wrapper(
    priority: int = 3, skip_unittesting: bool = False
) -> Callable[[InitTaskFunc], InitTaskFunc]:
    def wrapper(func: InitTaskFunc) -> InitTaskFunc:
        init_tasks.append((priority, func, skip_unittesting))
        return func

    return wrapper


recurring_tasks: List[InitTaskFunc] = []


def recurring_task_wrapper() -> Callable[[RecurringTaskFunc], RecurringTaskFunc]:
    def wrapper(func: RecurringTaskFunc) -> RecurringTaskFunc:
        recurring_tasks.append(func)
        return func

    return wrapper


modules = glob.glob(join(dirname(__file__), "*.py"))

for f in modules:
    if isfile(f) and not f.endswith("__init__.py"):
        name = basename(f)[:-3]
        importlib.import_module("tasks." + name)

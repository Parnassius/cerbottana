from __future__ import annotations

import importlib
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cerbottana.connection import Connection

    InitTaskFunc = Callable[[Connection], Coroutine[None, None, None]]
    RecurringTaskFunc = Callable[[Connection], Coroutine[None, None, None]]


init_tasks: list[tuple[int, InitTaskFunc]] = []


def init_task_wrapper(*, priority: int = 3) -> Callable[[InitTaskFunc], InitTaskFunc]:
    def wrapper(func: InitTaskFunc) -> InitTaskFunc:
        init_tasks.append((priority, func))
        return func

    return wrapper


background_tasks: list[RecurringTaskFunc] = []


def background_task_wrapper() -> Callable[[RecurringTaskFunc], RecurringTaskFunc]:
    def wrapper(func: RecurringTaskFunc) -> RecurringTaskFunc:
        background_tasks.append(func)
        return func

    return wrapper


modules = Path(__file__).parent.glob("*.py")

for f in modules:
    if f.is_file() and f.name != "__init__.py":
        name = f.stem
        importlib.import_module(f".{name}", __name__)

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Awaitable, List

if TYPE_CHECKING:
    from connection import Connection

    InittaskFunc = Callable[[Connection], Awaitable[None]]

from os.path import dirname, basename, isfile, join
import glob
import importlib


inittasks = list()  # type: List[InittaskFunc]


def inittask_wrapper() -> Callable[[InittaskFunc], InittaskFunc]:
    def cls_wrapper(func: InittaskFunc) -> InittaskFunc:
        inittasks.append(func)
        return func

    return cls_wrapper


modules = glob.glob(join(dirname(__file__), "*.py"))

for f in modules:
    if isfile(f) and not f.endswith("__init__.py"):
        name = basename(f)[:-3]
        importlib.import_module("inittasks." + name)

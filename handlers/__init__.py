from __future__ import annotations

import glob
import importlib
from os.path import basename, dirname, isfile, join
from typing import TYPE_CHECKING, Awaitable, Callable, Dict, List

if TYPE_CHECKING:
    from connection import Connection

    HandlerFunc = Callable[[Connection, str, str], Awaitable[None]]


handlers: Dict[str, List[HandlerFunc]] = {}


def handler_wrapper(message_types: List[str]) -> Callable[[HandlerFunc], HandlerFunc]:
    def cls_wrapper(func: HandlerFunc) -> HandlerFunc:
        for message_type in message_types:
            if not message_type in handlers:
                handlers[message_type] = []
            handlers[message_type].append(func)
        return func

    return cls_wrapper


modules = glob.glob(join(dirname(__file__), "*.py"))

for f in modules:
    if isfile(f) and not f.endswith("__init__.py"):
        name = basename(f)[:-3]
        importlib.import_module("handlers." + name)

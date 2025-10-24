from __future__ import annotations

import importlib
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from functools import wraps
from pathlib import Path

from cerbottana.models.protocol_message import ProtocolMessage

HandlerFunc = Callable[[ProtocolMessage], Coroutine[None, None, None]]


@dataclass
class Handler:
    callback: HandlerFunc
    required_parameters: int | None


handlers: dict[str, list[Handler]] = {}


def handler_wrapper(
    message_types: list[str], *, required_parameters: int | None = None
) -> Callable[[HandlerFunc], HandlerFunc]:
    def cls_wrapper(func: HandlerFunc) -> HandlerFunc:
        if required_parameters:
            func = check_required_parameters(func, required_parameters)
        for message_type in message_types:
            if message_type not in handlers:
                handlers[message_type] = []
            handlers[message_type].append(Handler(func, required_parameters))
        return func

    return cls_wrapper


def check_required_parameters(
    func: HandlerFunc, required_parameters: int
) -> HandlerFunc:
    @wraps(func)
    async def wrapper(msg: ProtocolMessage) -> None:
        if len(msg.params) < required_parameters:
            return
        await func(msg)

    return wrapper


modules = Path(__file__).parent.glob("*.py")

for f in modules:
    if f.is_file() and f.name != "__init__.py":
        name = f.stem
        importlib.import_module(f".{name}", __name__)

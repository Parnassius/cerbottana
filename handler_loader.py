from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Awaitable, List, Dict

if TYPE_CHECKING:
    from connection import Connection

    HandlerFunc = Callable[[Connection, str, str], Awaitable[None]]


class Handler:
    _instances = dict()  # type: Dict[str, Handler]

    def __init__(self, func: HandlerFunc, message_types: List[str]) -> None:
        self.callback = func
        self.message_types = message_types
        self._instances[func.__name__] = self

    @property
    def handlers(self) -> Dict[str, HandlerFunc]:
        return {message_type: self.callback for message_type in self.message_types}

    @classmethod
    def get_all_handlers(cls) -> Dict[str, List[HandlerFunc]]:
        d: Dict[str, List[HandlerFunc]] = {}
        for handler in cls._instances.values():
            for message_type in handler.handlers:
                if not message_type in d:
                    d[message_type] = []
                d[message_type].append(handler.handlers[message_type])
        return d


def handler_wrapper(message_types: List[str]) -> Callable[[HandlerFunc], Handler]:
    def cls_wrapper(func: HandlerFunc) -> Handler:
        return Handler(func, message_types)

    return cls_wrapper

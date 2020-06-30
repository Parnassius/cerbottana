from typing import Callable, Dict, List
from functools import wraps

import utils


class Handler:
    _instances = dict()  # type: Dict[str, Handler]

    def __init__(
        self,
        func: Callable,
        message_types: List[str],
    ) -> None:
        self.callback = func
        self.message_types = message_types
        self._instances[func.__name__] = self

    @property
    def handlers(self) -> Dict[str, Callable]:
        return {message_type: self.callback for message_type in self.message_types}

    @classmethod
    def get_all_handlers(cls) -> Dict[str, List[Callable]]:
        d: Dict[str, List[Callable]] = {}
        for handler in cls._instances.values():
            for message_type in handler.handlers:
                if not message_type in d:
                    d[message_type] = []
                d[message_type].append(handler.handlers[message_type])
        return d


def handler_wrapper(message_types):
    def cls_wrapper(func):
        return Handler(func, message_types)

    return cls_wrapper

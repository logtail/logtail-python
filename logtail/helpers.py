# coding: utf-8
from __future__ import print_function, unicode_literals
from types import TracebackType
from typing import Any, Optional


class LogtailContext(object):
    def __init__(self) -> None:
        self.extras: list[dict[str, dict[str, Any]]] = []

    def context(self, *args: Any, **kwargs: dict[str, Any]) -> 'LogtailContext':
        if args:
            raise ValueError(
                'All contexts must be passed by name as keyword arguments'
            )
        for key, val in kwargs.items():
            if not isinstance(val, dict):
                raise ValueError(
                    'All contexts must be dictionaries: %s' % key
                )
        self.extras.append(kwargs)
        return self

    def __call__(self, *args: Any, **kwargs: dict[str, Any]) -> 'LogtailContext':
        return self.context(*args, **kwargs)

    def __enter__(self) -> 'LogtailContext':
        return self

    def __exit__(self, type_: Optional[type[BaseException]], value: Optional[BaseException], traceback: Optional[TracebackType]) -> None:
        self.extras.pop()

    def exists(self) -> bool:
        return bool(self.extras)

    def collapse(self) -> dict[str, dict[str, Any]]:
        x: dict[str, dict[str, Any]] = {}
        for contexts in self.extras:
            for name, data in contexts.items():
                x.setdefault(name, {}).update(data)
        return x


DEFAULT_CONTEXT = LogtailContext()

# coding: utf-8
from __future__ import print_function, unicode_literals


class LogtailContext(object):
    def __init__(self):
        self.extras = []

    def context(self, *args, **kwargs):
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

    def __call__(self, *args, **kwargs):
        return self.context(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        if type_ is not None:
            return False
        self.extras.pop()
        return self

    def exists(self):
        return bool(self.extras)

    def collapse(self):
        x = {}
        for contexts in self.extras:
            for name, data in contexts.items():
                x.setdefault(name, {}).update(data)
        return x


DEFAULT_CONTEXT = LogtailContext()

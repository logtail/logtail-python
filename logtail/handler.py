# coding: utf-8
from __future__ import print_function, unicode_literals
import logging
import json
import os
import weakref
from typing import Any, Optional

from .compat import queue
from .helpers import DEFAULT_CONTEXT, LogtailContext
from .flusher import FlushWorker, TransportFrame, in_flush_worker
from .uploader import Uploader
from .frame import create_frame

DEFAULT_HOST = 'in.logs.betterstack.com'
DEFAULT_BUFFER_CAPACITY = 1000
DEFAULT_FLUSH_INTERVAL = 1
DEFAULT_CHECK_INTERVAL = 0.1
DEFAULT_RAISE_EXCEPTIONS = False
DEFAULT_DROP_EXTRA_EVENTS = True
DEFAULT_INCLUDE_EXTRA_ATTRIBUTES = True
DEFAULT_TIMEOUT = 30

_handlers: 'weakref.WeakSet[LogtailHandler]' = weakref.WeakSet()


class LogtailHandler(logging.Handler):
    def __init__(self,
                 source_token: str,
                 host: str = DEFAULT_HOST,
                 buffer_capacity: int = DEFAULT_BUFFER_CAPACITY,
                 flush_interval: float = DEFAULT_FLUSH_INTERVAL,
                 check_interval: float = DEFAULT_CHECK_INTERVAL,
                 raise_exceptions: bool = DEFAULT_RAISE_EXCEPTIONS,
                 drop_extra_events: bool = DEFAULT_DROP_EXTRA_EVENTS,
                 include_extra_attributes: bool = DEFAULT_INCLUDE_EXTRA_ATTRIBUTES,
                 context: LogtailContext = DEFAULT_CONTEXT,
                 timeout: float = DEFAULT_TIMEOUT,
                 level: int = logging.NOTSET) -> None:
        super(LogtailHandler, self).__init__(level=level)
        self.source_token = source_token
        if host.startswith('https://') or host.startswith('http://'):
            self.host = host
        else:
            self.host = "https://" + host
        self.context = context
        self.pipe: 'queue.Queue[dict[str, Any]]' = queue.Queue(maxsize=buffer_capacity)
        self.uploader = Uploader(self.source_token, self.host, timeout)
        self.drop_extra_events = drop_extra_events
        self.include_extra_attributes = include_extra_attributes
        self.buffer_capacity = buffer_capacity
        self.flush_interval = flush_interval
        self.check_interval = check_interval
        self.raise_exceptions = raise_exceptions
        self.dropcount = 0
        # Do not initialize the flush thread yet because it causes issues on Render.
        self.flush_thread: Optional[FlushWorker] = None
        _handlers.add(self)

    def ensure_flush_thread_alive(self) -> None:
        if self.flush_thread and self.flush_thread.is_alive():
            return

        self.flush_thread = FlushWorker(
            self.uploader,
            self.pipe,
            self.buffer_capacity,
            self.flush_interval,
            self.check_interval,
        )
        self.flush_thread.start()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.ensure_flush_thread_alive()

            message = self.format(record)
            frame = create_frame(record, message, self.context, include_extra_attributes=self.include_extra_attributes)
            serializable_frame = json.loads(json.dumps(frame, default=str))
            transport = in_flush_worker()
            if transport:
                serializable_frame = TransportFrame(serializable_frame)
            try:
                # The flush worker must never block on its own queue, so its records are dropped when full.
                self.pipe.put(serializable_frame, block=(not self.drop_extra_events) and not transport)
            except queue.Full:
                # Only raised when not blocking, which means that extra events
                # should be dropped.
                self.dropcount += 1
        except Exception as e:
            if self.raise_exceptions:
                raise e

    def flush(self) -> None:
        if self.flush_thread and self.flush_thread.is_alive():
             self.flush_thread.flush()

    def _reset_after_fork(self) -> None:
        # A forked child inherits the parent's queue with whatever was still buffered in it,
        # a flush thread object whose thread does not exist in the child, and an HTTP session
        # whose socket it shares with the parent, so it starts over with fresh ones.
        self.pipe = queue.Queue(maxsize=self.buffer_capacity)
        self.flush_thread = None
        self.uploader = Uploader(self.source_token, self.host, self.uploader.timeout)


def _reset_handlers_after_fork() -> None:
    for handler in _handlers:
        handler._reset_after_fork()


if hasattr(os, 'register_at_fork'):
    os.register_at_fork(after_in_child=_reset_handlers_after_fork)

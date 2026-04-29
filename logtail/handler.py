# coding: utf-8
from __future__ import print_function, unicode_literals
import logging
import json
import os

from .compat import queue
from .helpers import DEFAULT_CONTEXT
from .flusher import FlushWorker
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
DEFAULT_FLUSH_TIMEOUT = 30


# urllib3 emits per-request DEBUG logs from inside its connection pool.
# The FlushWorker uses requests/urllib3 to POST to BetterStack — so any
# debug() call from urllib3 happens on the FlushWorker thread. When
# logging.shutdown() / logging.config.dictConfig() runs (e.g. triggered
# at import time by libraries like pymilvus), the calling thread holds
# logging._lock while iterating handlers and invoking flush(); the
# FlushWorker's debug() call would need the same lock and the two threads
# deadlock. Quieting urllib3 to WARNING keeps the debug() calls cheap
# no-ops and avoids the lock contention entirely. Set
# LOGTAIL_KEEP_URLLIB3_LOGS=1 to opt out.
if os.getenv('LOGTAIL_KEEP_URLLIB3_LOGS', '').lower() not in ('1', 'true', 'yes'):
    _urllib3_logger = logging.getLogger('urllib3')
    if _urllib3_logger.level == logging.NOTSET or _urllib3_logger.level < logging.WARNING:
        _urllib3_logger.setLevel(logging.WARNING)


class LogtailHandler(logging.Handler):
    def __init__(self,
                 source_token,
                 host=DEFAULT_HOST,
                 buffer_capacity=DEFAULT_BUFFER_CAPACITY,
                 flush_interval=DEFAULT_FLUSH_INTERVAL,
                 check_interval=DEFAULT_CHECK_INTERVAL,
                 raise_exceptions=DEFAULT_RAISE_EXCEPTIONS,
                 drop_extra_events=DEFAULT_DROP_EXTRA_EVENTS,
                 include_extra_attributes=DEFAULT_INCLUDE_EXTRA_ATTRIBUTES,
                 context=DEFAULT_CONTEXT,
                 timeout=DEFAULT_TIMEOUT,
                 flush_timeout=DEFAULT_FLUSH_TIMEOUT,
                 level=logging.NOTSET):
        super(LogtailHandler, self).__init__(level=level)
        self.source_token = source_token
        if host.startswith('https://') or host.startswith('http://'):
            self.host = host
        else:
            self.host = "https://" + host
        self.context = context
        self.pipe = queue.Queue(maxsize=buffer_capacity)
        self.uploader = Uploader(self.source_token, self.host, timeout)
        self.drop_extra_events = drop_extra_events
        self.include_extra_attributes = include_extra_attributes
        self.buffer_capacity = buffer_capacity
        self.flush_interval = flush_interval
        self.check_interval = check_interval
        self.raise_exceptions = raise_exceptions
        self.flush_timeout = flush_timeout
        self.dropcount = 0
        # Do not initialize the flush thread yet because it causes issues on Render.
        self.flush_thread = None

    def ensure_flush_thread_alive(self):
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

    def emit(self, record):
        try:
            self.ensure_flush_thread_alive()

            message = self.format(record)
            frame = create_frame(record, message, self.context, include_extra_attributes=self.include_extra_attributes)
            serializable_frame = json.loads(json.dumps(frame, default=str))
            try:
                self.pipe.put(serializable_frame, block=(not self.drop_extra_events))
            except queue.Full:
                # Only raised when not blocking, which means that extra events
                # should be dropped.
                self.dropcount += 1
        except Exception as e:
            if self.raise_exceptions:
                raise e

    def flush(self):
        if self.flush_thread and self.flush_thread.is_alive():
             self.flush_thread.flush(timeout=self.flush_timeout)

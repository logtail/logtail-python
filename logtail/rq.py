# coding: utf-8
from __future__ import print_function, unicode_literals
import logging
from typing import Any

import rq

from .handler import LogtailHandler


class Worker(rq.Worker):
    """An RQ worker that sends buffered log records after every job.

    RQ runs each job in a forked work horse and ends it with os._exit(), which skips the
    interpreter shutdown that would otherwise let LogtailHandler flush. Use it with
    `rq worker --worker-class logtail.rq.Worker` or `RQ = {"WORKER_CLASS": "logtail.rq.Worker"}`
    in django-rq.
    """

    # rq 1.x and 2.x call perform_job(job, queue), rq 3.0 and later perform_job(job, queue, execution).
    def perform_job(self, *args: Any, **kwargs: Any) -> bool:
        try:
            return super(Worker, self).perform_job(*args, **kwargs)
        finally:
            for handler in _logtail_handlers():
                handler.flush()


def _logtail_handlers() -> set[LogtailHandler]:
    loggers = [logging.getLogger()] + [logger for logger in logging.Logger.manager.loggerDict.values() if isinstance(logger, logging.Logger)]
    return {handler for logger in loggers for handler in logger.handlers if isinstance(handler, LogtailHandler)}

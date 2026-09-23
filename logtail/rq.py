# coding: utf-8
from __future__ import print_function, unicode_literals
import logging

import rq

from .handler import LogtailHandler


class Worker(rq.Worker):
    """An RQ worker that sends buffered log records after every job.

    RQ runs each job in a forked work horse and ends it with os._exit(), which skips the
    interpreter shutdown that would otherwise let LogtailHandler flush. Use it with
    `rq worker --worker-class logtail.rq.Worker` or `RQ = {"WORKER_CLASS": "logtail.rq.Worker"}`
    in django-rq.
    """

    def perform_job(self, job, queue):
        try:
            return super(Worker, self).perform_job(job, queue)
        finally:
            for handler in _logtail_handlers():
                handler.flush()


def _logtail_handlers():
    loggers = [logging.getLogger()] + [logger for logger in logging.Logger.manager.loggerDict.values() if isinstance(logger, logging.Logger)]
    return {handler for logger in loggers for handler in logger.handlers if isinstance(handler, LogtailHandler)}

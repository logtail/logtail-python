# coding: utf-8
from __future__ import print_function, unicode_literals
import logging
import json

from .helpers import DEFAULT_CONTEXT
from .frame import create_frame


class LogtailFormatter(logging.Formatter):
    def __init__(self,
                 context=DEFAULT_CONTEXT,
                 json_default=None,
                 json_encoder=None):
        self.context = context
        self.json_default = json_default
        self.json_encoder = json_encoder

    def format(self, record):
        # Because the formatter does not have an underlying format string for
        # which `extra` may be used to substitute arguments (see
        # https://docs.python.org/2/library/logging.html#logging.debug ), we
        # augment the log frame with all of the entries in extra.
        frame = create_frame(record, record.getMessage(), self.context, include_extra_attributes=True)
        return json.dumps(frame, default=self.json_default, cls=self.json_encoder)

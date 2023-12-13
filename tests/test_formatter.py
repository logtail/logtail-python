# coding: utf-8
from __future__ import print_function, unicode_literals
import mock
import time
import threading
import json
import unittest
import pdb
import logging

import logtail
from logtail.formatter import LogtailFormatter
from logtail.helpers import LogtailContext


class TestLogtailFormatter(unittest.TestCase):
    def setUp(self):
        self.context = LogtailContext()
        self.customer = {'id': '1'}
        self.order = {'id': '1234', 'amount': 200, 'item': '#19849'}

    def _check_and_get_line(self, loglines):
        self.assertEqual(len(loglines), 1)
        return loglines[0]

    def test_format_emits_single_line(self):
        formatter = logtail.LogtailFormatter(context=self.context)
        logger, loglines = logger_and_lines(formatter)
        self.assertFalse(loglines)

        logger.info('Hello\n\n\n\n\n\nWorld')
        line = self._check_and_get_line(loglines)
        self.assertEqual(len(line.split('\n')), 1)

    def test_format_creates_json_serialized_frame_with_context(self):
        formatter = logtail.LogtailFormatter(context=self.context)
        logger, loglines = logger_and_lines(formatter)
        self.assertFalse(loglines)

        with self.context(customer=self.customer):
            logger.info('Received order id=%s', self.order['id'], extra={'order': self.order})

        line = self._check_and_get_line(loglines)
        frame = json.loads(line)
        self.assertEqual(frame['message'], 'Received order id=%s' % self.order['id'])
        self.assertEqual(frame['order'], self.order)
        self.assertEqual(frame['context']['customer'], self.customer)

    def test_format_collapses_context(self):
        formatter = logtail.LogtailFormatter(context=self.context)
        logger, loglines = logger_and_lines(formatter)
        self.assertFalse(loglines)

        with self.context(customer=self.customer):
            with self.context(customer={'trusted': True}):
                logger.info('Received an order', extra={'order': self.order})

        line = self._check_and_get_line(loglines)
        frame = json.loads(line)
        self.assertEqual(frame['message'], 'Received an order')
        self.assertEqual(frame['order'], self.order)
        self.assertEqual(frame['context']['customer'], {'id': self.customer['id'], 'trusted': True})


class ListHandler(logging.Handler):
    """ Accumulates all log lines in a list for testing purposes. """
    def __init__(self, *args, **kwargs):
        super(ListHandler, self).__init__(*args, **kwargs)
        self.lines = []

    def emit(self, record):
        logline = self.format(record)
        self.lines.append(logline)

def logger_and_lines(formatter, name=__name__):
    """ Helper for more easily writing formatter tests. """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    handler = ListHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger, handler.lines

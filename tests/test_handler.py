# coding: utf-8
from __future__ import print_function, unicode_literals
import mock
import time
import threading
import unittest2
import logging

from logtail.handler import LogtailHandler


class TestLogtailHandler(unittest2.TestCase):
    source_token = 'dummy_source_token'
    host = 'dummy_host'

    @mock.patch('logtail.handler.FlushWorker')
    def test_handler_creates_uploader_from_args(self, MockWorker):
        handler = LogtailHandler(source_token=self.source_token, host=self.host)
        self.assertEqual(handler.uploader.source_token, self.source_token)
        self.assertEqual(handler.uploader.host, self.host)

    @mock.patch('logtail.handler.FlushWorker')
    def test_handler_creates_pipe_from_args(self, MockWorker):
        buffer_capacity = 9
        flush_interval = 1
        handler = LogtailHandler(
            source_token=self.source_token,
            buffer_capacity=buffer_capacity,
            flush_interval=flush_interval
        )
        self.assertEqual(handler.pipe._maxsize, buffer_capacity)

    @mock.patch('logtail.handler.FlushWorker')
    def test_handler_creates_and_starts_worker_from_args(self, MockWorker):
        buffer_capacity = 9
        flush_interval = 9
        handler = LogtailHandler(source_token=self.source_token, buffer_capacity=buffer_capacity, flush_interval=flush_interval)
        MockWorker.assert_called_with(
            handler.uploader,
            handler.pipe,
            buffer_capacity,
            flush_interval
        )
        self.assertTrue(handler.flush_thread.start.called)

    @mock.patch('logtail.handler.FlushWorker')
    def test_emit_starts_thread_if_not_alive(self, MockWorker):
        handler = LogtailHandler(source_token=self.source_token)
        self.assertTrue(handler.flush_thread.start.call_count, 1)
        handler.flush_thread.is_alive = mock.Mock(return_value=False)

        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        logger.critical('hello')

        self.assertEqual(handler.flush_thread.start.call_count, 2)

    @mock.patch('logtail.handler.FlushWorker')
    def test_emit_drops_records_if_configured(self, MockWorker):
        buffer_capacity = 1
        handler = LogtailHandler(
            source_token=self.source_token,
            buffer_capacity=buffer_capacity,
            drop_extra_events=True
        )

        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        logger.critical('hello')
        logger.critical('goodbye')

        log_entry = handler.pipe.get()
        self.assertEqual(log_entry['message'], 'hello')
        self.assertTrue(handler.pipe.empty())
        self.assertEqual(handler.dropcount, 1)

    @mock.patch('logtail.handler.FlushWorker')
    def test_emit_does_not_drop_records_if_configured(self, MockWorker):
        buffer_capacity = 1
        handler = LogtailHandler(
            source_token=self.source_token,
            buffer_capacity=buffer_capacity,
            drop_extra_events=False
        )

        def consumer(q):
            while True:
                if q.full():
                    while not q.empty():
                        _ = q.get(block=True)
                time.sleep(.2)

        t = threading.Thread(target=consumer, args=(handler.pipe,))
        t.daemon = True

        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        logger.critical('hello')

        self.assertTrue(handler.pipe.full())
        t.start()
        logger.critical('goodbye')
        logger.critical('goodbye2')

        self.assertEqual(handler.dropcount, 0)

    @mock.patch('logtail.handler.FlushWorker')
    def test_error_suppression(self, MockWorker):
        buffer_capacity = 1
        handler = LogtailHandler(
            source_token=self.source_token,
            buffer_capacity=buffer_capacity,
            raise_exceptions=True
        )

        handler.pipe = mock.MagicMock(put=mock.Mock(side_effect=ValueError))

        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)

        with self.assertRaises(ValueError):
            logger.critical('hello')

        handler.raise_exceptions = False
        logger.critical('hello')

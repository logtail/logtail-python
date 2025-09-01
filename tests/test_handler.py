# coding: utf-8
from __future__ import print_function, unicode_literals
import mock
import time
import threading
import unittest
import logging

from unittest.mock import patch

from logtail import LogtailHandler, context
from logtail.handler import FlushWorker

class TestLogtailHandler(unittest.TestCase):
    source_token = 'dummy_source_token'
    host = 'dummy_host'

    @patch('logtail.handler.FlushWorker')
    def test_handler_creates_uploader_from_args(self, MockWorker):
        handler = LogtailHandler(source_token=self.source_token, host=self.host)
        self.assertEqual(handler.uploader.source_token, self.source_token)
        self.assertEqual(handler.uploader.host, "https://" + self.host)
        
    @patch('logtail.handler.FlushWorker')
    def test_handler_passes_timeout_to_uploader(self, MockWorker):
        # Test default timeout
        handler = LogtailHandler(source_token=self.source_token, host=self.host)
        self.assertEqual(handler.uploader.timeout, 30)
        
        # Test custom timeout
        handler = LogtailHandler(source_token=self.source_token, host=self.host, timeout=10)
        self.assertEqual(handler.uploader.timeout, 10)

    @patch('logtail.handler.FlushWorker')
    def test_handler_creates_pipe_from_args(self, MockWorker):
        buffer_capacity = 9
        flush_interval = 1
        handler = LogtailHandler(
            source_token=self.source_token,
            buffer_capacity=buffer_capacity,
            flush_interval=flush_interval
        )
        self.assertTrue(handler.pipe.empty())

    @patch('logtail.handler.FlushWorker')
    def test_handler_creates_and_starts_worker_from_args_after_first_log(self, MockWorker):
        buffer_capacity = 9
        flush_interval = 9
        check_interval = 4
        handler = LogtailHandler(source_token=self.source_token, buffer_capacity=buffer_capacity, flush_interval=flush_interval, check_interval=check_interval)

        self.assertFalse(MockWorker.called)

        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        logger.critical('hello')

        MockWorker.assert_called_with(
            handler.uploader,
            handler.pipe,
            buffer_capacity,
            flush_interval,
            check_interval,
        )
        self.assertEqual(handler.flush_thread.start.call_count, 1)

    @patch('logtail.handler.FlushWorker')
    def test_emit_starts_thread_if_not_alive(self, MockWorker):
        handler = LogtailHandler(source_token=self.source_token)

        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        logger.critical('hello')

        self.assertEqual(handler.flush_thread.start.call_count, 1)
        handler.flush_thread.is_alive = mock.Mock(return_value=False)

        logger.critical('hello')

        self.assertEqual(handler.flush_thread.start.call_count, 2)

    @patch('logtail.handler.FlushWorker')
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

    @patch('logtail.handler.FlushWorker')
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

    @patch('logtail.handler.FlushWorker')
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

    @patch('logtail.handler.FlushWorker')
    def test_can_send_unserializable_extra_data(self, MockWorker):
        buffer_capacity = 1
        handler = LogtailHandler(
            source_token=self.source_token,
            buffer_capacity=buffer_capacity
        )

        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        logger.info('hello', extra={'data': {'unserializable': UnserializableObject()}})

        log_entry = handler.pipe.get()

        self.assertEqual(log_entry['message'], 'hello')
        self.assertRegex(log_entry['data']['unserializable'], r'^<tests\.test_handler\.UnserializableObject object at 0x[0-f]+>$')
        self.assertTrue(handler.pipe.empty())

    @patch('logtail.handler.FlushWorker')
    def test_can_send_unserializable_context(self, MockWorker):
        buffer_capacity = 1
        handler = LogtailHandler(
            source_token=self.source_token,
            buffer_capacity=buffer_capacity
        )

        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        with context(data={'unserializable': UnserializableObject()}):
            logger.info('hello')

        log_entry = handler.pipe.get()

        self.assertEqual(log_entry['message'], 'hello')
        self.assertRegex(log_entry['context']['data']['unserializable'], r'^<tests\.test_handler\.UnserializableObject object at 0x[0-f]+>$')
        self.assertTrue(handler.pipe.empty())

    @patch('logtail.handler.FlushWorker')
    def test_can_send_circular_dependency_in_extra_data(self, MockWorker):
        buffer_capacity = 1
        handler = LogtailHandler(
            source_token=self.source_token,
            buffer_capacity=buffer_capacity
        )

        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        circular_dependency = {'egg': {}}
        circular_dependency['egg']['chicken'] = circular_dependency
        logger.info('hello', extra={'data': circular_dependency})

        log_entry = handler.pipe.get()

        self.assertEqual(log_entry['message'], 'hello')
        self.assertEqual(log_entry['data']['egg']['chicken'], "<omitted circular reference>")
        self.assertTrue(handler.pipe.empty())

    @patch('logtail.handler.FlushWorker')
    def test_can_have_multiple_instance_of_same_string_in_extra_data(self, MockWorker):
        buffer_capacity = 1
        handler = LogtailHandler(
            source_token=self.source_token,
            buffer_capacity=buffer_capacity
        )

        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        test_string = 'this is a test string'
        logger.info('hello', extra={'test1': test_string, 'test2': test_string})

        log_entry = handler.pipe.get()

        self.assertEqual(log_entry['message'], 'hello')
        self.assertEqual(log_entry['test1'], 'this is a test string')
        self.assertEqual(log_entry['test2'], 'this is a test string')
        self.assertTrue(handler.pipe.empty())

    @patch('logtail.handler.FlushWorker')
    def test_can_have_multiple_instance_of_same_array_in_extra_data(self, MockWorker):
        buffer_capacity = 1
        handler = LogtailHandler(
            source_token=self.source_token,
            buffer_capacity=buffer_capacity
        )

        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        test_array = ['this is a test string']
        logger.info('hello', extra={'test1': test_array, 'test2': test_array})

        log_entry = handler.pipe.get()

        self.assertEqual(log_entry['message'], 'hello')
        self.assertEqual(log_entry['test1'], ['this is a test string'])
        self.assertEqual(log_entry['test2'], ['this is a test string'])
        self.assertTrue(handler.pipe.empty())

    @patch('logtail.handler.FlushWorker')
    def test_can_send_circular_dependency_in_context(self, MockWorker):
        buffer_capacity = 1
        handler = LogtailHandler(
            source_token=self.source_token,
            buffer_capacity=buffer_capacity
        )

        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        circular_dependency = {'egg': {}}
        circular_dependency['egg']['chicken'] = circular_dependency
        with context(data=circular_dependency):
            logger.info('hello')

        log_entry = handler.pipe.get()

        self.assertEqual(log_entry['message'], 'hello')
        self.assertEqual(log_entry['context']['data']['egg']['chicken']['egg'], "<omitted circular reference>")
        self.assertTrue(handler.pipe.empty())


class UnserializableObject(object):
    """ Because this is a custom class, it cannot be serialized into JSON. """

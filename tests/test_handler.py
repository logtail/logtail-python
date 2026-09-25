# coding: utf-8
from __future__ import print_function, unicode_literals
import mock
import os
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
    def test_handler_stores_flush_timeout(self, MockWorker):
        # Default
        handler = LogtailHandler(source_token=self.source_token, host=self.host)
        self.assertEqual(handler.flush_timeout, 30)
        # Custom
        handler = LogtailHandler(source_token=self.source_token, host=self.host, flush_timeout=2)
        self.assertEqual(handler.flush_timeout, 2)
        # Explicit None disables the timeout (legacy unbounded wait)
        handler = LogtailHandler(source_token=self.source_token, host=self.host, flush_timeout=None)
        self.assertIsNone(handler.flush_timeout)

    @patch('logtail.handler.FlushWorker')
    def test_handler_passes_flush_timeout_to_worker(self, MockWorker):
        handler = LogtailHandler(source_token=self.source_token, host=self.host, flush_timeout=7)
        # Trigger flush_thread creation by emitting once.
        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        logger.critical('hello')
        # The mocked FlushWorker is alive by default; flush() forwards timeout.
        handler.flush()
        handler.flush_thread.flush.assert_called_with(timeout=7)

    @patch('logtail.handler.print', create=True)
    @patch('logtail.handler.FlushWorker')
    def test_flush_reports_giving_up(self, MockWorker, mock_print):
        handler = LogtailHandler(source_token=self.source_token, host=self.host, flush_timeout=3)
        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        logger.critical('hello')
        handler.flush_thread.flush.return_value = False

        handler.flush()

        mock_print.assert_called_once_with('Gave up waiting for Better Stack uploads after 3s, logs are still buffered')

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

    @patch('logtail.handler.FlushWorker')
    def test_forked_child_starts_with_a_fresh_queue_thread_and_session(self, MockWorker):
        handler = LogtailHandler(source_token=self.source_token)
        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.addHandler(handler)
        logger.critical('queued in the parent')
        uploader = handler.uploader
        parent_session = uploader.session

        pid = os.fork()
        if pid == 0:
            # The child gets its own session, but never resolves proxy settings again: on macOS
            # that means SystemConfiguration, which refuses to run in a forked child.
            fresh = (handler.pipe.empty() and handler.flush_thread is None and handler.uploader is uploader
                     and uploader.session is not parent_session and uploader.session.trust_env is False)
            os._exit(0 if fresh else 1)
        _, status = os.waitpid(pid, 0)

        self.assertEqual(os.waitstatus_to_exitcode(status), 0)
        self.assertEqual(handler.pipe.get(block=False)['message'], 'queued in the parent')

    def test_flush_returns_when_the_upload_itself_logs_to_the_handler(self):
        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.setLevel(logging.DEBUG)
        handler = LogtailHandler(source_token=self.source_token, flush_interval=0.01, check_interval=0.01)
        uploads = []

        def upload(frame):
            uploads.append(frame)
            # urllib3 logs every request it makes at DEBUG, and a handler on the
            # root logger receives that record.
            logger.debug('http://in.logs.betterstack.com:443 "POST / HTTP/1.1" 202 0')
            return mock.MagicMock(status_code=202)

        handler.uploader = upload
        logger.addHandler(handler)
        logger.info('hello')
        self.addCleanup(self._stop_flush_worker, handler)

        flushed = threading.Event()
        threading.Thread(target=lambda: (handler.flush(), flushed.set()), daemon=True).start()

        self.assertTrue(flushed.wait(2), 'flush() did not return')
        self.assertEqual([f['message'] for frame in uploads for f in frame], ['hello'])

    def test_records_logged_by_the_upload_ride_along_with_the_next_batch(self):
        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.setLevel(logging.DEBUG)
        # Only a full buffer sends a batch within the test.
        handler = LogtailHandler(source_token=self.source_token, buffer_capacity=2, flush_interval=1000, check_interval=0.01)
        uploads = []

        def upload(frame):
            logger.debug('POST / 202')  # what urllib3 does, still inside the request
            uploads.append([f['message'] for f in frame])
            return mock.MagicMock(status_code=202)

        handler.uploader = upload
        logger.addHandler(handler)
        self.addCleanup(self._stop_flush_worker, handler)

        logger.info('hello')
        logger.info('hello again')
        self._wait_until(lambda: len(uploads) == 1)
        logger.info('world')
        self._wait_until(lambda: len(uploads) == 2)

        self.assertEqual(uploads, [['hello', 'hello again'], ['POST / 202', 'world']])

    def test_a_batch_of_only_the_uploads_own_records_is_dropped_not_sent(self):
        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.setLevel(logging.DEBUG)
        handler = LogtailHandler(source_token=self.source_token, flush_interval=0.01, check_interval=0.01)
        uploads = []

        def upload(frame):
            logger.debug('POST / 202')
            uploads.append([f['message'] for f in frame])
            return mock.MagicMock(status_code=202)

        handler.uploader = upload
        logger.addHandler(handler)
        self.addCleanup(self._stop_flush_worker, handler)

        logger.info('hello')
        self._wait_until(lambda: len(uploads) == 1)
        time.sleep(0.1)  # several flush intervals, enough for the loop to show if it existed

        self.assertEqual(uploads, [['hello']])
        self.assertTrue(handler.pipe.empty())

    def test_flush_does_not_wait_while_the_caller_holds_the_logging_lock(self):
        # logging.config.dictConfig() flushes the handlers it replaces while holding the global
        # logging lock, and the worker's upload needs that lock whenever urllib3's logger has a
        # level-cache miss, so waiting for the worker there can only deadlock.
        logger = logging.getLogger(__name__)
        logger.handlers = []
        logger.setLevel(logging.INFO)
        handler = LogtailHandler(source_token=self.source_token, flush_interval=0.01, check_interval=0.01, flush_timeout=2)
        uploads = []
        in_upload = threading.Event()

        def upload(frame):
            in_upload.set()
            with logging._lock:  # what urllib3's isEnabledFor() does on a level-cache miss
                uploads.append([f['message'] for f in frame])
            return mock.MagicMock(status_code=202)

        handler.uploader = upload
        logger.addHandler(handler)
        self.addCleanup(self._stop_flush_worker, handler)

        with logging._lock:
            logger.info('hello')
            self.assertTrue(in_upload.wait(2))
            started = time.time()
            handler.flush()
            self.assertLess(time.time() - started, 0.5, 'flush() waited for a worker that needs the lock we hold')
        self._wait_until(lambda: uploads == [['hello']])

    def _wait_until(self, condition):
        deadline = time.time() + 2
        while not condition() and time.time() < deadline:
            time.sleep(0.01)
        self.assertTrue(condition())

    def _stop_flush_worker(self, handler):
        handler.flush_thread.should_run = False
        handler.flush_thread.join(1)


class UnserializableObject(object):
    """ Because this is a custom class, it cannot be serialized into JSON. """

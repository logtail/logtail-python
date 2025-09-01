# coding: utf-8
from __future__ import print_function, unicode_literals
import mock
import sys
import time
import threading
import unittest

from unittest.mock import patch

from logtail.compat import queue
from logtail.flusher import RETRY_SCHEDULE
from logtail.flusher import FlushWorker
from logtail.uploader import Uploader


class TestFlushWorker(unittest.TestCase):
    host = 'https://in.logtail.com'
    source_token = 'dummy_source_token'
    buffer_capacity = 5
    flush_interval = 2
    check_interval = 0.01
    timeout = 0.1

    def _setup_worker(self, uploader=None):
        pipe = queue.Queue(maxsize=self.buffer_capacity)
        uploader = uploader or Uploader(self.source_token, self.host, self.timeout)
        fw = FlushWorker(uploader, pipe, self.buffer_capacity, self.flush_interval, self.check_interval)
        return pipe, uploader, fw

    def test_is_thread(self):
        _, _, fw = self._setup_worker()
        self.assertIsInstance(fw, threading.Thread)

    def test_flushes_when_queue_is_full(self):
        first_frame = list(range(self.buffer_capacity))
        self.calls = 0
        self.flush_interval = 1000

        def uploader(frame):
            self.calls += 1
            self.assertEqual(frame, first_frame)
            return mock.MagicMock(status_code=202)

        pipe, _, fw = self._setup_worker(uploader)

        for log in first_frame:
            pipe.put(log, block=False)

        t1 = time.time()
        fw.step()
        t2 = time.time()
        self.assertLess(t2 - t1, self.flush_interval)

        self.assertEqual(self.calls, 1)

    @patch('logtail.flusher._calculate_time_remaining')
    def test_flushes_after_interval(self, calculate_time_remaining):
        self.buffer_capacity = 10
        num_items = 2
        first_frame = list(range(self.buffer_capacity))
        self.assertLess(num_items, self.buffer_capacity)

        self.upload_calls = 0
        def uploader(frame):
            self.upload_calls += 1
            self.assertEqual(frame, first_frame[:num_items])
            return mock.MagicMock(status_code=202)

        self.timeout_calls = 0
        def timeout(last_flush, interval):
            self.timeout_calls += 1
            # Until the last item has been retrieved from the pipe, the timeout
            # length doesn't matter. After the last item has been retrieved,
            # return a very small number so that the blocking get times out
            if self.timeout_calls < num_items:
                return 1000000
            return 0
        calculate_time_remaining.side_effect = timeout

        pipe, _, fw = self._setup_worker(uploader)
        for i in range(num_items):
            pipe.put(first_frame[i], block=False)

        fw.step()
        self.assertEqual(self.upload_calls, 1)
        self.assertEqual(self.timeout_calls, 2)

    @patch('logtail.flusher._calculate_time_remaining')
    @patch('logtail.flusher._initial_time_remaining')
    def test_does_nothing_without_any_items(self, initial_time_remaining, calculate_time_remaining):
        calculate_time_remaining.side_effect = lambda a,b: 0.0
        initial_time_remaining.side_effect = lambda a: 0.0001

        uploader = mock.MagicMock(side_effect=mock.MagicMock(status_code=202))
        pipe, _, fw = self._setup_worker(uploader)

        self.assertEqual(pipe.qsize(), 0)
        fw.step()
        self.assertFalse(uploader.called)

    @patch('logtail.flusher.time.sleep')
    def test_retries_according_to_schedule(self, mock_sleep):
        first_frame = list(range(self.buffer_capacity))

        self.uploader_calls = 0
        def uploader(frame):
            self.uploader_calls += 1
            self.assertEqual(frame, first_frame)
            return mock.MagicMock(status_code=500)

        self.sleep_calls = 0
        def sleep(time):
            self.assertEqual(time, RETRY_SCHEDULE[self.sleep_calls])
            self.sleep_calls += 1
        mock_sleep.side_effect = sleep

        pipe, _, fw = self._setup_worker(uploader)

        for log in first_frame:
            pipe.put(log, block=False)

        fw.step()
        self.assertEqual(self.uploader_calls, len(RETRY_SCHEDULE) + 1)
        self.assertEqual(self.sleep_calls, len(RETRY_SCHEDULE))

    def test_shutdown_condition_empties_queue_and_shuts_down(self):
        self.buffer_capacity = 10
        num_items = 5
        first_frame = list(range(self.buffer_capacity))
        self.assertLess(num_items, self.buffer_capacity)

        self.upload_calls = 0
        def uploader(frame):
            self.upload_calls += 1
            self.assertEqual(frame, first_frame[:num_items])
            return mock.MagicMock(status_code=202)

        pipe, _, fw = self._setup_worker(uploader)
        fw.parent_thread = mock.MagicMock(is_alive=lambda: False)

        for i in range(num_items):
            pipe.put(first_frame[i], block=False)

        fw.step()
        self.assertEqual(self.upload_calls, 1)
        self.assertFalse(fw.should_run)

    # test relies on overriding excepthook which is available from 3.8+
    @unittest.skipIf(sys.version_info < (3, 8), "Test skipped because overriding excepthook is only available on Python 3.8+")
    def test_shutdown_dont_raise_exception_in_thread(self):
        original_excepthook = threading.excepthook
        threading.excepthook = mock.Mock()

        _, _, fw = self._setup_worker()
        fw.parent_thread = mock.MagicMock(is_alive=lambda: False)
        fw.step()

        self.assertFalse(fw.should_run)
        self.assertFalse(threading.excepthook.called)

        threading.excepthook = original_excepthook

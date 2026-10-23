import json
import logging
import unittest
from io import StringIO
from unittest.mock import patch

from logtail import LogtailFormatter, LogtailHandler
from logtail.helpers import LogtailContext


class CapturingHandler(logging.Handler):
    def emit(self, record):
        self.request = getattr(record, 'request', self)


class TestLogRecordRequest(unittest.TestCase):
    def check_formatter(self, request, included):
        stream = StringIO()
        first = logging.StreamHandler(stream)
        first.setFormatter(LogtailFormatter(context=LogtailContext()))
        second = CapturingHandler()
        logger = logging.Logger('request-preservation')
        logger.addHandler(first)
        logger.addHandler(second)
        try:
            logger.info('example', extra={'request': request})
            frame = json.loads(stream.getvalue())
            self.assertEqual('request' in frame, included)
            if included:
                self.assertEqual(frame['request'], request)
            self.assertIs(second.request, request)
        finally:
            first.close()
            second.close()

    def check_handler(self, request, included):
        with patch('logtail.handler.Uploader') as uploader:
            handler = LogtailHandler('local-test', context=LogtailContext())
        record = logging.LogRecord('example', logging.INFO, __file__, 1,
                                   'example', (), None)
        record.request = request
        try:
            with patch.object(handler, 'ensure_flush_thread_alive'):
                handler.emit(record)
            frame = handler.pipe.get_nowait()
            self.assertEqual('request' in frame, included)
            if included:
                self.assertEqual(frame['request'], request)
            self.assertIn('request', record.__dict__)
            self.assertIs(record.request, request)
            uploader.return_value.assert_not_called()
        finally:
            handler.close()

    def test_formatter_preserves_request_object_for_next_handler(self):
        self.check_formatter(object(), False)

    def test_formatter_preserves_none_for_next_handler(self):
        self.check_formatter(None, False)

    def test_handler_preserves_request_object(self):
        self.check_handler(object(), False)

    def test_handler_preserves_none(self):
        self.check_handler(None, False)

    def test_formatter_keeps_supported_request_values(self):
        for request in ({'path': '/'}, ['example'], False, 0, 1.5, 'example'):
            with self.subTest(request=request):
                self.check_formatter(request, True)

    def test_handler_keeps_supported_request_values(self):
        for request in ({'path': '/'}, ['example'], False, 0, 1.5, 'example'):
            with self.subTest(request=request):
                self.check_handler(request, True)

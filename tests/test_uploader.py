# coding: utf-8
from __future__ import print_function, unicode_literals
import msgpack
import mock
import unittest

from unittest.mock import patch

from logtail.uploader import Uploader, DEFAULT_TIMEOUT


class TestUploader(unittest.TestCase):
    host = 'https://in.logtail.com'
    source_token = 'dummy_source_token'
    frame = [1, 2, 3]

    @patch('logtail.uploader.requests.Session.post')
    def test_call(self, post):
        def mock_post(endpoint, data=None, headers=None, timeout=None):
            # Check that the data is sent to ther correct endpoint
            self.assertEqual(endpoint, self.host)
            # Check the content-type
            self.assertIsInstance(headers, dict)
            self.assertIn('Authorization', headers)
            self.assertEqual('application/msgpack', headers.get('Content-Type'))
            # Check the content was msgpacked correctly
            self.assertEqual(msgpack.unpackb(data, raw=False), self.frame)

        post.side_effect = mock_post
        u = Uploader(self.source_token, self.host)
        u(self.frame)

        self.assertTrue(post.called)

    @patch('logtail.uploader.requests.Session.post')
    def test_call_passes_a_timeout_by_default(self, post):
        # A request.post() call with no timeout can hang indefinitely if the
        # server never responds - this is what caused a hubspot-sync cron
        # job to hang for hours in production, blocking every subsequent
        # scheduled run behind its lock file. Guard against a regression
        # back to an unbounded call.
        u = Uploader(self.source_token, self.host)
        u(self.frame)

        self.assertTrue(post.called)
        _, kwargs = post.call_args
        self.assertIn('timeout', kwargs)
        self.assertIsNotNone(kwargs['timeout'])
        self.assertEqual(kwargs['timeout'], DEFAULT_TIMEOUT)

    @patch('logtail.uploader.requests.Session.post')
    def test_call_respects_custom_timeout(self, post):
        u = Uploader(self.source_token, self.host, timeout=1)
        u(self.frame)

        _, kwargs = post.call_args
        self.assertEqual(kwargs['timeout'], 1)

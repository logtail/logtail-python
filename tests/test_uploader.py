# coding: utf-8
from __future__ import print_function, unicode_literals
import msgpack
import mock
import unittest

from unittest.mock import patch

from logtail.uploader import Uploader


class TestUploader(unittest.TestCase):
    host = 'https://in.logtail.com'
    source_token = 'dummy_source_token'
    frame = [1, 2, 3]
    timeout = 30

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
            # Check that timeout is passed to the request
            self.assertEqual(timeout, 30)

        post.side_effect = mock_post
        u = Uploader(self.source_token, self.host, self.timeout)
        u(self.frame)

        self.assertTrue(post.called)

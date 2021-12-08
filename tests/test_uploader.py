# coding: utf-8
from __future__ import print_function, unicode_literals
import msgpack
import mock
import unittest2

from logtail.uploader import Uploader


class TestUploader(unittest2.TestCase):
    host = 'https://in.logtail.com'
    source_token = 'dummy_source_token'
    frame = [1, 2, 3]

    @mock.patch('logtail.uploader.requests.Session.post')
    def test_call(self, post):
        def mock_post(endpoint, data=None, headers=None):
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

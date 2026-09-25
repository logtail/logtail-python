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

    @patch('logtail.uploader.requests.utils.get_environ_proxies', return_value={'https': 'http://proxy.internal:3128'})
    def test_resolves_proxy_settings_once_instead_of_on_every_request(self, get_environ_proxies):
        u = Uploader(self.source_token, self.host, self.timeout)

        with patch('logtail.uploader.requests.Session.post'):
            u(self.frame)
            u(self.frame)

        get_environ_proxies.assert_called_once_with(self.host)
        self.assertEqual(u.session.proxies, {'https': 'http://proxy.internal:3128'})
        self.assertFalse(u.session.trust_env)

    @patch.dict('os.environ', {'REQUESTS_CA_BUNDLE': '/etc/ssl/corporate-ca.pem'})
    def test_uses_the_ca_bundle_from_the_environment(self):
        u = Uploader(self.source_token, self.host, self.timeout)

        self.assertEqual(u.session.verify, '/etc/ssl/corporate-ca.pem')

    @patch('logtail.uploader.requests.utils.get_environ_proxies', return_value={'https': 'http://proxy.internal:3128'})
    def test_reset_replaces_the_session_but_keeps_the_resolved_settings(self, get_environ_proxies):
        u = Uploader(self.source_token, self.host, self.timeout)
        session = u.session

        u.reset()

        self.assertIsNot(u.session, session)
        self.assertEqual(u.session.proxies, {'https': 'http://proxy.internal:3128'})
        self.assertFalse(u.session.trust_env)
        get_environ_proxies.assert_called_once_with(self.host)

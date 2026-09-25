# coding: utf-8
from __future__ import print_function, unicode_literals
import os
from typing import Any, Union
import msgpack
import requests
import requests.utils

class Fake500(object):
    def __init__(self, exception: Exception) -> None:
        self.status_code = 500
        self.exception = exception

class Uploader(object):
    def __init__(self, source_token: str, host: str, timeout: float) -> None:
        self.source_token = source_token
        self.host = host
        self.timeout = timeout
        # requests would otherwise ask the environment, and on macOS SystemConfiguration, for
        # proxy settings on every request. Resolving them once here keeps the flush thread out
        # of CoreFoundation, which refuses to run in a child forked from a multithreaded
        # process, such as an RQ work horse. The CA bundle variables follow the same rule.
        self.proxies = requests.utils.get_environ_proxies(host)
        self.verify = os.environ.get('REQUESTS_CA_BUNDLE') or os.environ.get('CURL_CA_BUNDLE') or True
        self.headers = {
            'Authorization': 'Bearer %s' % source_token,
            'Content-Type': 'application/msgpack',
        }
        self.session = self._new_session()

    def __call__(self, frame: list[dict[str, Any]]) -> Union[requests.Response, Fake500]:
        data = msgpack.packb(frame, use_bin_type=True)
        try:
            return self.session.post(self.host, data=data, headers=self.headers, timeout=self.timeout)
        except requests.RequestException as e:
            return Fake500(e)

    def reset(self) -> None:
        # A forked child shares the parent's pooled socket, so it needs a session of its own,
        # built from the settings resolved above rather than looked up again.
        self.session = self._new_session()

    def _new_session(self) -> requests.Session:
        session = requests.Session()
        session.trust_env = False
        session.proxies = self.proxies
        session.verify = self.verify
        return session

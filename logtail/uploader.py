# coding: utf-8
from __future__ import print_function, unicode_literals
from typing import Any, Union
import msgpack
import requests

class Fake500(object):
    def __init__(self, exception: Exception) -> None:
        self.status_code = 500
        self.exception = exception

class Uploader(object):
    def __init__(self, source_token: str, host: str, timeout: float) -> None:
        self.source_token = source_token
        self.host = host
        self.timeout = timeout
        self.session = requests.Session()
        self.headers = {
            'Authorization': 'Bearer %s' % source_token,
            'Content-Type': 'application/msgpack',
        }

    def __call__(self, frame: list[dict[str, Any]]) -> Union[requests.Response, Fake500]:
        data = msgpack.packb(frame, use_bin_type=True)
        try:
            return self.session.post(self.host, data=data, headers=self.headers, timeout=self.timeout)
        except requests.RequestException as e:
            return Fake500(e)

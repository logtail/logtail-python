# coding: utf-8
from __future__ import print_function, unicode_literals
import msgpack
import requests


class Uploader(object):
    def __init__(self, source_token, host):
        self.source_token = source_token
        self.host = host
        self.session = requests.Session()
        self.headers = {
            'Authorization': 'Bearer %s' % source_token,
            'Content-Type': 'application/msgpack',
        }

    def __call__(self, frame):
        data = msgpack.packb(frame, use_bin_type=True)
        return self.session.post(self.host, data=data, headers=self.headers)

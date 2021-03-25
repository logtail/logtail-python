# coding: utf-8
from __future__ import print_function, unicode_literals
import msgpack
import requests


class Uploader(object):
    def __init__(self, access_token, host):
        self.access_token = access_token
        self.host = host
        self.headers = {
            'Authorization': 'Bearer %s' % access_token,
            'Content-Type': 'application/msgpack',
        }

    def __call__(self, frame):
        data = msgpack.packb(frame, use_bin_type=True)
        return requests.post(self.host, data=data, headers=self.headers)

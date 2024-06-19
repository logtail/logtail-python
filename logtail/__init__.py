# coding: utf-8
from __future__ import print_function, unicode_literals

from .handler import LogtailHandler
from .helpers import LogtailContext, DEFAULT_CONTEXT
from .formatter import LogtailFormatter

__version__ = '0.3.0'

context = DEFAULT_CONTEXT

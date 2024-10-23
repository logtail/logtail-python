# coding: utf-8
from __future__ import print_function, unicode_literals

try:
    import queue
except ImportError:
    import Queue as queue # type: ignore[import-not-found, no-redef]

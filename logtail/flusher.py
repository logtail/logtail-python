# coding: utf-8
from __future__ import print_function, unicode_literals
import sys
import time
import threading

from .compat import queue

RETRY_SCHEDULE = (1, 10, 60)  # seconds


class FlushWorker(threading.Thread):
    def __init__(self, upload, pipe, buffer_capacity, flush_interval):
        threading.Thread.__init__(self)
        self.parent_thread = threading.currentThread()
        self.upload = upload
        self.pipe = pipe
        self.buffer_capacity = buffer_capacity
        self.flush_interval = flush_interval

    def run(self):
        while True:
            self.step()

    def step(self):
        last_flush = time.time()
        time_remaining = _initial_time_remaining(self.flush_interval)
        frame = []

        # If the parent thread has exited but there are still outstanding
        # events, attempt to send them before exiting.
        shutdown = not self.parent_thread.is_alive()

        # Fill phase: take events out of the queue and group them for sending.
        # Takes up to `buffer_capacity` events out of the queue and groups them
        # for sending; may send fewer than `buffer_capacity` events if
        # `flush_interval` seconds have passed without sending any events.
        while len(frame) < self.buffer_capacity and time_remaining > 0:
            try:
                # Blocks for up to 1.0 seconds for each item to prevent
                # spinning and burning CPU unnecessarily. Could block for the
                # entire amount of `time_remaining` but then in the case that
                # the parent thread has exited, that entire amount of time
                # would be waited before this child worker thread exits.
                entry = self.pipe.get(block=(not shutdown), timeout=1.0)
                frame.append(entry)
                self.pipe.task_done()
            except queue.Empty:
                if shutdown:
                    break
            shutdown = not self.parent_thread.is_alive()
            time_remaining = _calculate_time_remaining(last_flush, self.flush_interval)

        # Send phase: takes the outstanding events (up to `buffer_capacity`
        # count) and sends them to the Logtail endpoint all at once. If the
        # request fails in a way that can be retried, it is retried with an
        # exponential backoff in between attempts.
        if frame:
            for delay in RETRY_SCHEDULE + (None, ):
                response = self.upload(frame)
                if not _should_retry(response.status_code):
                    break
                if delay is not None:
                    time.sleep(delay)

        if shutdown:
            sys.exit(0)


def _initial_time_remaining(flush_interval):
    return flush_interval


def _calculate_time_remaining(last_flush, flush_interval):
    elapsed = time.time() - last_flush
    time_remaining = max(flush_interval - elapsed, 0)
    return time_remaining


def _should_retry(status_code):
    return 500 <= status_code < 600

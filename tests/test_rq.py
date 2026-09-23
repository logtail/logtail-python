# coding: utf-8
from __future__ import print_function, unicode_literals
import json
import logging
import mock
import os
import unittest

from unittest.mock import patch

import rq

from logtail import LogtailHandler
from logtail.rq import Worker


class TestWorker(unittest.TestCase):
    source_token = 'dummy_source_token'

    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.logger.handlers = []
        self.logger.setLevel(logging.DEBUG)
        self.uploads = []
        # Only an explicit flush can send anything within the test.
        self.handler = LogtailHandler(source_token=self.source_token, flush_interval=1000, check_interval=0.01)
        self.handler.uploader = self._upload
        self.logger.addHandler(self.handler)
        connection = mock.MagicMock()
        connection.connection_pool.connection_kwargs = {}
        self.worker = Worker(['default'], connection=connection, prepare_for_work=False)

    def tearDown(self):
        if self.handler.flush_thread:
            self.handler.flush_thread.should_run = False
            self.handler.flush_thread.join(1)

    def _upload(self, frame):
        self.uploads.append([f['message'] for f in frame])
        return mock.MagicMock(status_code=202)

    def test_is_an_rq_worker(self):
        self.assertIsInstance(self.worker, rq.Worker)

    @patch.object(rq.Worker, 'perform_job')
    def test_flushes_logtail_handlers_after_the_job(self, perform_job):
        perform_job.side_effect = lambda job, queue: self.logger.info('inside the job') or True

        self.assertTrue(self.worker.perform_job(mock.sentinel.job, mock.sentinel.queue))

        perform_job.assert_called_once_with(mock.sentinel.job, mock.sentinel.queue)
        self.assertEqual(self.uploads, [['inside the job']])

    @patch.object(rq.Worker, 'perform_job')
    def test_flushes_logtail_handlers_when_the_job_raises(self, perform_job):
        def fail(job, queue):
            self.logger.error('the job blew up')
            raise ValueError('boom')
        perform_job.side_effect = fail

        with self.assertRaises(ValueError):
            self.worker.perform_job(mock.sentinel.job, mock.sentinel.queue)

        self.assertEqual(self.uploads, [['the job blew up']])

    @patch.object(rq.Worker, 'perform_job')
    def test_records_logged_in_the_work_horse_are_sent_before_it_exits(self, perform_job):
        # RQ forks a work horse per job and ends it with os._exit(), which skips
        # the interpreter shutdown that would otherwise flush the handler.
        perform_job.side_effect = lambda job, queue: self.logger.info('inside the work horse')
        read_end, write_end = os.pipe()
        self.handler.uploader = lambda frame: os.write(write_end, json.dumps([f['message'] for f in frame]).encode()) and mock.MagicMock(status_code=202)

        pid = os.fork()
        if pid == 0:
            self.worker.main_work_horse(mock.MagicMock(), mock.MagicMock())
        os.waitpid(pid, 0)
        os.close(write_end)
        os.set_blocking(read_end, False)

        self.assertEqual(json.loads(os.read(read_end, 4096)), ['inside the work horse'])

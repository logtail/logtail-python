# coding: utf-8

from logtail.frame import create_frame
from logtail.handler import LogtailHandler
from logtail.helpers import LogtailContext
from sys import version_info
import datetime
import unittest
import logging

class TestLogtailLogEntry(unittest.TestCase):
    def test_create_frame_happy_path(self):
        log_record = logging.LogRecord("logtail-test", 20, "/some/path", 10, "Some log message", [], None)
        frame = create_frame(log_record, log_record.getMessage(), LogtailContext())
        self.assertTrue(frame['level'] == 'info')
        # ISO timestamp must end with timezone info
        self.assertTrue(frame['dt'].endswith("+00:00"))

        # These tests require Python >= 3.7
        if version_info.major == 2 or version_info.minor <= 6:
            return
        # Sent date matches log record date
        date_ref = datetime.datetime.utcfromtimestamp(log_record.created).replace(tzinfo=datetime.timezone.utc)
        date_sent = datetime.datetime.fromisoformat(frame['dt'])
        self.assertEqual(date_ref, date_sent)

    def test_create_frame_with_extra(self):
        log_record = logging.LogRecord("logtail-test", 20, "/some/path", 10, "Some log message", [], None)
        extra = {'non_dict_key': 'string_value', 'dict_key': {'name': 'Test Test'}}
        log_record.__dict__.update(extra) # This is how `extra` gets included in the LogRecord

        # By default, non-dict keys are excluded.
        frame = create_frame(log_record, log_record.getMessage(), LogtailContext())
        self.assertTrue(frame['level'] == 'info')
        self.assertIn('dict_key', frame)
        self.assertNotIn('non_dict_key', frame)

        frame = create_frame(log_record, log_record.getMessage(), LogtailContext(), include_extra_attributes=True)
        self.assertIn('non_dict_key', frame)

    def test_create_frame_with_unserializable_extra(self):
        log_record = logging.LogRecord("logtail-test", 20, "/some/path", 10, "Some log message", [], None)
        extra = {'extra': {'unserializable': UnserializableObject()}}
        log_record.__dict__.update(extra) # This is how `extra` gets included in the LogRecord

        frame = create_frame(log_record, log_record.getMessage(), LogtailContext())
        self.assertRegex(frame['extra']['unserializable'], r'^<tests\.test_frame\.UnserializableObject object at 0x[0-f]+>$')

    def test_create_frame_with_context(self):
        log_record = logging.LogRecord("logtail-test", 20, "/some/path", 10, "Some log message", [], None)

        context = LogtailContext()
        with context(data={'my_field': 'my_value'}):
            frame = create_frame(log_record, log_record.getMessage(), context)

        self.assertEqual(frame['context']['data'], {'my_field': 'my_value'})

    def test_create_frame_with_unserializable_context(self):
        log_record = logging.LogRecord("logtail-test", 20, "/some/path", 10, "Some log message", [], None)

        context = LogtailContext()
        with context(data={'unserializable': UnserializableObject()}):
            frame = create_frame(log_record, log_record.getMessage(), context)

        self.assertRegex(frame['context']['data']['unserializable'], r'^<tests\.test_frame\.UnserializableObject object at 0x[0-f]+>$')

class UnserializableObject(object):
    """ Because this is a custom class, it cannot be serialized into JSON. """

# coding: utf-8
from __future__ import print_function, unicode_literals
import unittest2

from logtail import LogtailContext


class TestLogtailContext(unittest2.TestCase):

    def test_exists(self):
        c = LogtailContext()
        self.assertFalse(c.exists())
        with c(user={'name': 'a'}):
            self.assertTrue(c.exists())
        self.assertFalse(c.exists())

    def test_only_accepts_keyword_argument_dicts(self):
        c = LogtailContext()
        # Named context passes
        c(user={'name': 'a'})
        # Non-named contexts fail, even if they're dicts
        for garbage in ['x', 1, [{'name': 'a'}], {'name': 'a'}]:
            with self.assertRaises(ValueError):
                c(garbage)
        # Named contexts fail if they are not dicts
        for garbage in [{'user': 1}, {'user': []}, {'user': tuple()}]:
            with self.assertRaises(ValueError):
                c(**garbage)

    def test_does_not_suppress_exceptions(self):
        c = LogtailContext()
        with self.assertRaises(ValueError):
            with c(user={'name': 'a'}):
                raise ValueError('should be thrown')

    def test_nested_collapse(self):
        c = LogtailContext()
        self.assertEqual(c.collapse(), {})

        with c(user={'name': 'a', 'count': 1}):
            self.assertEqual(
                c.collapse(),
                {'user': {'name': 'a', 'count': 1}}
            )

            with c(user={'name': 'b'}, other={'foo': 'bar'}):
                self.assertEqual(
                    c.collapse(),
                    {'user': {'name': 'b', 'count': 1},
                     'other': {'foo': 'bar'}}
                )

            self.assertEqual(
                c.collapse(),
                {'user': {'name': 'a', 'count': 1}}
            )

        self.assertEqual(c.collapse(), {})

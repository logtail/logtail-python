"""Tests for plan.py: python -m unittest discover -s e2e -p 'plan_test.py'"""
import unittest

import plan

SETUP_PY = """
setup(
    name='logtail-python',
    install_requires=REQUIREMENTS,
    python_requires='>=3.10',
)
"""

REQUIREMENTS_TXT = """# runtime dependencies
requests>=2.18.4
msgpack >= 0.5.6, <2

typing-extensions==4.12.2
"""

# The shape of actions/python-versions' versions-manifest.json, newest first, files left out.
MANIFEST = [
    {'version': '3.16.0-alpha.1', 'stable': False},
    {'version': '3.15.2', 'stable': True},
    {'version': '3.15.0-rc.3', 'stable': False},
    {'version': '3.15.1', 'stable': True},
    {'version': '3.9.25', 'stable': True},
]


class PythonFloorTest(unittest.TestCase):
    def test_reads_python_requires(self):
        self.assertEqual(plan.python_floor(SETUP_PY), '3.10')

    def test_accepts_double_quotes_and_spaces(self):
        self.assertEqual(plan.python_floor('python_requires = ">= 3.11",'), '3.11')

    def test_refuses_a_setup_py_without_a_floor(self):
        with self.assertRaises(ValueError):
            plan.python_floor("setup(name='logtail-python')")


class RequirementFloorsTest(unittest.TestCase):
    def test_reads_each_floor_and_skips_comments_and_pins(self):
        self.assertEqual(plan.requirement_floors(REQUIREMENTS_TXT), {'requests': '2.18.4', 'msgpack': '0.5.6'})


class PythonVersionsTest(unittest.TestCase):
    def test_newest_stable_compares_numerically_and_skips_pre_releases(self):
        self.assertEqual(plan.newest_stable_python(MANIFEST), '3.15.2')

    def test_canary_is_the_next_minor_as_a_pre_release(self):
        self.assertEqual(plan.canary_python(MANIFEST), '3.16-dev')

    def test_canary_stays_on_the_newest_minor_until_the_next_one_has_an_alpha(self):
        self.assertEqual(plan.canary_python(MANIFEST[1:]), '3.15-dev')

    def test_next_minor_after_a_two_digit_minor(self):
        manifest = [{'version': '3.9.25', 'stable': True}, {'version': '3.10.0-alpha.1', 'stable': False}]
        self.assertEqual(plan.canary_python(manifest), '3.10-dev')


class EntryTest(unittest.TestCase):
    def test_floor_entry(self):
        self.assertEqual(plan.entry('floor', '3.10', '2.18.4', '0.5.6', 'checkout'), {
            'leg': 'floor',
            'name': 'floor (Python 3.10, requests 2.18.4, msgpack 0.5.6)',
            'python': '3.10',
            'requests': '2.18.4',
            'msgpack': '0.5.6',
            'prerelease': False,
            'source': 'checkout',
            'runner': 'ubuntu-24.04',
        })

    def test_canary_entry_allows_pre_releases(self):
        self.assertEqual(plan.entry('canary', '3.16-dev', '2.33.0', '1.1.2', 'pypi'), {
            'leg': 'canary',
            'name': 'canary (Python 3.16-dev, newest requests and msgpack, pre-releases allowed)',
            'python': '3.16-dev',
            'requests': '2.33.0',
            'msgpack': '1.1.2',
            'prerelease': True,
            'source': 'pypi',
            'runner': 'ubuntu-latest',
        })

    def test_exact_versions_replace_the_floors(self):
        floor = plan.plan('floor', '3.10', 'checkout', requests='2.19.0', msgpack='0.6.0')
        self.assertEqual(floor['name'], 'floor (Python 3.10, requests 2.19.0, msgpack 0.6.0)')

    def test_refuses_a_name_that_cannot_be_an_artifact_name(self):
        with self.assertRaises(ValueError):
            plan.entry('latest', 'pypy:3.11', '2.33.0', '1.1.2', 'checkout')


if __name__ == '__main__':
    unittest.main()

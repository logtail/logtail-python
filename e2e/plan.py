"""Prints the job matrix of the E2E workflow (.github/workflows/e2e.yml) as JSON.

    python e2e/plan.py --leg all|floor|latest|canary [--python <exact>] [--requests <exact>] [--msgpack <exact>] [--source checkout|pypi]

floor   the oldest versions this package declares: Python from python_requires in setup.py, requests and
        msgpack from their >= floors in requirements.txt. Works offline.
latest  the newest stable CPython that actions/setup-python can install, and the newest requests and msgpack
        on PyPI. The job fails when pip installs anything older than what is planned here.
canary  the next CPython minor as a pre-release ("3.16-dev"), with requests and msgpack installed with --pre.

--python, --requests and --msgpack replace the planned version of every leg with one exact version, which is
how a run bisects a failure to one release. --source is copied into every entry: checkout installs the client
built from this checkout, pypi installs its newest release from PyPI.

Standard library only, so the plan job needs nothing but a Python.
"""
import argparse
import functools
import json
import pathlib
import re
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST_URL = 'https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json'
PYPI_URL = 'https://pypi.org/pypi/{}/json'
LEGS = ('floor', 'latest', 'canary')
# Job names become artifact names (e2e-summary-<job name>), which must not contain any of these.
NOT_IN_NAMES = ':"<>|*?/\\'


def python_floor(setup_py):
    match = re.search(r"python_requires\s*=\s*['\"]>=\s*([0-9.]+)['\"]", setup_py)
    if not match:
        raise ValueError("setup.py declares no python_requires='>=X.Y'")
    return match.group(1)


def requirement_floors(requirements_txt):
    floors = {}
    for line in requirements_txt.splitlines():
        match = re.match(r'\s*([A-Za-z0-9_.-]+)\s*>=\s*([^,;\s]+)', line)
        if match:
            floors[match.group(1).lower()] = match.group(2)
    return floors


def version_key(version):
    return tuple(int(part) for part in version.split('.'))


def newest_stable_python(manifest):
    return max((entry['version'] for entry in manifest if entry['stable']), key=version_key)


def canary_python(manifest):
    major, minor = version_key(newest_stable_python(manifest))[:2]
    next_minor = '{}.{}'.format(major, minor + 1)
    # For a week or two after an X.Y.0 release, the next minor has no alpha yet and setup-python would find
    # nothing to install, so the canary stays on the newest minor until its first pre-release shows up.
    if any(entry['version'].startswith(next_minor + '.') for entry in manifest):
        return next_minor + '-dev'
    return '{}.{}-dev'.format(major, minor)


def job_name(leg, python, requests, msgpack):
    if leg == 'canary':
        name = 'canary (Python {}, newest requests and msgpack, pre-releases allowed)'.format(python)
    else:
        name = '{} (Python {}, requests {}, msgpack {})'.format(leg, python, requests, msgpack)
    if set(name) & set(NOT_IN_NAMES):
        raise ValueError('job name {!r} contains one of {}, which artifact names do not allow'.format(name, NOT_IN_NAMES))
    return name


def entry(leg, python, requests, msgpack, source):
    return {
        'leg': leg,
        'name': job_name(leg, python, requests, msgpack),
        'python': python,
        'requests': requests,
        'msgpack': msgpack,
        'prerelease': leg == 'canary',
        'source': source,
        # The floor runs on the oldest Ubuntu image GitHub offers, the other legs follow ubuntu-latest.
        'runner': 'ubuntu-24.04' if leg == 'floor' else 'ubuntu-latest',
    }


@functools.lru_cache(maxsize=None)
def fetch_json(url, attempts=3):
    # A registry hiccup at schedule time should not file a Linear issue, so the lookup is retried.
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.load(response)
        except Exception as error:
            if attempt == attempts:
                raise SystemExit('GET {} failed {} times, last: {}'.format(url, attempts, error))
            time.sleep(10)


def newest_release(package):
    return fetch_json(PYPI_URL.format(package))['info']['version']


def plan(leg, python, source, requests='', msgpack=''):
    if leg == 'floor':
        floors = requirement_floors((ROOT / 'requirements.txt').read_text())
        missing = [package for package in ('requests', 'msgpack') if package not in floors]
        if missing:
            raise SystemExit('requirements.txt declares no >= floor for {}'.format(', '.join(missing)))
        python = python or python_floor((ROOT / 'setup.py').read_text())
        return entry(leg, python, requests or floors['requests'], msgpack or floors['msgpack'], source)
    if not python:
        manifest = fetch_json(MANIFEST_URL)
        python = newest_stable_python(manifest) if leg == 'latest' else canary_python(manifest)
    return entry(leg, python, requests or newest_release('requests'), msgpack or newest_release('msgpack'), source)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Prints the E2E job matrix as JSON.')
    parser.add_argument('--leg', choices=('all',) + LEGS, default='all')
    parser.add_argument('--python', default='', help='one exact Python version for every leg instead of the planned one')
    parser.add_argument('--requests', default='', help='one exact requests version for every leg instead of the planned one')
    parser.add_argument('--msgpack', default='', help='one exact msgpack version for every leg instead of the planned one')
    parser.add_argument('--source', choices=('checkout', 'pypi'), default='checkout')
    args = parser.parse_args(argv)
    legs = LEGS if args.leg == 'all' else (args.leg,)
    try:
        include = [plan(leg, args.python.strip(), args.source, args.requests.strip(), args.msgpack.strip()) for leg in legs]
    except ValueError as error:
        raise SystemExit(error)
    print(json.dumps(include))


if __name__ == '__main__':
    main()

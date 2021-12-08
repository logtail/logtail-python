# coding: utf-8
from __future__ import print_function, unicode_literals
from datetime import datetime

from os import path
import __main__

def create_frame(record, message, context, include_extra_attributes=False):
    r = record.__dict__
    frame = {}
    frame['dt'] = datetime.utcfromtimestamp(r['created']).isoformat()
    frame['level'] = level = _levelname(r['levelname'])
    frame['severity'] = int(r['levelno'] / 10)
    frame['message'] = message
    frame['context'] = ctx = {}

    # Runtime context
    ctx['runtime'] = runtime = {}
    runtime['function'] = r['funcName']
    runtime['file'] = _relative_to_main_module_if_possible(r['pathname'])
    runtime['line'] = r['lineno']
    runtime['thread_id'] = r['thread']
    runtime['thread_name'] = r['threadName']
    runtime['logger_name'] = r['name']

    # Runtime context
    ctx['system'] = system = {}
    system['pid'] = r['process']
    system['process_name'] = r['processName']

    # Custom context
    if context.exists():
        ctx.update(context.collapse())

    events = _parse_custom_events(record, include_extra_attributes)
    if events:
        frame.update(events)

    return frame


def _parse_custom_events(record, include_extra_attributes):
    default_keys = {
        'args', 'asctime', 'created', 'exc_info', 'exc_text', 'pathname',
        'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
        'message', 'msg', 'name', 'pathname', 'process', 'processName',
        'relativeCreated', 'thread', 'threadName'
    }
    events = {}
    for key, val in record.__dict__.items():
        if key in default_keys:
            continue
        if not include_extra_attributes and not isinstance(val, dict):
            continue
        events[key] = val
    return events


def _levelname(level):
    return {
        'debug': 'debug',
        'info': 'info',
        'warning': 'warn',
        'error': 'error',
        'critical': 'critical',
    }[level.lower()]


def _relative_to_main_module_if_possible(pathname):
    has_main_module = hasattr(__main__, '__file__')
    return _relative_to_main_module(pathname) if has_main_module else pathname

def _relative_to_main_module(pathname):
    return path.relpath(pathname, path.dirname(__main__.__file__))

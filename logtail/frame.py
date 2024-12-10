# coding: utf-8
from __future__ import print_function, unicode_literals
from datetime import datetime, timezone

from os import path
import __main__

def create_frame(record, message, context, include_extra_attributes=False):
    r = record.__dict__
    # Django sends a request object in the record, which is not JSON serializable
    if "request" in r and not isinstance(r["request"], (dict, list, bool, int, float, str)) :
        del r["request"]
    frame = {}
    frame['dt'] = datetime.fromtimestamp(r['created'], timezone.utc).isoformat()
    frame['level'] = _levelname(r['levelname'])
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

    return _remove_circular_dependencies(frame)

def _parse_custom_events(record, include_extra_attributes):
    default_keys = {
        'args', 'asctime', 'created', 'exc_info', 'exc_text', 'pathname',
        'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
        'message', 'msg', 'name', 'process', 'processName',
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

def _remove_circular_dependencies(obj, memo=None):
    if memo is None:
        memo = set()

    # Skip immutable types, which can't contain circular dependencies
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj

    # For mutable objects, check for circular references
    obj_id = id(obj)
    if obj_id in memo:
        return "<omitted circular reference>"
    memo.add(obj_id)

    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            new_dict[key] = _remove_circular_dependencies(value, memo.copy())
        return new_dict
    elif isinstance(obj, list):
        return [_remove_circular_dependencies(item, memo.copy()) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_remove_circular_dependencies(item, memo.copy()) for item in obj)
    elif isinstance(obj, set):
        return {_remove_circular_dependencies(item, memo.copy()) for item in obj}
    else:
        return obj

def _levelname(level):
    return level.lower()

def _relative_to_main_module_if_possible(pathname):
    has_main_module = hasattr(__main__, '__file__')
    return _relative_to_main_module(pathname) if has_main_module else pathname

def _relative_to_main_module(pathname):
    return path.relpath(pathname, path.dirname(__main__.__file__))

# Fork Comments

This is a fork of Better Stack's logtail-python repo.  It adds functionality similar to `handler.context()`, except it allows custom properties to be added at the top level of the log JSON.

So instead of saying `handler.context(program={'name': 'transmogrifier'})`, you simply say `handler.staticProps={'name': 'transmogrifier'}`.  The difference is that now, it is easier to search: Instead of searching on `context.program.name=transmogrifier`, you can simply search on `name=transmogrifier`.  This was done to reproduce the program name functionality in Papertrail / SWO.

# [Better Stack](https://betterstack.com/logs) Python client

📣 Logtail is now part of Better Stack. [Learn more ⇗](https://betterstack.com/press/introducing-better-stack/)

[![Better Stack dashboard](https://github.com/logtail/logtail-python/assets/10132717/e2a1196b-7924-4abc-9b85-055e17b5d499)](https://betterstack.com/logs)

[![ISC License](https://img.shields.io/badge/license-ISC-ff69b4.svg)](LICENSE.md)
[![PyPI package](https://badge.fury.io/py/logtail-python.svg)](https://badge.fury.io/py/logtail-python)
![Tests](https://github.com/logtail/logtail-python/actions/workflows/main.yml/badge.svg?branch=master)

Experience SQL-compatible structured log management based on ClickHouse. [Learn more ⇗](https://betterstack.com/logs)

## Documentation

[Getting started ⇗](https://betterstack.com/docs/logs/python/)

## Need help?
Please let us know at [hello@betterstack.com](mailto:hello@betterstack.com). We're happy to help!

---

[ISC license](https://github.com/logtail/logtail-python/blob/master/LICENSE.md), [example project](https://github.com/logtail/logtail-python/tree/master/example-project)

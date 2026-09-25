# Checked with `mypy --strict` in CI, never run: imports and calls the public API the
# way applications do, so it fails if a name stops being exported from `logtail`.
import json
import logging

import logtail
from logtail import DEFAULT_CONTEXT, LogtailContext, LogtailFormatter, LogtailHandler

handler = LogtailHandler(source_token='token', host='in.logs.betterstack.com', timeout=(3.05, 27), flush_timeout=None)
handler.setFormatter(LogtailFormatter(context=DEFAULT_CONTEXT, json_default=str, json_encoder=json.JSONEncoder))
logging.getLogger(__name__).addHandler(handler)

request_context: LogtailContext = logtail.context
with request_context(request={'id': 'abc'}):
    logging.getLogger(__name__).info('typed')

version: str = logtail.__version__

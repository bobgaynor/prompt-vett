import logging

from pythonjsonlogger.json import JsonFormatter

from prompt_vett.security.redaction import KeyRedactionFilter


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()

    # Idempotent: bail out if we already attached the filter.
    if any(isinstance(f, KeyRedactionFilter) for f in root.filters):
        return

    filter_ = KeyRedactionFilter()
    root.addFilter(filter_)

    for handler in root.handlers:
        handler.addFilter(filter_)

    # In local dev there are no pre-existing handlers; add a JSON one.
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.addFilter(filter_)
        handler.setFormatter(JsonFormatter())
        root.addHandler(handler)

    root.setLevel(level)

import logging
import re

# Order matters: sk-ant- must come before sk- so the longer prefix matches first.
KEY_PATTERNS = re.compile(
    r"AIza[0-9A-Za-z_-]{35}"
    r"|sk-ant-[A-Za-z0-9_-]{20,}"
    r"|sk-[A-Za-z0-9]{20,}"
)

_REPLACEMENT = "[REDACTED]"


def redact(value: str) -> str:
    return KEY_PATTERNS.sub(_REPLACEMENT, value)


def redact_payload(payload: object) -> object:
    if isinstance(payload, str):
        return redact(payload)
    if isinstance(payload, dict):
        return {k: redact_payload(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [redact_payload(item) for item in payload]
    if isinstance(payload, tuple):
        return tuple(redact_payload(item) for item in payload)
    return payload


class KeyRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)

        if isinstance(record.args, tuple):
            record.args = tuple(
                redact(a) if isinstance(a, str) else a for a in record.args
            )
        elif isinstance(record.args, dict):
            record.args = {
                k: redact(v) if isinstance(v, str) else v
                for k, v in record.args.items()
            }

        # Pre-format exception info so the traceback text can be redacted.
        # Clearing exc_info prevents the formatter from re-formatting it later.
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = logging.Formatter().formatException(record.exc_info)
            record.exc_text = redact(record.exc_text)
            record.exc_info = None
        elif record.exc_text:
            record.exc_text = redact(record.exc_text)

        return True

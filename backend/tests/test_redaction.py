import io
import logging

import pytest

from prompt_vett.logging_setup import setup_logging
from prompt_vett.security.redaction import KeyRedactionFilter, redact, redact_payload

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GOOGLE_KEY = "AIza" + "A" * 35
_OPENAI_KEY = "sk-" + "B" * 20
_ANTHROPIC_KEY = "sk-ant-" + "C" * 20


def _make_logger(name: str) -> tuple[logging.Logger, io.StringIO]:
    """Return an isolated logger + its StringIO stream.

    The logger does not propagate so root-logger state doesn't interfere.
    Both the logger and the handler carry KeyRedactionFilter, matching the
    same dual-attachment pattern used by setup_logging().
    """
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.filters.clear()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))

    filt = KeyRedactionFilter()
    logger.addFilter(filt)
    handler.addFilter(filt)
    logger.addHandler(handler)
    return logger, stream


def _clean_root_filter() -> None:
    """Remove any KeyRedactionFilter instances from root and its handlers."""
    root = logging.getLogger()
    root.filters = [f for f in root.filters if not isinstance(f, KeyRedactionFilter)]
    for h in root.handlers:
        h.filters = [f for f in h.filters if not isinstance(f, KeyRedactionFilter)]


# ---------------------------------------------------------------------------
# redact()
# ---------------------------------------------------------------------------


def test_redact_google_key() -> None:
    assert redact(f"key={_GOOGLE_KEY}") == "key=[REDACTED]"


def test_redact_openai_key() -> None:
    assert redact(f"key={_OPENAI_KEY}") == "key=[REDACTED]"


def test_redact_anthropic_key() -> None:
    assert redact(f"key={_ANTHROPIC_KEY}") == "key=[REDACTED]"


def test_redact_multiple_keys_in_one_string() -> None:
    s = f"{_GOOGLE_KEY} and {_OPENAI_KEY}"
    result = redact(s)
    assert _GOOGLE_KEY not in result
    assert _OPENAI_KEY not in result
    assert result.count("[REDACTED]") == 2


def test_redact_no_match_returns_unchanged() -> None:
    s = "no keys here, just normal text"
    assert redact(s) == s


# ---------------------------------------------------------------------------
# redact_payload()
# ---------------------------------------------------------------------------


def test_redact_payload_nested_dict() -> None:
    payload = {"outer": {"inner": f"key={_GOOGLE_KEY}"}}
    result = redact_payload(payload)
    assert isinstance(result, dict)
    inner = result["outer"]  # type: ignore[index]
    assert isinstance(inner, dict)
    assert inner["inner"] == "key=[REDACTED]"  # type: ignore[index]


def test_redact_payload_list_of_strings() -> None:
    payload = [f"key={_OPENAI_KEY}", "safe"]
    result = redact_payload(payload)
    assert isinstance(result, list)
    assert result[0] == "key=[REDACTED]"  # type: ignore[index]
    assert result[1] == "safe"  # type: ignore[index]


def test_redact_payload_preserves_non_strings() -> None:
    payload = {"n": 42, "b": True, "null": None, "f": 3.14}
    result = redact_payload(payload)
    assert result == payload


# ---------------------------------------------------------------------------
# KeyRedactionFilter
# ---------------------------------------------------------------------------


def test_filter_redacts_log_message() -> None:
    logger, stream = _make_logger("test.msg")
    logger.info("key=%s", _GOOGLE_KEY)
    output = stream.getvalue()
    assert _GOOGLE_KEY not in output
    assert "[REDACTED]" in output


def test_filter_redacts_log_args() -> None:
    logger, stream = _make_logger("test.args")
    logger.info("user key: %s", _ANTHROPIC_KEY)
    output = stream.getvalue()
    assert _ANTHROPIC_KEY not in output
    assert "[REDACTED]" in output


def test_filter_redacts_exception_traceback() -> None:
    # The key lives only in the exception message, not in the log call itself.
    # This is the path that leaks in Lambda: unhandled exceptions echo their
    # args (including API keys) into CloudWatch via the traceback formatter.
    logger, stream = _make_logger("test.exc")
    try:
        raise ValueError(f"key is {_GOOGLE_KEY}")
    except ValueError:
        logger.exception("an error occurred")
    output = stream.getvalue()
    assert _GOOGLE_KEY not in output
    assert "[REDACTED]" in output


# ---------------------------------------------------------------------------
# setup_logging() — Lambda compatibility
# ---------------------------------------------------------------------------


def test_filter_attached_when_handler_pre_exists() -> None:
    # Simulate Lambda: a handler is already on the root logger before our
    # code runs.  setup_logging() must attach the filter to that handler too,
    # not just to the logger.
    _clean_root_filter()
    root = logging.getLogger()

    stream = io.StringIO()
    pre_handler = logging.StreamHandler(stream)
    pre_handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(pre_handler)

    try:
        setup_logging()

        assert any(isinstance(f, KeyRedactionFilter) for f in pre_handler.filters)

        test_logger = logging.getLogger("test.lambda_compat")
        test_logger.setLevel(logging.DEBUG)
        test_logger.propagate = True
        test_logger.handlers.clear()
        test_logger.filters.clear()
        test_logger.info(f"key={_GOOGLE_KEY}")

        output = stream.getvalue()
        assert _GOOGLE_KEY not in output
        assert "[REDACTED]" in output
    finally:
        root.removeHandler(pre_handler)
        _clean_root_filter()


def test_setup_logging_is_idempotent() -> None:
    # Calling setup_logging() twice must not attach two copies of the filter.
    # Lambda cold-starts can re-import modules; double-filters would double
    # processing and could confuse downstream log readers.
    _clean_root_filter()
    try:
        setup_logging()
        setup_logging()
        root = logging.getLogger()
        count = sum(1 for f in root.filters if isinstance(f, KeyRedactionFilter))
        assert count == 1
    finally:
        _clean_root_filter()

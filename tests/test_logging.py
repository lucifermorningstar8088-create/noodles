import logging

from noodles.logging_config import JsonFormatter, SecretRedactionFilter, redact_secrets


def test_redact_common_secret_assignments() -> None:
    message = "api_key=abc123 password:topsecret Authorization: Bearer token123"
    redacted = redact_secrets(message)

    assert "abc123" not in redacted
    assert "topsecret" not in redacted
    assert "token123" not in redacted
    assert redacted.count("[REDACTED]") == 3


def test_log_filter_redacts_formatted_message() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="access_token=%s",
        args=("sensitive-value",),
        exc_info=None,
    )

    assert SecretRedactionFilter().filter(record) is True
    assert "sensitive-value" not in record.getMessage()


def test_json_formatter_redacts_exception_text() -> None:
    try:
        raise RuntimeError("password=exception-secret")
    except RuntimeError:
        import sys

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="request failed",
            args=(),
            exc_info=sys.exc_info(),
        )

    output = JsonFormatter().format(record)
    assert "exception-secret" not in output
    assert "[REDACTED]" in output

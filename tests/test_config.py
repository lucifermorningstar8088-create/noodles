import pytest
from pydantic import SecretStr, ValidationError

from noodles.config import Settings


def test_loopback_is_the_default_bind_address() -> None:
    assert Settings().api_host == "127.0.0.1"


@pytest.mark.parametrize("host", ["0.0.0.0", "192.0.2.10", "example.com"])
def test_non_loopback_bind_requires_explicit_opt_in_and_token(host: str) -> None:
    with pytest.raises(ValidationError):
        Settings(api_host=host)
    with pytest.raises(ValidationError):
        Settings(api_host=host, api_allow_remote_bind=True)
    configured = Settings(
        api_host=host,
        api_allow_remote_bind=True,
        api_auth_token=SecretStr("x" * 40),
    )
    assert configured.api_allow_remote_bind is True


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "localhost"])
def test_loopback_bind_is_allowed(host: str) -> None:
    assert Settings(api_host=host).api_host == host


def test_short_auth_token_is_rejected() -> None:
    with pytest.raises(ValidationError, match="at least 32"):
        Settings(api_auth_token=SecretStr("too-short"))


def test_invalid_port_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(api_port=70000)

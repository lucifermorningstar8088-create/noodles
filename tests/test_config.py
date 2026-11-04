import pytest
from pydantic import ValidationError

from noodles.config import Settings


def test_loopback_is_the_default_bind_address() -> None:
    assert Settings().api_host == "127.0.0.1"


@pytest.mark.parametrize("host", ["0.0.0.0", "192.0.2.10", "example.com"])
def test_non_loopback_bind_is_rejected(host: str) -> None:
    with pytest.raises(ValidationError):
        Settings(api_host=host)


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "localhost"])
def test_loopback_bind_is_allowed(host: str) -> None:
    assert Settings(api_host=host).api_host == host


def test_invalid_port_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(api_port=70000)

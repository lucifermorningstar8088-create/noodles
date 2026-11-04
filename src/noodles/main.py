"""CLI entry point for the Noodles API."""

import uvicorn

from noodles.config import get_settings
from noodles.logging_config import configure_logging


def run() -> None:
    """Start the local API server."""
    settings = get_settings()
    configure_logging(settings.log_level)
    uvicorn.run(
        "noodles.api:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()

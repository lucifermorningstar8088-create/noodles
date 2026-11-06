"""Windows desktop entry point: embeds the local Noodles UI in a native WebView window."""

from __future__ import annotations

import logging
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import NoReturn

import uvicorn


def _log_path() -> Path:
    """Return a per-user log path without writing into the installation directory."""
    root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Noodles" / "logs"
    root.mkdir(parents=True, exist_ok=True)
    return root / "desktop.log"


def _show_error(message: str) -> None:
    """Show a Windows message box, with a console fallback for development."""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message, "Noodles", 0x10)
            return
        except (AttributeError, OSError):
            pass
    print(message, file=sys.stderr)


def _wait_until_ready(url: str, server_thread: threading.Thread, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if not server_thread.is_alive():
            raise RuntimeError("Noodles local API stopped before becoming ready.")
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
        time.sleep(0.25)
    raise RuntimeError(f"Noodles local API did not become ready in time: {last_error}")


def run() -> None:
    """Start the local API on a reserved loopback port and open the desktop window."""
    logging.basicConfig(
        filename=str(_log_path()),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    server: uvicorn.Server | None = None
    server_thread: threading.Thread | None = None
    listener: socket.socket | None = None
    try:
        import webview

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        port = int(listener.getsockname()[1])
        url = f"http://127.0.0.1:{port}/"

        config = uvicorn.Config(
            "noodles.api:create_app",
            factory=True,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False,
        )
        server = uvicorn.Server(config)
        server_thread = threading.Thread(
            target=server.run,
            kwargs={"sockets": [listener]},
            name="noodles-local-api",
            daemon=True,
        )
        server_thread.start()
        _wait_until_ready(url, server_thread)

        webview.create_window(
            "Noodles",
            url,
            width=1280,
            height=860,
            min_size=(900, 620),
            text_select=True,
        )
        webview.start(gui="edgechromium", debug=False)
    except Exception as exc:
        logging.exception("Noodles desktop startup failed")
        _show_error(
            "Noodles could not start. Check that Microsoft Edge WebView2 Runtime is "
            "installed, then review the log at:\n"
            f"{_log_path()}\n\nDetails: {exc}"
        )
        raise SystemExit(1) from exc
    finally:
        if server is not None:
            server.should_exit = True
        if listener is not None:
            try:
                listener.close()
            except OSError:
                logging.exception("Failed to close the local API socket")
        if server_thread is not None:
            server_thread.join(timeout=5)


if __name__ == "__main__":
    run()

"""Explicit local tool registry. Tools are Python callables, never model-generated code."""

from __future__ import annotations

import platform
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any


class ToolError(RuntimeError):
    """Raised for unknown or failed local tool calls."""


class LocalToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, tuple[str, Callable[[dict[str, Any]], Any]]] = {}
        self.register("system.time", "Return the local machine's current UTC time.", self._time)
        self.register("system.info", "Return basic local runtime platform information.", self._system_info)

    def register(self, name: str, description: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        if name in self._tools:
            raise ValueError(f"local tool already registered: {name}")
        self._tools[name] = (description, handler)

    def describe(self) -> list[dict[str, str]]:
        return [
            {"name": name, "description": desc}
            for name, (desc, _) in sorted(self._tools.items())
        ]

    def call(self, name: str, arguments: dict[str, Any]) -> Any:
        entry = self._tools.get(name)
        if entry is None:
            raise ToolError(f"unknown local tool: {name}")
        return entry[1](arguments)

    @staticmethod
    def _time(_: dict[str, Any]) -> dict[str, str]:
        return {"utc": datetime.now(UTC).isoformat()}

    @staticmethod
    def _system_info(_: dict[str, Any]) -> dict[str, str]:
        return {"platform": platform.platform(), "python": platform.python_version()}

"""Workspace-scoped file and command operations for local Coworkers."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


class WorkspaceError(RuntimeError):
    """Raised when a workspace operation is invalid or fails."""


class WorkspaceManager:
    """Restricts file access to one explicitly configured local workspace."""

    MAX_FILE_BYTES = 1_000_000
    MAX_TREE_ITEMS = 300
    MAX_OUTPUT_CHARS = 20_000
    ALLOWED_COMMANDS = {"python", "python3", "py", "pytest", "uv", "git", "npm", "node"}

    def __init__(self, root: Path, command_timeout: int = 120) -> None:
        self.root = root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.root.is_dir():
            raise WorkspaceError("workspace root must be a directory")
        self.command_timeout = max(5, min(command_timeout, 300))

    def _target(self, relative_path: str, *, must_exist: bool = False) -> Path:
        if not relative_path or len(relative_path) > 500 or "\x00" in relative_path:
            raise WorkspaceError("invalid workspace-relative path")
        if "\\" in relative_path:
            raise WorkspaceError("use forward slashes in workspace paths")
        candidate = PurePosixPath(relative_path)
        if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
            raise WorkspaceError("path must stay inside the workspace")
        target = self.root.joinpath(*candidate.parts)
        current = self.root
        for part in candidate.parts:
            current = current / part
            if current.is_symlink():
                raise WorkspaceError("symbolic links are not allowed in workspace paths")
        try:
            resolved = target.resolve(strict=must_exist)
            resolved.relative_to(self.root)
        except (OSError, ValueError) as exc:
            raise WorkspaceError("path is outside the workspace or unavailable") from exc
        return resolved

    def status(self) -> dict[str, Any]:
        return {"root": str(self.root), "exists": self.root.is_dir(), "local_only": True}

    def list_files(self) -> list[dict[str, Any]]:
        ignored = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache"}
        output: list[dict[str, Any]] = []
        for current, dirs, files in os.walk(self.root, followlinks=False):
            dirs[:] = sorted(
                name
                for name in dirs
                if (
                    name not in ignored
                    and not name.startswith(".")
                    and not (Path(current) / name).is_symlink()
                )
            )
            for name in sorted(files):
                if name.startswith("."):
                    continue
                path = Path(current) / name
                if path.is_symlink():
                    continue
                rel = path.relative_to(self.root).as_posix()
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                output.append({"path": rel, "size": size, "kind": "file"})
                if len(output) >= self.MAX_TREE_ITEMS:
                    return output
        return output

    def read_file(self, relative_path: str) -> str:
        target = self._target(relative_path, must_exist=True)
        if not target.is_file():
            raise WorkspaceError("requested path is not a file")
        if target.stat().st_size > self.MAX_FILE_BYTES:
            raise WorkspaceError("file exceeds the 1 MB inspection limit")
        try:
            return target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise WorkspaceError("file cannot be read as UTF-8 text") from exc

    def write_file(self, relative_path: str, content: str) -> dict[str, Any]:
        if len(content.encode("utf-8")) > self.MAX_FILE_BYTES:
            raise WorkspaceError("generated file exceeds the 1 MB write limit")
        target = self._target(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Re-check after directory creation to reduce symlink/path race exposure.
        target = self._target(relative_path)
        fd, temporary_name = tempfile.mkstemp(prefix=".noodles-", dir=target.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            raise WorkspaceError("file write failed") from exc
        return {"path": relative_path, "bytes_written": len(content.encode("utf-8"))}

    def run_command(self, argv: list[str]) -> dict[str, Any]:
        if (
            not argv
            or len(argv) > 32
            or any(not isinstance(arg, str) or len(arg) > 2000 for arg in argv)
        ):
            raise WorkspaceError("command must be an argument array with at most 32 arguments")
        if any("\x00" in arg for arg in argv):
            raise WorkspaceError("command arguments cannot contain NUL characters")
        executable = Path(argv[0]).name.lower()
        if executable.endswith(".exe"):
            executable = executable[:-4]
        if executable not in self.ALLOWED_COMMANDS:
            raise WorkspaceError("command executable is not in the local allowlist")
        resolved_executable = shutil.which(argv[0])
        if not resolved_executable:
            raise WorkspaceError(f"command executable is not installed: {executable}")
        try:
            completed = subprocess.run(
                [resolved_executable, *argv[1:]],
                cwd=self.root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.command_timeout,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            return {
                "argv": argv,
                "return_code": None,
                "timed_out": True,
                "stdout": str(stdout)[-self.MAX_OUTPUT_CHARS :],
                "stderr": str(stderr)[-self.MAX_OUTPUT_CHARS :],
            }
        except (OSError, ValueError) as exc:
            raise WorkspaceError("local command could not be started") from exc
        return {
            "argv": argv,
            "return_code": completed.returncode,
            "timed_out": False,
            "stdout": completed.stdout[-self.MAX_OUTPUT_CHARS :],
            "stderr": completed.stderr[-self.MAX_OUTPUT_CHARS :],
        }

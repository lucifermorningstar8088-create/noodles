from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from noodles.agent.coworkers import CoworkerManager
from noodles.workspace import WorkspaceError, WorkspaceManager


class FakeRuntime:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, str]:
        self.calls += 1
        if self.calls == 1:
            payload = {"summary": "Inspect the project entry point.", "inspect_paths": ["README.md"]}
        else:
            payload = {
                "summary": "Add a local test artifact.",
                "response": "I inspected the project README and prepared one file change.",
                "actions": [
                    {
                        "kind": "write_file",
                        "path": "notes/coworker.txt",
                        "content": "Created by an approved local Coworker.\n",
                        "reason": "Save the requested project note.",
                        "argv": [],
                    }
                ],
            }
        return {"content": json.dumps(payload)}


def test_workspace_reads_and_writes_only_relative_files(tmp_path: Path) -> None:
    manager = WorkspaceManager(tmp_path / "workspace")
    manager.write_file("src/example.txt", "hello")

    assert manager.read_file("src/example.txt") == "hello"
    assert manager.list_files()[0]["path"] == "src/example.txt"
    with pytest.raises(WorkspaceError):
        manager.read_file("../outside.txt")
    with pytest.raises(WorkspaceError):
        manager.write_file("../outside.txt", "no")


def test_workspace_rejects_symlink_paths(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    link = root / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is not available in this environment")

    manager = WorkspaceManager(root)
    with pytest.raises(WorkspaceError):
        manager.read_file("linked/secret.txt")


def test_workspace_commands_use_allowlist_and_no_shell(tmp_path: Path) -> None:
    manager = WorkspaceManager(tmp_path / "workspace")
    with pytest.raises(WorkspaceError):
        manager.run_command(["powershell", "-Command", "Write-Output unsafe"])


def test_coworker_plan_requires_approval_before_file_write(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "README.md").write_text("# Local project", encoding="utf-8")
    manager = CoworkerManager(FakeRuntime(), WorkspaceManager(root))  # type: ignore[arg-type]

    plan = manager.plan("Builder", "Create a short note file.")
    target = root / "notes" / "coworker.txt"

    assert plan["requires_approval"] is True
    assert not target.exists()
    with pytest.raises(Exception):
        manager.execute(plan["plan_id"], approved=False)
    assert not target.exists()

    result = manager.execute(plan["plan_id"], approved=True)

    assert result["status"] == "completed"
    assert target.read_text(encoding="utf-8") == "Created by an approved local Coworker.\n"
    with pytest.raises(Exception):
        manager.execute(plan["plan_id"], approved=True)

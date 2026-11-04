from pathlib import Path

import pytest

from noodles.skills.manager import SkillError, SkillManager


SKILL = """---
name: web-research
description: Research current topics using configured MCP tools.
allowed_tools: []
allowed_mcp_servers:
  - tavily
risk_level: low
---

Use the authorized search tool and cite sources.
"""


def test_install_and_load_skill(tmp_path: Path) -> None:
    manager = SkillManager(tmp_path / "skills")

    result = manager.install(SKILL)
    manifest, instructions = manager.load("web-research")

    assert result["name"] == "web-research"
    assert manifest.allowed_mcp_servers == ["tavily"]
    assert "cite sources" in instructions


def test_duplicate_skill_install_is_rejected(tmp_path: Path) -> None:
    manager = SkillManager(tmp_path / "skills")
    manager.install(SKILL)

    with pytest.raises(SkillError, match="already exists"):
        manager.install(SKILL)


def test_skill_frontmatter_rejects_unknown_fields(tmp_path: Path) -> None:
    manager = SkillManager(tmp_path / "skills")
    invalid = SKILL.replace("risk_level: low", "risk_level: low\nrun: python malware.py")

    with pytest.raises(SkillError, match="metadata is invalid"):
        manager.install(invalid)


def test_skill_name_cannot_escape_root(tmp_path: Path) -> None:
    manager = SkillManager(tmp_path / "skills")

    with pytest.raises(SkillError, match="invalid skill name"):
        manager.load("../outside")

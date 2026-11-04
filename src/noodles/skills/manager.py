"""Skill discovery, validation, and safe loading."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class SkillError(ValueError):
    """Raised when a skill is invalid or unavailable."""


class SkillManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    description: str = Field(min_length=8, max_length=500)
    version: str = Field(default="1.0.0", max_length=32)
    triggers: list[str] = Field(default_factory=list, max_length=30)
    allowed_tools: list[str] = Field(default_factory=list, max_length=50)
    allowed_mcp_servers: list[str] = Field(default_factory=list, max_length=30)
    risk_level: str = Field(default="low", pattern=r"^(low|medium|high)$")


class SkillManager:
    """Loads instruction-only SKILL.md files from a confined local directory."""

    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _parse(raw: str) -> tuple[SkillManifest, str]:
        if len(raw) > 64_000:
            raise SkillError("skill file exceeds 64 KB")
        match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", raw, re.S)
        if not match:
            raise SkillError("SKILL.md must start with YAML frontmatter delimited by ---")
        try:
            metadata = yaml.safe_load(match.group(1))
            manifest = SkillManifest.model_validate(metadata)
        except (yaml.YAMLError, ValidationError, TypeError) as exc:
            raise SkillError("skill metadata is invalid") from exc
        instructions = match.group(2).strip()
        if not instructions:
            raise SkillError("skill instructions cannot be empty")
        return manifest, instructions

    def install(self, raw: str) -> dict[str, Any]:
        manifest, _ = self._parse(raw)
        target_dir = self.root / manifest.name
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "SKILL.md"
        if target.exists():
            raise SkillError("skill already exists; use the explicit update operation")
        temporary = target.with_suffix(".md.tmp")
        temporary.write_text(raw, encoding="utf-8")
        temporary.replace(target)
        return manifest.model_dump()

    def update(self, name: str, raw: str) -> dict[str, Any]:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", name):
            raise SkillError("invalid skill name")
        manifest, _ = self._parse(raw)
        if manifest.name != name:
            raise SkillError("skill name in metadata must match target name")
        target_dir = (self.root / name).resolve()
        target_dir.relative_to(self.root)
        target = target_dir / "SKILL.md"
        if not target.is_file() or target.is_symlink():
            raise SkillError("skill does not exist")
        temporary = target.with_suffix(".md.tmp")
        temporary.write_text(raw, encoding="utf-8")
        temporary.replace(target)
        return manifest.model_dump()

    def list(self) -> list[dict[str, Any]]:
        skills: list[dict[str, Any]] = []
        for path in sorted(self.root.glob("*/SKILL.md")):
            if path.is_symlink() or not path.is_file():
                continue
            try:
                manifest, _ = self._parse(path.read_text(encoding="utf-8"))
            except (OSError, SkillError):
                continue
            skills.append(manifest.model_dump())
        return skills

    def load(self, name: str) -> tuple[SkillManifest, str]:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", name):
            raise SkillError("invalid skill name")
        target_dir = (self.root / name).resolve()
        try:
            target_dir.relative_to(self.root)
        except ValueError as exc:
            raise SkillError("skill path escaped skill root") from exc
        path = target_dir / "SKILL.md"
        if path.is_symlink() or not path.is_file():
            raise SkillError("skill not found")
        return self._parse(path.read_text(encoding="utf-8"))

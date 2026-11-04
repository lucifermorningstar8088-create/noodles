"""Skill-first local agent."""
from __future__ import annotations
import json
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from noodles.models.runtime import NativeModelRuntime
from noodles.skills.manager import SkillManager, SkillError
from noodles.tools.registry import LocalToolRegistry, ToolError
from noodles.mcp.manager import MCPManager, MCPError

class AgentError(RuntimeError):
    pass

class PlannedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str
    tool: str
    server: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    purpose: str = ""

class AgentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: str
    mode: str
    skill_names: list[str] = Field(default_factory=list)
    actions: list[PlannedAction] = Field(default_factory=list)
    answer: str | None = None

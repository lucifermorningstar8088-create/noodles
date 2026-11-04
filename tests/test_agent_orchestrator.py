import asyncio
import json
from pathlib import Path
from typing import Any

from noodles.agent.orchestrator import AgentOrchestrator
from noodles.skills.manager import SkillManager
from noodles.tools.registry import LocalToolRegistry


class FakeRuntime:
    def __init__(self) -> None:
        self.messages: list[list[dict[str, str]]] = []

    def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, str]:
        self.messages.append(messages)
        return {
            "content": json.dumps(
                {
                    "intent": "general knowledge question",
                    "mode": "answer",
                    "skill_names": [],
                    "mcp_servers": [],
                    "actions": [],
                    "answer": "A concise local answer.",
                }
            )
        }


class FakeMCPRegistry:
    def list(self) -> list[dict[str, Any]]:
        return [{"name": "tavily", "enabled": True, "trusted": True}]


class FakeMCPManager:
    registry = FakeMCPRegistry()

    async def list_tools(self, server_name: str) -> list[dict[str, Any]]:
        raise AssertionError("direct answers must not connect to MCP")

    async def call_tool(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise AssertionError("direct answers must not call MCP")


def test_direct_answer_does_not_connect_to_mcp(tmp_path: Path) -> None:
    runtime = FakeRuntime()
    agent = AgentOrchestrator(
        runtime,  # type: ignore[arg-type]
        SkillManager(Path(tmp_path) / "skills"),
        LocalToolRegistry(),
        FakeMCPManager(),  # type: ignore[arg-type]
    )

    result = asyncio.run(agent.chat("What is a prime number?", mode="auto"))

    assert result["route"] == "direct_answer"
    assert result["content"] == "A concise local answer."
    assert result["cloud_llm_fallback"] is False


def test_history_is_passed_to_local_planner(tmp_path: Path) -> None:
    runtime = FakeRuntime()
    agent = AgentOrchestrator(
        runtime,  # type: ignore[arg-type]
        SkillManager(Path(tmp_path) / "skills"),
        LocalToolRegistry(),
        FakeMCPManager(),  # type: ignore[arg-type]
    )
    history = [
        {"role": "user", "content": "My project is called Noodles."},
        {"role": "assistant", "content": "Understood."},
    ]

    asyncio.run(agent.chat("Continue the project.", history=history))

    payload = json.loads(runtime.messages[0][1]["content"])
    assert payload["conversation_history"] == history

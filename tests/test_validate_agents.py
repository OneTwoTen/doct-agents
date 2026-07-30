from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_agents.py"
SPEC = importlib.util.spec_from_file_location("validate_agents", MODULE_PATH)
validate_agents = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = validate_agents
SPEC.loader.exec_module(validate_agents)


def agent_text(
    name: str,
    *,
    tools: list[str] | None = None,
    agents: list[str] | None = None,
    user_invocable: bool = False,
) -> str:
    return "\n".join(
        [
            "---",
            f"name: {name}",
            f'description: "Agent {name}"',
            f"tools: {tools or []!r}",
            f"agents: {agents or []!r}",
            f"user-invocable: {'true' if user_invocable else 'false'}",
            "---",
            "",
            f"# {name}",
            "",
        ]
    )


class ValidateAgentsTest(unittest.TestCase):
    def validate_files(self, files: dict[str, str]) -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for filename, content in files.items():
                (root / filename).write_text(content, encoding="utf-8")
            return validate_agents.validate(root)

    def test_accepts_valid_orchestrator_and_worker(self) -> None:
        errors = self.validate_files(
            {
                "orchestrator.agent.md": agent_text(
                    "orchestrator",
                    tools=["agent", "read"],
                    agents=["worker"],
                    user_invocable=True,
                ),
                "worker.agent.md": agent_text("worker", tools=["read"]),
            }
        )
        self.assertEqual([], errors)

    def test_rejects_duplicate_names(self) -> None:
        errors = self.validate_files(
            {
                "one.agent.md": agent_text("worker"),
                "two.agent.md": agent_text("worker"),
            }
        )
        self.assertTrue(any("duplicate agent name 'worker'" in error for error in errors))

    def test_rejects_unknown_reference(self) -> None:
        errors = self.validate_files(
            {
                "orchestrator.agent.md": agent_text(
                    "orchestrator",
                    tools=["agent"],
                    agents=["missing"],
                    user_invocable=True,
                )
            }
        )
        self.assertTrue(any("unknown agent reference 'missing'" in error for error in errors))

    def test_rejects_self_reference(self) -> None:
        errors = self.validate_files(
            {
                "worker.agent.md": agent_text(
                    "worker", tools=["agent"], agents=["worker"]
                )
            }
        )
        self.assertTrue(any("cannot reference itself" in error for error in errors))

    def test_requires_agent_tool_for_handoff(self) -> None:
        errors = self.validate_files(
            {
                "orchestrator.agent.md": agent_text(
                    "orchestrator",
                    agents=["worker"],
                    user_invocable=True,
                ),
                "worker.agent.md": agent_text("worker"),
            }
        )
        self.assertTrue(any("requires the 'agent' tool" in error for error in errors))

    def test_rejects_unapproved_edit_execute_pair(self) -> None:
        errors = self.validate_files(
            {"worker.agent.md": agent_text("worker", tools=["edit", "execute"])}
        )
        self.assertTrue(any("edit+execute requires explicit allowlisting" in error for error in errors))

    def test_allows_test_agent_edit_execute_pair(self) -> None:
        errors = self.validate_files(
            {"test-agent.agent.md": agent_text("test-agent", tools=["edit", "execute"])}
        )
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()

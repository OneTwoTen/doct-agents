from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_agents.py"
SPEC = importlib.util.spec_from_file_location("validate_agents", MODULE_PATH)
validate_agents = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = validate_agents
SPEC.loader.exec_module(validate_agents)


def agent_text(
    name: str,
    *,
    tools: Optional[list[str]] = None,
    agents: Optional[list[str]] = None,
    user_invocable: bool = False,
    body: str = "",
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
            body,
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

    def test_rejects_worker_subagent_routing(self) -> None:
        errors = self.validate_files(
            {
                "orchestrator.agent.md": agent_text(
                    "orchestrator",
                    tools=["agent"],
                    agents=["worker", "peer"],
                    user_invocable=True,
                ),
                "worker.agent.md": agent_text(
                    "worker", tools=["agent"], agents=["peer"]
                ),
                "peer.agent.md": agent_text("peer", tools=["read"]),
            }
        )
        self.assertTrue(
            any("only orchestrator may reference subagents" in error for error in errors)
        )

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

    def test_rejects_nonstandard_declared_status_values(self) -> None:
        errors = self.validate_files(
            {
                "worker.agent.md": agent_text(
                    "worker",
                    tools=["read"],
                    body="- `Status`: `done | needs-fix | blocked`.",
                )
            }
        )

        self.assertTrue(any("unsupported status value 'done'" in error for error in errors))
        self.assertTrue(
            any("unsupported status value 'needs-fix'" in error for error in errors)
        )

    def test_rejects_unknown_declared_status_value(self) -> None:
        errors = self.validate_files(
            {
                "worker.agent.md": agent_text(
                    "worker",
                    tools=["read"],
                    body="- `Status`: `completed | retry-later | failed`.",
                )
            }
        )

        self.assertTrue(
            any("unsupported status value 'retry-later'" in error for error in errors)
        )

    def test_rejects_fully_unknown_declared_status_values(self) -> None:
        errors = self.validate_files(
            {
                "worker.agent.md": agent_text(
                    "worker",
                    tools=["read"],
                    body="- `Status`: `success | retry-later`.",
                )
            }
        )

        self.assertTrue(any("unsupported status value 'success'" in error for error in errors))
        self.assertTrue(
            any("unsupported status value 'retry-later'" in error for error in errors)
        )

    def test_accepts_common_declared_status_values(self) -> None:
        errors = self.validate_files(
            {
                "worker.agent.md": agent_text(
                    "worker",
                    tools=["read"],
                    body="- `Status`: `completed | needs-info | blocked | failed`.",
                )
            }
        )

        self.assertEqual([], errors)

    def test_accepts_docs_impact_status_values(self) -> None:
        errors = self.validate_files(
            {
                "orchestrator.agent.md": agent_text(
                    "orchestrator",
                    tools=["read"],
                    user_invocable=True,
                    body="- `Status`: `required | not-required | uncertain`.",
                )
            }
        )

        self.assertEqual([], errors)

    def test_repository_has_production_implementation_route(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        agents_directory = repository_root / "agents"
        implementation_path = agents_directory / "implementation-agent.agent.md"
        orchestrator_path = agents_directory / "orchestrator.agent.md"

        self.assertTrue(
            implementation_path.exists(),
            "production code changes need a dedicated implementation-agent",
        )
        implementation = validate_agents.parse_frontmatter(implementation_path)
        self.assertIn("edit", implementation["tools"])
        self.assertNotIn("agent", implementation["tools"])
        self.assertFalse(implementation["user-invocable"])

        orchestrator = validate_agents.parse_frontmatter(orchestrator_path)
        self.assertIn("implementation-agent", orchestrator["agents"])

        orchestrator_text = orchestrator_path.read_text(encoding="utf-8")
        self.assertIn("bắt buộc handoff sang `implementation-agent`", orchestrator_text)
        self.assertIn("không được trả patch hoặc code copy-paste", orchestrator_text)

    def test_repository_supports_long_running_workflow(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        agents_directory = repository_root / "agents"

        architecture_path = agents_directory / "architecture-agent.agent.md"
        planning_path = agents_directory / "planning-agent.agent.md"
        orchestrator_path = agents_directory / "orchestrator.agent.md"
        docs_path = agents_directory / "docs-agent.agent.md"
        implementation_path = agents_directory / "implementation-agent.agent.md"
        review_path = agents_directory / "review-agent.agent.md"

        self.assertTrue(architecture_path.exists())
        self.assertTrue(planning_path.exists())

        architecture = validate_agents.parse_frontmatter(architecture_path)
        planning = validate_agents.parse_frontmatter(planning_path)
        self.assertFalse(architecture["user-invocable"])
        self.assertFalse(planning["user-invocable"])
        self.assertNotIn("agent", architecture["tools"])
        self.assertNotIn("agent", planning["tools"])

        orchestrator = validate_agents.parse_frontmatter(orchestrator_path)
        self.assertIn("architecture-agent", orchestrator["agents"])
        self.assertIn("planning-agent", orchestrator["agents"])

        orchestrator_text = orchestrator_path.read_text(encoding="utf-8")
        self.assertIn("LONG_RUNNING", orchestrator_text)
        self.assertIn("DOCS_IMPACT", orchestrator_text)
        self.assertIn("independent-analysis", orchestrator_text)
        self.assertIn("autonomous blocker policy", orchestrator_text.lower())

        docs_text = docs_path.read_text(encoding="utf-8")
        implementation_text = implementation_path.read_text(encoding="utf-8")
        review_text = review_path.read_text(encoding="utf-8")
        self.assertIn("impact-update", docs_text)
        self.assertIn("Docs impact candidates", implementation_text)
        self.assertIn("`milestone`", review_text)
        self.assertIn("`final`", review_text)


if __name__ == "__main__":
    unittest.main()

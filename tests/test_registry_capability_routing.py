from __future__ import annotations

import unittest
from pathlib import Path


class RegistryCapabilityRoutingContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository_root = Path(__file__).resolve().parents[1]
        cls.agents_directory = cls.repository_root / "agents"
        cls.orchestrator_text = (
            cls.agents_directory / "orchestrator.agent.md"
        ).read_text(encoding="utf-8")
        cls.dependency_text = (
            cls.agents_directory / "dependency-agent.agent.md"
        ).read_text(encoding="utf-8")

    def test_orchestrator_delegates_missing_capability_before_asking_user(self) -> None:
        self.assertIn(
            "Thiếu tool trên orchestrator không phải blocker",
            self.orchestrator_text,
        )
        self.assertIn(
            "package metadata hoặc registry version",
            self.orchestrator_text,
        )
        self.assertIn("`dependency-agent`", self.orchestrator_text)
        self.assertIn("`research-agent`", self.orchestrator_text)

    def test_dependency_agent_can_query_registry_metadata_read_only(self) -> None:
        self.assertIn('tools: ["read", "search", "execute", "web"]', self.dependency_text)
        self.assertIn("registry metadata", self.dependency_text)
        self.assertIn("`npm view`", self.dependency_text)
        self.assertIn("read-only", self.dependency_text)

    def test_tool_approval_is_not_treated_as_a_preemptive_blocker(self) -> None:
        self.assertIn(
            "không tự suy rằng mình không có quyền trước khi gọi tool",
            self.orchestrator_text,
        )
        self.assertIn(
            "không hỏi user trước chỉ vì command cần network",
            self.dependency_text,
        )


if __name__ == "__main__":
    unittest.main()

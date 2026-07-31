from __future__ import annotations

import unittest
from pathlib import Path


class SkillRoutingContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.agents = self.root / "agents"

    def read_agent(self, name: str) -> str:
        return (self.agents / f"{name}.agent.md").read_text(encoding="utf-8")

    def test_orchestrator_limits_skill_composition_by_phase_and_evidence(self) -> None:
        text = self.read_agent("orchestrator")

        self.assertIn("tối đa một primary workflow skill", text)
        self.assertIn("tối đa một language skill và một framework skill", text)
        self.assertIn("file, dependency, import hoặc config thuộc scope", text)
        self.assertIn("3–4", text)
        self.assertIn("không được load phòng hờ", text)

    def test_workers_reference_workflow_skills_without_copying_full_procedures(self) -> None:
        review = self.read_agent("review-agent")
        implementation = self.read_agent("implementation-agent")
        cli = self.read_agent("cli-executor")
        authoring = self.read_agent("agent-authoring")

        self.assertIn("`code-review` làm primary workflow", review)
        self.assertIn("`implementation-workflow` làm primary workflow", implementation)
        self.assertIn("`verification-before-completion`", cli)
        self.assertIn("`skills/catalog.json`", authoring)

        for text in (review, implementation, cli):
            self.assertNotIn("# Code Review", text)
            self.assertNotIn("# Implementation Workflow", text)
            self.assertNotIn("# Verification Before Completion", text)

    def test_catalog_keeps_workflow_language_and_framework_separate(self) -> None:
        catalog = (self.root / "skills" / "catalog.json").read_text(encoding="utf-8")

        self.assertIn('"name": "code-review"', catalog)
        self.assertIn('"name": "implementation-workflow"', catalog)
        self.assertIn('"type": "language"', catalog)
        self.assertIn('"type": "framework"', catalog)
        self.assertNotIn("java-review", catalog)
        self.assertNotIn("spring-review", catalog)


if __name__ == "__main__":
    unittest.main()

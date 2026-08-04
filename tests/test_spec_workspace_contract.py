from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "agents"


class SpecWorkspaceContractTest(unittest.TestCase):
    def test_planning_agent_owns_executor_neutral_spec_workspace(self) -> None:
        text = (AGENTS / "planning-agent.agent.md").read_text(encoding="utf-8")

        self.assertIn(".doct/specs/<feature>/", text)
        for artifact in ("requirements.md", "design.md", "tasks.md", "progress.md"):
            self.assertIn(artifact, text)
        self.assertIn("WHAT", text)
        self.assertIn("HOW", text)
        self.assertIn("WORK", text)
        self.assertIn("STATE", text)
        self.assertNotIn("docs/superpowers/plans/YYYY-MM-DD-<feature>-implementation.md", text)

    def test_long_running_has_spec_review_executor_and_feature_lifecycle(self) -> None:
        text = (AGENTS / "orchestrator.agent.md").read_text(encoding="utf-8")

        for stage in (
            "REQUIREMENTS_REVIEW",
            "DESIGN_REVIEW",
            "SELECT_EXECUTOR",
            "FEATURE_IMPACT",
            "UPDATE_FEATURE_REGISTRY",
        ):
            self.assertIn(stage, text)
        self.assertIn(".doct/specs/<feature>/", text)
        self.assertIn("progress.md", text)
        self.assertIn("Feature impact candidates", text)

    def test_docs_agent_separates_public_docs_from_feature_registry(self) -> None:
        text = (AGENTS / "docs-agent.agent.md").read_text(encoding="utf-8")

        self.assertIn("feature-update", text)
        self.assertIn(".doct/features/index.md", text)
        self.assertIn(".doct/features/<feature>.md", text)
        self.assertIn("current-state", text)
        self.assertIn("không thay thế", text)

    def test_repository_bootstraps_project_and_feature_catalog(self) -> None:
        project = ROOT / ".doct" / "project.md"
        index = ROOT / ".doct" / "features" / "index.md"
        long_running = ROOT / ".doct" / "features" / "long-running.md"

        self.assertTrue(project.exists())
        self.assertTrue(index.exists())
        self.assertTrue(long_running.exists())

        index_text = index.read_text(encoding="utf-8")
        self.assertIn("LONG_RUNNING", index_text)
        self.assertIn("Feature", index_text)
        self.assertIn("Status", index_text)

        feature_text = long_running.read_text(encoding="utf-8")
        self.assertIn("Implemented", feature_text)
        self.assertIn("Not implemented", feature_text)
        self.assertIn("Related specs", feature_text)

    def test_readme_uses_doct_spec_workspace_as_canonical_long_running_state(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(".doct/specs/<feature>/", text)
        self.assertIn("FEATURE_IMPACT", text)
        self.assertIn("UPDATE_FEATURE_REGISTRY", text)
        self.assertNotIn(
            "Tiếp tục triển khai theo plan docs/superpowers/plans/",
            text,
        )


if __name__ == "__main__":
    unittest.main()

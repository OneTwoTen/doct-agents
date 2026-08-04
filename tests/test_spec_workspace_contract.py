from __future__ import annotations

import re
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
        for role in ("WHAT", "HOW", "WORK", "STATE"):
            self.assertIn(role, text)
        self.assertNotIn("docs/superpowers/plans/YYYY-MM-DD-<feature>-implementation.md", text)

    def test_long_running_has_review_executor_feature_and_checklist_lifecycle(self) -> None:
        text = (AGENTS / "orchestrator.agent.md").read_text(encoding="utf-8")

        for stage in (
            "REQUIREMENTS_REVIEW",
            "DESIGN_REVIEW",
            "SELECT_EXECUTOR",
            "CHECKLIST_RECONCILE",
            "FEATURE_IMPACT",
            "UPDATE_FEATURE_REGISTRY",
        ):
            self.assertIn(stage, text)
        self.assertIn(".doct/specs/<feature>/", text)
        self.assertIn("progress.md", text)
        self.assertIn("Feature impact candidates", text)
        self.assertIn("## Final reconciliation", text)
        self.assertIn("canonical spec còn drift", text)
        self.assertIn("validation revision", text)
        self.assertIn("Metadata-only reconciliation", text)
        self.assertIn("Status: completed", text)
        self.assertIn("downgrade `- [x]` về `- [ ]`", text)

    def test_planning_agent_defines_strict_authoritative_checklist(self) -> None:
        text = (AGENTS / "planning-agent.agent.md").read_text(encoding="utf-8")

        self.assertIn("authoritative", text)
        self.assertIn("- [ ]", text)
        self.assertIn("- [x]", text)
        self.assertIn("implementation evidence", text)
        self.assertIn("required validation", text)
        self.assertIn("blocked", text)
        self.assertIn("deferred", text)
        self.assertIn("Status: completed", text)
        self.assertIn("không sao chép toàn bộ checklist", text)

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

        project_text = project.read_text(encoding="utf-8")
        self.assertNotIn("## Current capabilities", project_text)
        self.assertIn(".doct/features/index.md", project_text)

        index_text = index.read_text(encoding="utf-8")
        self.assertIn("LONG_RUNNING", index_text)
        self.assertIn("Feature", index_text)
        self.assertIn("Status", index_text)

        feature_text = long_running.read_text(encoding="utf-8")
        self.assertIn("## Đã triển khai", feature_text)
        self.assertIn("## Chưa triển khai", feature_text)
        self.assertIn("## Related specs", feature_text)

    def test_tasks_is_authoritative_checklist_and_progress_is_journal(self) -> None:
        spec = ROOT / ".doct" / "specs" / "doct-spec-workspace"
        tasks = (spec / "tasks.md").read_text(encoding="utf-8")
        progress = (spec / "progress.md").read_text(encoding="utf-8")

        self.assertIn("Status: implementing", tasks)
        self.assertIn("Status: implementing", progress)
        self.assertIn("authoritative completion ledger", tasks)
        self.assertRegex(tasks, r"- \[ \] `M1-T1`")
        self.assertIn("Current checklist item", progress)
        self.assertNotRegex(progress, re.compile(r"^- \[[ x]\] `M\d+-T\d+`", re.MULTILINE))

    def test_readme_uses_doct_workspace_and_preserves_browser_loop(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(".doct/specs/<feature>/", text)
        self.assertIn("CHECKLIST_RECONCILE", text)
        self.assertIn("FEATURE_IMPACT", text)
        self.assertIn("UPDATE_FEATURE_REGISTRY", text)
        self.assertIn("browser-driven", text)
        self.assertIn("implementation-agent", text)
        self.assertIn("browser-agent", text)
        self.assertNotIn("Tiếp tục triển khai theo plan docs/superpowers/plans/", text)


if __name__ == "__main__":
    unittest.main()

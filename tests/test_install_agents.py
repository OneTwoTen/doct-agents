from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "install.py"
SPEC = importlib.util.spec_from_file_location("doct_agents_installer", MODULE_PATH)
installer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(installer)


class InstallAgentsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.source = self.root / "source"
        self.target = self.root / "target"
        self.source.mkdir()
        (self.source / "orchestrator.agent.md").write_text(
            "---\nname: orchestrator\n---\n", encoding="utf-8"
        )
        (self.source / "review-agent.agent.md").write_text(
            "---\nname: review-agent\n---\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_install_copies_agents_and_writes_manifest(self) -> None:
        result = installer.install_agents(self.source, self.target)

        self.assertEqual(2, result.installed)
        self.assertTrue((self.target / "orchestrator.agent.md").exists())
        manifest = json.loads((self.target / installer.MANIFEST_NAME).read_text("utf-8"))
        self.assertEqual(
            ["orchestrator.agent.md", "review-agent.agent.md"],
            sorted(manifest["files"]),
        )

    def test_install_rejects_unmanaged_conflict_without_force(self) -> None:
        self.target.mkdir()
        (self.target / "orchestrator.agent.md").write_text("custom", encoding="utf-8")

        with self.assertRaises(installer.InstallConflict):
            installer.install_agents(self.source, self.target)

        self.assertEqual(
            "custom",
            (self.target / "orchestrator.agent.md").read_text(encoding="utf-8"),
        )

    def test_update_rejects_locally_modified_managed_file_without_force(self) -> None:
        installer.install_agents(self.source, self.target)
        (self.target / "orchestrator.agent.md").write_text("local edit", encoding="utf-8")
        (self.source / "orchestrator.agent.md").write_text("upstream", encoding="utf-8")

        with self.assertRaises(installer.InstallConflict):
            installer.install_agents(self.source, self.target)

    def test_force_update_replaces_modified_managed_file(self) -> None:
        installer.install_agents(self.source, self.target)
        (self.target / "orchestrator.agent.md").write_text("local edit", encoding="utf-8")
        (self.source / "orchestrator.agent.md").write_text("upstream", encoding="utf-8")

        result = installer.install_agents(self.source, self.target, force=True)

        self.assertEqual(2, result.installed)
        self.assertEqual(
            "upstream",
            (self.target / "orchestrator.agent.md").read_text(encoding="utf-8"),
        )

    def test_uninstall_preserves_modified_files(self) -> None:
        installer.install_agents(self.source, self.target)
        (self.target / "review-agent.agent.md").write_text("local edit", encoding="utf-8")

        result = installer.uninstall_agents(self.target)

        self.assertEqual(1, result.removed)
        self.assertEqual(["review-agent.agent.md"], result.preserved)
        self.assertFalse((self.target / "orchestrator.agent.md").exists())
        self.assertTrue((self.target / "review-agent.agent.md").exists())

    def test_status_reports_modified_and_missing_files(self) -> None:
        installer.install_agents(self.source, self.target)
        (self.target / "orchestrator.agent.md").write_text("changed", encoding="utf-8")
        (self.target / "review-agent.agent.md").unlink()

        status = installer.get_status(self.target)

        self.assertEqual(["orchestrator.agent.md"], status.modified)
        self.assertEqual(["review-agent.agent.md"], status.missing)


if __name__ == "__main__":
    unittest.main()

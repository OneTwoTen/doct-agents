from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
import zipfile
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

    def write_manifest(self, target: Path, manifest: dict[str, object]) -> None:
        target.mkdir(parents=True, exist_ok=True)
        (target / installer.MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

    def test_install_copies_agents_and_writes_canonical_manifest(self) -> None:
        result = installer.install_agents(self.source, self.target)

        self.assertEqual(2, result.installed)
        self.assertTrue((self.target / "orchestrator.agent.md").exists())
        manifest = installer.load_manifest(self.target)
        self.assertEqual(1, manifest["schema"])
        self.assertEqual("doct-agents", manifest["package"])
        self.assertEqual(installer.PACKAGE_VERSION, manifest["version"])
        self.assertEqual("OneTwoTen/doct-agents", manifest["repository"])
        self.assertEqual(
            ["orchestrator.agent.md", "review-agent.agent.md"],
            sorted(manifest["files"]),
        )

    def test_install_uses_downloaded_source_package_version(self) -> None:
        (self.source.parent / "package.json").write_text(
            json.dumps({"name": "doct-agents", "version": "1.2.3"}),
            encoding="utf-8",
        )

        installer.install_agents(self.source, self.target)

        self.assertEqual("1.2.3", installer.load_manifest(self.target)["version"])

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

    def test_partial_uninstall_preserves_installed_version(self) -> None:
        installer.install_agents(self.source, self.target)
        manifest = installer.load_manifest(self.target)
        manifest["version"] = "0.3.0"
        self.write_manifest(self.target, manifest)
        (self.target / "review-agent.agent.md").write_text("local edit", encoding="utf-8")

        installer.uninstall_agents(self.target)

        self.assertEqual("0.3.0", installer.load_manifest(self.target)["version"])

    def test_status_reports_modified_and_missing_files(self) -> None:
        installer.install_agents(self.source, self.target)
        (self.target / "orchestrator.agent.md").write_text("changed", encoding="utf-8")
        (self.target / "review-agent.agent.md").unlink()

        status = installer.get_status(self.target)

        self.assertEqual(installer.PACKAGE_VERSION, status.version)
        self.assertEqual(["orchestrator.agent.md"], status.modified)
        self.assertEqual(["review-agent.agent.md"], status.missing)

    def test_status_reports_unknown_version_for_legacy_manifest(self) -> None:
        self.target.mkdir()
        destination = self.target / "orchestrator.agent.md"
        destination.write_text("installed", encoding="utf-8")
        self.write_manifest(
            self.target,
            {
                "schema": 1,
                "package": "doct-agents",
                "repository": installer.REPOSITORY,
                "files": {"orchestrator.agent.md": installer.sha256(destination)},
            },
        )

        self.assertIsNone(installer.get_status(self.target).version)

    def test_manifest_rejects_parent_traversal_before_force_uninstall(self) -> None:
        outside = self.root / "outside.agent.md"
        outside.write_text("keep", encoding="utf-8")
        self.write_manifest(
            self.target,
            {
                "schema": 1,
                "repository": installer.REPOSITORY,
                "files": {"../outside.agent.md": installer.sha256(outside)},
            },
        )

        with self.assertRaises(installer.InstallConflict):
            installer.uninstall_agents(self.target, force=True)

        self.assertEqual("keep", outside.read_text(encoding="utf-8"))

    def test_manifest_rejects_absolute_paths(self) -> None:
        outside = (self.root / "absolute.agent.md").resolve()
        outside.write_text("keep", encoding="utf-8")
        self.write_manifest(
            self.target,
            {
                "schema": 1,
                "package": "doct-agents",
                "files": {str(outside): installer.sha256(outside)},
            },
        )

        with self.assertRaises(installer.InstallConflict):
            installer.get_status(self.target)

    def test_manifest_rejects_unsupported_schema_and_invalid_checksum(self) -> None:
        self.write_manifest(
            self.target,
            {
                "schema": 2,
                "package": "doct-agents",
                "files": {"orchestrator.agent.md": "0" * 64},
            },
        )
        with self.assertRaises(installer.InstallConflict):
            installer.load_manifest(self.target)

        self.write_manifest(
            self.target,
            {
                "schema": 1,
                "package": "doct-agents",
                "files": {"orchestrator.agent.md": "not-a-sha256"},
            },
        )
        with self.assertRaises(installer.InstallConflict):
            installer.load_manifest(self.target)

    def test_manifest_accepts_legacy_package_or_repository_identifier(self) -> None:
        identities = (
            {"package": "doct-agents"},
            {"repository": installer.REPOSITORY},
        )
        for index, identity in enumerate(identities):
            with self.subTest(identity=identity):
                target = self.root / f"legacy-{index}"
                target.mkdir()
                destination = target / "orchestrator.agent.md"
                destination.write_text("installed", encoding="utf-8")
                self.write_manifest(
                    target,
                    {
                        "schema": 1,
                        **identity,
                        "files": {
                            "orchestrator.agent.md": installer.sha256(destination)
                        },
                    },
                )

                self.assertEqual(
                    ["orchestrator.agent.md"], installer.get_status(target).installed
                )

    def test_update_removes_unchanged_obsolete_managed_agents(self) -> None:
        installer.install_agents(self.source, self.target)
        (self.source / "review-agent.agent.md").unlink()

        installer.install_agents(self.source, self.target)

        self.assertFalse((self.target / "review-agent.agent.md").exists())
        manifest = installer.load_manifest(self.target)
        self.assertNotIn("review-agent.agent.md", manifest["files"])

    def test_update_preserves_modified_obsolete_agents_and_keeps_them_managed(self) -> None:
        installer.install_agents(self.source, self.target)
        destination = self.target / "review-agent.agent.md"
        destination.write_text("local edit", encoding="utf-8")
        (self.source / "review-agent.agent.md").unlink()

        installer.install_agents(self.source, self.target)

        self.assertEqual("local edit", destination.read_text(encoding="utf-8"))
        self.assertEqual(
            ["review-agent.agent.md"], installer.get_status(self.target).modified
        )
        manifest = installer.load_manifest(self.target)
        self.assertIn("review-agent.agent.md", manifest["files"])

    @unittest.skipIf(os.name == "nt", "creating file symlinks requires Windows privileges")
    def test_install_rejects_symbolic_link_destination_even_with_force(self) -> None:
        self.target.mkdir()
        outside = self.root / "outside.agent.md"
        outside.write_text("outside", encoding="utf-8")
        (self.target / "orchestrator.agent.md").symlink_to(outside)

        with self.assertRaisesRegex(installer.InstallConflict, "symbolic link"):
            installer.install_agents(self.source, self.target, force=True)

        self.assertEqual("outside", outside.read_text(encoding="utf-8"))

    @unittest.skipIf(os.name == "nt", "creating directory symlinks requires Windows privileges")
    def test_install_rejects_symbolic_link_ancestor_before_creating_target(self) -> None:
        outside = self.root / "outside"
        workspace = self.root / "workspace"
        outside.mkdir()
        workspace.mkdir()
        (workspace / ".github").symlink_to(outside, target_is_directory=True)
        target = workspace / ".github" / "agents"

        with self.assertRaisesRegex(installer.InstallConflict, "symbolic link"):
            installer.install_agents(self.source, target)

        self.assertFalse((outside / "agents").exists())

    @unittest.skipIf(os.name == "nt", "permission-based copy failure is POSIX-specific")
    def test_update_stages_every_source_before_mutating_target(self) -> None:
        installer.install_agents(self.source, self.target)
        manifest_path = self.target / installer.MANIFEST_NAME
        original_manifest = manifest_path.read_text(encoding="utf-8")
        (self.source / "orchestrator.agent.md").write_text("upstream", encoding="utf-8")
        unreadable = self.source / "review-agent.agent.md"
        unreadable.chmod(0)

        try:
            with self.assertRaises(OSError):
                installer.install_agents(self.source, self.target)
        finally:
            unreadable.chmod(0o600)

        self.assertEqual(
            "---\nname: orchestrator\n---\n",
            (self.target / "orchestrator.agent.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            "---\nname: review-agent\n---\n",
            (self.target / "review-agent.agent.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(original_manifest, manifest_path.read_text(encoding="utf-8"))

    def test_safe_extract_rejects_parent_traversal(self) -> None:
        archive_path = self.root / "unsafe.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("../escaped.txt", "escape")

        with zipfile.ZipFile(archive_path) as archive:
            with self.assertRaisesRegex(RuntimeError, "unsafe archive member"):
                installer.safe_extract_archive(archive, self.root / "extract")

        self.assertFalse((self.root / "escaped.txt").exists())

    def test_safe_extract_rejects_symbolic_link_members(self) -> None:
        archive_path = self.root / "symlink.zip"
        link = zipfile.ZipInfo("agents/link.agent.md")
        link.create_system = 3
        link.external_attr = 0o120777 << 16
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr(link, "target")

        with zipfile.ZipFile(archive_path) as archive:
            with self.assertRaisesRegex(RuntimeError, "symbolic link"):
                installer.safe_extract_archive(archive, self.root / "extract")


if __name__ == "__main__":
    unittest.main()

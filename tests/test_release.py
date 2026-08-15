from __future__ import annotations

import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_release.py"
SPEC = importlib.util.spec_from_file_location("check_release", MODULE_PATH)
check_release = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(check_release)


class CheckReleaseTest(unittest.TestCase):
    def test_repository_package_version_matches_latest_release(self) -> None:
        package_path = Path(__file__).resolve().parents[1] / "package.json"

        self.assertEqual("0.4.2", check_release.read_package_version(package_path))

    def test_read_package_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package_path = Path(temp_dir) / "package.json"
            package_path.write_text(
                json.dumps({"name": "doct-agents", "version": "1.2.3"}),
                encoding="utf-8",
            )

            self.assertEqual("1.2.3", check_release.read_package_version(package_path))

    def test_accepts_matching_release_tag(self) -> None:
        check_release.validate_release_tag("v1.2.3", "1.2.3")

    def test_rejects_mismatched_release_tag(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not match package version"):
            check_release.validate_release_tag("v1.2.4", "1.2.3")

    def test_rejects_tag_without_v_prefix(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected v1.2.3"):
            check_release.validate_release_tag("1.2.3", "1.2.3")

    def test_rejects_missing_release_tag(self) -> None:
        with self.assertRaisesRegex(ValueError, "release tag is required"):
            check_release.validate_release_tag(None, "1.2.3")

    def test_publish_workflow_checks_out_and_validates_explicit_tag(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "publish-npm.yml"
        ).read_text(encoding="utf-8")

        self.assertRegex(
            workflow,
            re.compile(
                r"workflow_dispatch:\s+inputs:\s+tag:\s+description:.*?required:\s*true",
                re.DOTALL,
            ),
        )
        self.assertGreaterEqual(
            workflow.count("github.event.release.tag_name || inputs.tag"),
            2,
        )


if __name__ == "__main__":
    unittest.main()

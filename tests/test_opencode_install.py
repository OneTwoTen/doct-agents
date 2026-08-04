from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "install.py"
SPEC = importlib.util.spec_from_file_location("doct_agents_opencode_installer", MODULE_PATH)
installer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(installer)


def source_agent(
    *,
    name: str,
    description: str | None = None,
    tools: list[str] | None = None,
    agents: list[str] | None = None,
    user_invocable: bool = False,
    body: str = "body\n",
) -> str:
    description = description or name
    tools = tools or []
    agents = agents or []
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {json.dumps(description)}\n"
        f"tools: {json.dumps(tools)}\n"
        f"agents: {json.dumps(agents)}\n"
        f"user-invocable: {'true' if user_invocable else 'false'}\n"
        "---\n\n"
        f"{body}"
    )


class OpenCodeInstallerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.source = self.root / "source"
        self.target = self.root / ".opencode" / "agents"
        self.source.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_opencode_targets_preserve_legacy_copilot_defaults(self) -> None:
        self.assertEqual(
            Path("/home/dev/.copilot/agents"),
            installer.default_target("user", Path("/repo"), platform="copilot", home=Path("/home/dev")),
        )
        self.assertEqual(
            Path("/repo/.github/agents"),
            installer.default_target("workspace", Path("/repo"), platform="copilot", home=Path("/home/dev")),
        )
        self.assertEqual(
            Path("/home/dev/.config/opencode/agents"),
            installer.default_target("user", Path("/repo"), platform="opencode", home=Path("/home/dev")),
        )
        self.assertEqual(
            Path("/repo/.opencode/agents"),
            installer.default_target("workspace", Path("/repo"), platform="opencode", home=Path("/home/dev")),
        )

    def test_renderer_maps_orchestrator_and_worker_permissions(self) -> None:
        rendered_name, rendered = installer.render_opencode_agent(
            source_agent(
                name="orchestrator",
                description="route work",
                tools=["agent", "read", "search", "todo", "vscode/askQuestions"],
                agents=["review-agent", "implementation-agent"],
                user_invocable=True,
            ),
            "orchestrator.agent.md",
        )
        self.assertEqual("orchestrator.md", rendered_name)
        for part in (
            'description: "route work"',
            "mode: primary",
            "read: allow",
            "glob: allow",
            "grep: allow",
            "todowrite: allow",
            "question: allow",
            "edit: deny",
            "bash: deny",
            '"*": deny',
            '"review-agent": allow',
            '"implementation-agent": allow',
            '"doct_playwright_*": deny',
            "body\n",
        ):
            self.assertIn(part, rendered)
        for copilot_key in ("name:", "tools:", "agents:", "user-invocable:", "argument-hint:"):
            self.assertNotIn(copilot_key, rendered)

        _, implementation = installer.render_opencode_agent(
            source_agent(name="implementation-agent", tools=["read", "search", "edit"]),
            "implementation-agent.agent.md",
        )
        self.assertIn("mode: subagent", implementation)
        self.assertIn("hidden: true", implementation)
        self.assertIn("edit: allow", implementation)
        self.assertIn("bash: deny", implementation)
        self.assertIn("task: deny", implementation)

        _, browser = installer.render_opencode_agent(
            source_agent(name="browser-agent", tools=["read", "search", "execute", "openBrowserPage"]),
            "browser-agent.agent.md",
        )
        self.assertIn('"doct_playwright_*": allow', browser)

    def test_schema_2_manages_opencode_markdown_files(self) -> None:
        (self.source / "orchestrator.md").write_text("rendered\n", encoding="utf-8")
        installer.install_agents(
            self.source,
            self.target,
            platform="opencode",
            manifest_metadata={
                "config": {
                    "filename": "opencode.json",
                    "mcpEntrySha256": "0" * 64,
                }
            },
        )
        manifest = installer.load_manifest(self.target, platform="opencode")
        self.assertEqual(2, manifest["schema"])
        self.assertEqual("opencode", manifest["platform"])
        self.assertEqual("opencode.json", manifest["config"]["filename"])
        self.assertEqual([], installer.get_status(self.target, platform="opencode").modified)

        (self.target / "orchestrator.md").write_text("changed\n", encoding="utf-8")
        self.assertEqual(
            ["orchestrator.md"], installer.get_status(self.target, platform="opencode").modified
        )
        installer.uninstall_agents(self.target, platform="opencode", force=True)

    def test_playwright_mcp_is_pinned_isolated_and_preserves_json(self) -> None:
        self.assertEqual(
            {
                "type": "local",
                "command": ["npx", "-y", "@playwright/mcp@0.0.78", "--isolated"],
                "enabled": True,
            },
            installer.PLAYWRIGHT_MCP,
        )
        text = json.dumps(
            {
                "model": "example/model",
                "mcp": {"other": {"type": "local", "command": ["other"]}},
            },
            indent=2,
        ) + "\n"
        patched = installer.patch_opencode_config(text)
        parsed = json.loads(patched.text)
        self.assertEqual("example/model", parsed["model"])
        self.assertEqual(["other"], parsed["mcp"]["other"]["command"])
        self.assertEqual(installer.PLAYWRIGHT_MCP, parsed["mcp"]["doct_playwright"])
        self.assertRegex(patched.mcp_entry_sha256, r"^[a-f0-9]{64}$")

        removed = installer.patch_opencode_config(
            patched.text,
            expected_hash=patched.mcp_entry_sha256,
            remove=True,
        )
        self.assertNotIn("doct_playwright", json.loads(removed.text)["mcp"])

    def test_jsonc_patch_preserves_comments_trailing_commas_and_other_mcp(self) -> None:
        text = """{
  // keep this comment
  "model": "example/model",
  "mcp": {
    "other": {
      "type": "local",
      "command": ["other"],
    },
  },
}
"""
        patched = installer.patch_opencode_config(text)
        self.assertIn("// keep this comment", patched.text)
        self.assertIn('"other"', patched.text)
        self.assertIn('"doct_playwright"', patched.text)

        removed = installer.patch_opencode_config(
            patched.text,
            expected_hash=patched.mcp_entry_sha256,
            remove=True,
        )
        self.assertIn("// keep this comment", removed.text)
        self.assertIn('"other"', removed.text)
        self.assertNotIn('"doct_playwright"', removed.text)

    def test_modified_mcp_entry_is_protected_without_force(self) -> None:
        installed = installer.patch_opencode_config("{}\n")
        customized = installed.text.replace("--isolated", "--headless")
        with self.assertRaisesRegex(installer.InstallConflict, "modified"):
            installer.patch_opencode_config(
                customized,
                expected_hash=installed.mcp_entry_sha256,
            )
        forced = installer.patch_opencode_config(
            customized,
            expected_hash=installed.mcp_entry_sha256,
            force=True,
        )
        self.assertIn("--isolated", forced.text)

    def test_opencode_config_path_prefers_jsonc(self) -> None:
        config_dir = self.target.parent
        config_dir.mkdir(parents=True, exist_ok=True)
        self.assertEqual(config_dir / "opencode.json", installer.opencode_config_path(self.target))
        (config_dir / "opencode.jsonc").write_text("{}\n", encoding="utf-8")
        self.assertEqual(config_dir / "opencode.jsonc", installer.opencode_config_path(self.target))

    def test_detection_recognizes_path_command_and_workspace_directory(self) -> None:
        bin_dir = self.root / "bin"
        workspace = self.root / "workspace"
        home = self.root / "home"
        empty_bin = self.root / "empty-bin"
        for path in (bin_dir, workspace, home, empty_bin):
            path.mkdir(parents=True)

        executable_name = "opencode.cmd" if os.name == "nt" else "opencode"
        executable = bin_dir / executable_name
        executable.write_text("@echo off\n" if os.name == "nt" else "#!/bin/sh\n", encoding="utf-8")
        if os.name != "nt":
            executable.chmod(0o755)

        self.assertTrue(
            installer.detect_opencode(workspace=workspace, home=home, path_env=str(bin_dir))
        )
        self.assertFalse(
            installer.detect_opencode(workspace=workspace, home=home, path_env=str(empty_bin))
        )
        (workspace / ".opencode").mkdir()
        self.assertTrue(
            installer.detect_opencode(workspace=workspace, home=home, path_env=str(empty_bin))
        )


if __name__ == "__main__":
    unittest.main()

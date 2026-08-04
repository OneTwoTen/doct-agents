from __future__ import annotations

import contextlib
import importlib.util
import io
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

    def run_main(self, args: list[str]) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return installer.main(args)

    def write_cli_source(self) -> None:
        (self.source / "orchestrator.agent.md").write_text(
            source_agent(
                name="orchestrator",
                description="route work",
                tools=["agent", "read", "search", "todo", "vscode/askQuestions"],
                agents=["cli-executor"],
                user_invocable=True,
            ),
            encoding="utf-8",
        )
        (self.source / "cli-executor.agent.md").write_text(
            source_agent(
                name="cli-executor",
                tools=["execute", "read"],
                user_invocable=True,
            ),
            encoding="utf-8",
        )

    def test_opencode_targets_preserve_legacy_copilot_defaults(self) -> None:
        home = Path("/home/dev")
        workspace = Path("/repo")
        self.assertEqual(
            installer.normalize_target(home / ".copilot" / "agents"),
            installer.default_target("user", workspace, platform="copilot", home=home),
        )
        self.assertEqual(
            installer.normalize_target(workspace) / ".github" / "agents",
            installer.default_target("workspace", workspace, platform="copilot", home=home),
        )
        self.assertEqual(
            installer.normalize_target(home / ".config" / "opencode" / "agents"),
            installer.default_target("user", workspace, platform="opencode", home=home),
        )
        self.assertEqual(
            installer.normalize_target(workspace) / ".opencode" / "agents",
            installer.default_target("workspace", workspace, platform="opencode", home=home),
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

    def test_cli_explicit_opencode_install_status_uninstall(self) -> None:
        self.write_cli_source()
        workspace = self.root / "workspace-explicit"
        workspace.mkdir()
        base = ["--platform", "opencode", "--scope", "workspace", "--workspace", str(workspace)]
        self.assertEqual(0, self.run_main(["install", *base, "--source-dir", str(self.source)]))

        agent = workspace / ".opencode" / "agents" / "orchestrator.md"
        config = workspace / ".opencode" / "opencode.json"
        self.assertTrue(agent.exists())
        self.assertEqual(PLAYWRIGHT_MCP := installer.PLAYWRIGHT_MCP, json.loads(config.read_text(encoding="utf-8"))["mcp"]["doct_playwright"])
        self.assertEqual(0, self.run_main(["status", *base]))
        self.assertEqual(0, self.run_main(["uninstall", *base]))
        self.assertFalse(agent.exists())
        self.assertNotIn("doct_playwright", json.loads(config.read_text(encoding="utf-8"))["mcp"])
        self.assertEqual(installer.PLAYWRIGHT_MCP, PLAYWRIGHT_MCP)

    def test_cli_all_installs_both_and_legacy_uninstall_is_copilot_only(self) -> None:
        self.write_cli_source()
        workspace = self.root / "workspace-all"
        workspace.mkdir()
        self.assertEqual(
            0,
            self.run_main([
                "install", "--platform", "all", "--scope", "workspace", "--workspace", str(workspace),
                "--source-dir", str(self.source),
            ]),
        )
        copilot = workspace / ".github" / "agents" / "orchestrator.agent.md"
        opencode = workspace / ".opencode" / "agents" / "orchestrator.md"
        self.assertTrue(copilot.exists())
        self.assertTrue(opencode.exists())

        self.assertEqual(0, self.run_main(["uninstall", "--scope", "workspace", "--workspace", str(workspace)]))
        self.assertFalse(copilot.exists())
        self.assertTrue(opencode.exists())
        self.assertEqual(
            0,
            self.run_main(["uninstall", "--platform", "opencode", "--scope", "workspace", "--workspace", str(workspace)]),
        )

    def test_cli_auto_detect_adds_opencode_to_copilot_install(self) -> None:
        self.write_cli_source()
        workspace = self.root / "workspace-auto"
        (workspace / ".opencode").mkdir(parents=True)
        self.assertEqual(
            0,
            self.run_main([
                "install", "--scope", "workspace", "--workspace", str(workspace), "--source-dir", str(self.source),
            ]),
        )
        self.assertTrue((workspace / ".github" / "agents" / "orchestrator.agent.md").exists())
        self.assertTrue((workspace / ".opencode" / "agents" / "orchestrator.md").exists())


if __name__ == "__main__":
    unittest.main()

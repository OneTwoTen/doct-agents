from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_agents.py"
SPEC = importlib.util.spec_from_file_location("validate_agents_opencode", MODULE_PATH)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

OUTCOME = "- `Outcome`: `passed | change-made | defect-found | validation-failed | no-change`."


def agent_text(name: str, tools: list[str]) -> str:
    return "\n".join(
        [
            "---",
            f"name: {name}",
            f'description: "Agent {name}"',
            f"tools: {tools!r}",
            "agents: []",
            "user-invocable: false",
            "---",
            "",
            f"# {name}",
            "",
            OUTCOME,
        ]
    )


class OpenCodeSourceValidationTest(unittest.TestCase):
    def validate_one(self, name: str, tools: list[str]) -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / f"{name}.agent.md").write_text(
                agent_text(name, tools), encoding="utf-8"
            )
            return validator.validate(root)

    def test_rejects_unknown_source_tool_that_cannot_render_to_opencode(self) -> None:
        errors = self.validate_one("worker", ["read", "unknownTool"])
        self.assertTrue(
            any(
                "OpenCode" in error and "unsupported source tool 'unknownTool'" in error
                for error in errors
            )
        )

    def test_rejects_browser_runtime_tool_on_non_browser_agent(self) -> None:
        errors = self.validate_one("worker", ["read", "openBrowserPage"])
        self.assertTrue(
            any(
                "browser runtime tool 'openBrowserPage' is only allowed for browser-agent"
                in error
                for error in errors
            )
        )

    def test_accepts_browser_runtime_tools_for_browser_agent(self) -> None:
        errors = self.validate_one(
            "browser-agent",
            [
                "read",
                "search",
                "execute",
                "openBrowserPage",
                "navigatePage",
                "readPage",
                "screenshotPage",
                "clickElement",
                "hoverElement",
                "dragElement",
                "typeInPage",
                "handleDialog",
                "runPlaywrightCode",
            ],
        )
        opencode_errors = [error for error in errors if "OpenCode" in error or "browser runtime" in error]
        self.assertEqual([], opencode_errors)

    def test_repository_sources_are_opencode_renderable(self) -> None:
        root = Path(__file__).resolve().parents[1] / "agents"
        errors = validator.validate(root)
        opencode_errors = [error for error in errors if "OpenCode" in error or "browser runtime" in error]
        self.assertEqual([], opencode_errors)


if __name__ == "__main__":
    unittest.main()

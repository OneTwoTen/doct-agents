from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_agents.py"
SPEC = importlib.util.spec_from_file_location("validate_agents", MODULE_PATH)
validate_agents = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = validate_agents
SPEC.loader.exec_module(validate_agents)

COMMON_OUTCOME = "- `Outcome`: `passed | change-made | defect-found | validation-failed | no-change`."
BROWSER_TOOLS = {
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
}


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
            COMMON_OUTCOME,
        ]
    )


class BrowserCapabilityOwnershipTest(unittest.TestCase):
    def test_allows_implementation_agent_edit_execute_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "implementation-agent.agent.md").write_text(
                agent_text(
                    "implementation-agent",
                    ["read", "search", "edit", "execute"],
                ),
                encoding="utf-8",
            )

            errors = validate_agents.validate(root)

        self.assertEqual([], errors)

    def test_repository_browser_capability_ownership(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        agents_directory = repository_root / "agents"

        implementation = validate_agents.parse_frontmatter(
            agents_directory / "implementation-agent.agent.md"
        )
        browser = validate_agents.parse_frontmatter(
            agents_directory / "browser-agent.agent.md"
        )
        orchestrator = validate_agents.parse_frontmatter(
            agents_directory / "orchestrator.agent.md"
        )

        self.assertTrue(BROWSER_TOOLS.issubset(set(implementation["tools"])))
        self.assertIn("edit", implementation["tools"])
        self.assertIn("execute", implementation["tools"])

        self.assertTrue(BROWSER_TOOLS.issubset(set(browser["tools"])))
        self.assertNotIn("edit", browser["tools"])

        self.assertTrue(BROWSER_TOOLS.isdisjoint(set(orchestrator["tools"])))


if __name__ == "__main__":
    unittest.main()

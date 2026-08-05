from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "agents"
COMMON_RESULT_FIELDS = {"Status", "Outcome", "Summary", "Scope", "Validation", "Next"}


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise AssertionError(f"missing section: {heading}")
    return match.group("body")


def declared_result_fields(path: Path) -> set[str]:
    body = section(path.read_text(encoding="utf-8"), "Kết quả bắt buộc")
    return set(re.findall(r"^- `([^`]+)`\s*:", body, re.MULTILINE))


class AgentResultContractTest(unittest.TestCase):
    def test_docs_agent_author_contract_has_common_core_and_explicit_docs_fields(self) -> None:
        fields = declared_result_fields(AGENTS / "docs-agent.agent.md")

        self.assertTrue(COMMON_RESULT_FIELDS <= fields)
        self.assertTrue({"Mode", "Docs checked", "Docs changed", "Docs unchanged"} <= fields)
        self.assertNotIn("Docs impact candidates", fields)

    def test_orchestrator_handoff_uses_target_worker_result_contract(self) -> None:
        text = (AGENTS / "orchestrator.agent.md").read_text(encoding="utf-8")
        handoff = section(text, "Handoff contract")

        self.assertIn("Kết quả bắt buộc", handoff)
        self.assertIn("chỉ gửi field mà worker đích khai báo", handoff)
        self.assertIn("docs-agent` mode `author", handoff)
        self.assertIn("không gửi `Docs impact candidates`", handoff)


if __name__ == "__main__":
    unittest.main()

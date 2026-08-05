from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "agents"
COMMON_ENVELOPE_FIELDS = {
    "Status",
    "Outcome",
    "Summary",
    "Scope",
    "Validation",
    "Next",
}


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise AssertionError(f"missing section: {heading}")
    return match.group("body")


def declared_fields(text: str, heading: str) -> set[str]:
    body = section(text, heading)
    return set(re.findall(r"^- `([^`]+)`\s*:", body, re.MULTILINE))


def declared_result_fields(path: Path) -> set[str]:
    return declared_fields(path.read_text(encoding="utf-8"), "Kết quả bắt buộc")


def worker_paths() -> list[Path]:
    return sorted(
        path for path in AGENTS.glob("*.agent.md") if path.name != "orchestrator.agent.md"
    )


class AgentResultContractTest(unittest.TestCase):
    def test_all_workers_declare_common_result_envelope(self) -> None:
        for path in worker_paths():
            with self.subTest(agent=path.name):
                fields = declared_result_fields(path)
                missing = COMMON_ENVELOPE_FIELDS - fields
                self.assertFalse(missing, f"{path.name} missing common fields: {sorted(missing)}")

    def test_docs_agent_author_contract_has_explicit_docs_fields(self) -> None:
        fields = declared_result_fields(AGENTS / "docs-agent.agent.md")

        self.assertTrue({"Mode", "Docs checked", "Docs changed", "Docs unchanged"} <= fields)
        self.assertNotIn("Docs impact candidates", fields)

    def test_orchestrator_declares_same_common_envelope(self) -> None:
        text = (AGENTS / "orchestrator.agent.md").read_text(encoding="utf-8")
        fields = declared_fields(text, "Worker result contract")

        self.assertEqual(COMMON_ENVELOPE_FIELDS, fields)
        self.assertIn(
            "field domain-specific chỉ xuất hiện khi worker-specific",
            section(text, "Worker result contract"),
        )

    def test_orchestrator_handoff_uses_target_worker_result_contract(self) -> None:
        text = (AGENTS / "orchestrator.agent.md").read_text(encoding="utf-8")
        handoff = section(text, "Handoff contract")

        self.assertIn("Kết quả bắt buộc", handoff)
        self.assertIn("chỉ gửi field mà worker đích khai báo", handoff)
        self.assertIn("docs-agent` mode `author", handoff)
        self.assertIn("không gửi `Docs impact candidates`", handoff)


if __name__ == "__main__":
    unittest.main()

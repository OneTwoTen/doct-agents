from __future__ import annotations

import unittest
from pathlib import Path


class AdaptiveFastFixContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository_root = Path(__file__).resolve().parents[1]
        cls.agents_directory = cls.repository_root / "agents"
        cls.orchestrator_text = (
            cls.agents_directory / "orchestrator.agent.md"
        ).read_text(encoding="utf-8")
        cls.implementation_text = (
            cls.agents_directory / "implementation-agent.agent.md"
        ).read_text(encoding="utf-8")

    def test_fast_fix_defines_direct_and_guarded_paths(self) -> None:
        self.assertIn("FAST_FIX direct", self.orchestrator_text)
        self.assertIn("FAST_FIX guarded", self.orchestrator_text)
        self.assertIn(
            "DISCOVER -> IMPLEMENT -> VALIDATE -> FINALIZE",
            self.orchestrator_text,
        )
        self.assertIn(
            "DISCOVER -> IMPLEMENT -> optional TEST/REVIEW/DOMAIN -> VALIDATE -> FINALIZE",
            self.orchestrator_text,
        )

    def test_fast_fix_optional_workers_are_not_defaults(self) -> None:
        self.assertIn(
            "FAST_FIX không gọi `planning-agent`",
            self.orchestrator_text,
        )
        self.assertIn(
            "mặc định không gọi `review-agent`",
            self.orchestrator_text,
        )
        self.assertIn(
            "chỉ gọi `test-agent` khi cần thêm hoặc sửa test",
            self.orchestrator_text,
        )
        self.assertIn(
            "chỉ gọi `docs-agent` khi docs impact là `required`",
            self.orchestrator_text,
        )

    def test_fast_fix_preserves_specialized_routes(self) -> None:
        self.assertIn(
            "`browser-agent` dành cho `BROWSER_VALIDATION`",
            self.orchestrator_text,
        )
        self.assertIn("Refactor giữ behavior: `refactor-agent`", self.orchestrator_text)
        self.assertIn("Test-only: `test-agent`", self.orchestrator_text)

    def test_fast_fix_can_escalate_to_long_running(self) -> None:
        self.assertIn("chuyển sang `LONG_RUNNING`", self.orchestrator_text)
        self.assertIn("migration/rollback", self.orchestrator_text)
        self.assertIn("compatibility", self.orchestrator_text)
        self.assertIn("architecture", self.orchestrator_text.lower())

    def test_fast_fix_has_smaller_default_worker_budget(self) -> None:
        self.assertIn("FAST_FIX direct: tối đa 2 worker", self.orchestrator_text)
        self.assertIn("FAST_FIX guarded: tối đa 3 worker", self.orchestrator_text)
        self.assertIn("mặc định 1 worker tại một thời điểm", self.orchestrator_text)

    def test_fast_fix_validation_plan_is_conditional(self) -> None:
        self.assertIn(
            "FAST_FIX cần `Objective`, `Scope`, `Expected behavior`",
            self.implementation_text,
        )
        self.assertIn(
            "`Validation plan` chỉ bắt buộc khi validation không hiển nhiên",
            self.implementation_text,
        )
        self.assertIn(
            "LONG_RUNNING vẫn bắt buộc `Validation plan`",
            self.implementation_text,
        )


if __name__ == "__main__":
    unittest.main()

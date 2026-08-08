from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Optional

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_skills.py"
SPEC = importlib.util.spec_from_file_location("validate_skills", MODULE_PATH)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class ValidateSkillsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.skills = self.root / "skills"
        self.skills.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_catalog(self, entries: list[dict[str, str]]) -> None:
        (self.skills / "catalog.json").write_text(
            json.dumps({"schema": 1, "skills": entries}, indent=2) + "\n",
            encoding="utf-8",
        )

    def write_skill(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        user_invocable: bool = False,
        disable_model_invocation: bool = False,
        body: str = "# Workflow\n\nFollow the evidence.\n",
    ) -> Path:
        skill_dir = self.skills / name
        skill_dir.mkdir(parents=True)
        description = description or (
            f"Dùng khi thực hiện {name}. Không dùng khi task không thuộc phạm vi này."
        )
        fields = [
            "---",
            f"name: {name}",
            f'description: "{description}"',
            f"user-invocable: {'true' if user_invocable else 'false'}",
        ]
        if disable_model_invocation:
            fields.append("disable-model-invocation: true")
        fields.extend(["---", "", body])
        (skill_dir / "SKILL.md").write_text("\n".join(fields), encoding="utf-8")
        return skill_dir

    def test_accepts_valid_composed_skills(self) -> None:
        self.write_catalog(
            [
                {
                    "name": "code-review",
                    "type": "workflow",
                    "activation": "auto-and-user",
                    "compositionGroup": "primary-workflow",
                },
                {
                    "name": "java",
                    "type": "language",
                    "activation": "auto",
                    "compositionGroup": "language",
                },
            ]
        )
        self.write_skill("code-review", user_invocable=True)
        self.write_skill("java")

        self.assertEqual([], validator.validate(self.skills))

    def test_rejects_directory_and_frontmatter_name_mismatch(self) -> None:
        self.write_catalog(
            [
                {
                    "name": "code-review",
                    "type": "workflow",
                    "activation": "auto",
                    "compositionGroup": "primary-workflow",
                }
            ]
        )
        skill_dir = self.write_skill("code-review")
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        (skill_dir / "SKILL.md").write_text(
            text.replace("name: code-review", "name: code_review"), encoding="utf-8"
        )

        errors = validator.validate(self.skills)
        self.assertTrue(any("must match directory" in error for error in errors))
        self.assertTrue(any("lowercase kebab-case" in error for error in errors))

    def test_rejects_activation_mismatch(self) -> None:
        self.write_catalog(
            [
                {
                    "name": "repository-discovery",
                    "type": "workflow",
                    "activation": "auto",
                    "compositionGroup": "supporting-workflow",
                }
            ]
        )
        self.write_skill("repository-discovery", user_invocable=True)

        errors = validator.validate(self.skills)
        self.assertTrue(any("auto skills must set user-invocable: false" in error for error in errors))

    def test_rejects_escaping_and_broken_links(self) -> None:
        self.write_catalog(
            [
                {
                    "name": "java",
                    "type": "language",
                    "activation": "auto",
                    "compositionGroup": "language",
                }
            ]
        )
        self.write_skill(
            "java",
            body="# Java\n\nRead [outside](../secret.md) and [missing](references/missing.md).\n",
        )

        errors = validator.validate(self.skills)
        self.assertTrue(any("link escapes" in error for error in errors))
        self.assertTrue(any("broken relative link" in error for error in errors))

    def test_rejects_uncatalogued_directory_and_duplicate_catalog_name(self) -> None:
        entry = {
            "name": "code-review",
            "type": "workflow",
            "activation": "auto",
            "compositionGroup": "primary-workflow",
        }
        self.write_catalog([entry, entry])
        self.write_skill("code-review")
        self.write_skill("extra-skill")

        errors = validator.validate(self.skills)
        self.assertTrue(any("duplicate skill name" in error for error in errors))
        self.assertTrue(any("missing from catalog.json" in error for error in errors))

    def test_rejects_description_without_activation_boundaries(self) -> None:
        self.write_catalog(
            [
                {
                    "name": "code-review",
                    "type": "workflow",
                    "activation": "auto",
                    "compositionGroup": "primary-workflow",
                }
            ]
        )
        self.write_skill("code-review", description="Review code changes carefully.")

        errors = validator.validate(self.skills)
        self.assertTrue(any("positive use condition" in error for error in errors))
        self.assertTrue(any("negative activation boundary" in error for error in errors))

    def test_rejects_body_budgets(self) -> None:
        self.write_catalog(
            [
                {
                    "name": "code-review",
                    "type": "workflow",
                    "activation": "auto",
                    "compositionGroup": "primary-workflow",
                }
            ]
        )
        self.write_skill("code-review", body=("x\n" * 501) + ("y" * 8001))

        errors = validator.validate(self.skills)
        self.assertTrue(any("line budget" in error for error in errors))
        self.assertTrue(any("character budget" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

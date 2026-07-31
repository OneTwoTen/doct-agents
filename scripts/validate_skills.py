#!/usr/bin/env python3
"""Validate doct-agents Agent Skills without third-party dependencies."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Optional

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", re.DOTALL)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
ALLOWED_TYPES = {"workflow", "language", "framework", "risk"}
ALLOWED_ACTIVATIONS = {"auto", "manual", "auto-and-user"}
ALLOWED_GROUPS = {
    "primary-workflow",
    "supporting-workflow",
    "language",
    "framework",
    "risk",
}
GROUPS_BY_TYPE = {
    "workflow": {"primary-workflow", "supporting-workflow"},
    "language": {"language"},
    "framework": {"framework"},
    "risk": {"risk"},
}
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_BODY_LINES = 500
MAX_BODY_CHARACTERS = 8_000
REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def is_link_like(path: Path) -> bool:
    try:
        entry = os.lstat(path)
    except FileNotFoundError:
        return False
    attributes = getattr(entry, "st_file_attributes", 0)
    return stat.S_ISLNK(entry.st_mode) or bool(attributes & REPARSE_POINT_ATTRIBUTE)


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith("["):
        parsed = ast.literal_eval(value)
        if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
            raise ValueError("list fields must contain only strings")
        return parsed
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return ast.literal_eval(value)
    return value


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        raise ValueError("missing YAML frontmatter")

    lines = match.group(1).splitlines()
    data: dict[str, Any] = {}
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        line_number = index + 2
        stripped = raw_line.strip()
        index += 1
        if not stripped or stripped.startswith("#"):
            continue
        if raw_line[:1].isspace():
            raise ValueError(f"line {line_number}: unexpected indentation")
        if ":" not in raw_line:
            raise ValueError(f"line {line_number}: expected key: value")
        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            raise ValueError(f"line {line_number}: empty field name")
        if key in data:
            raise ValueError(f"line {line_number}: duplicate field {key}")

        if value in {">", ">-", ">+", "|", "|-", "|+"}:
            block: list[str] = []
            while index < len(lines):
                candidate = lines[index]
                if candidate and not candidate[:1].isspace():
                    break
                index += 1
                block.append(candidate[2:] if candidate.startswith("  ") else candidate.lstrip())
            if value.startswith(">"):
                data[key] = " ".join(part.strip() for part in block if part.strip())
            else:
                data[key] = "\n".join(block).rstrip("\n")
        else:
            data[key] = parse_scalar(value)

    body = text[match.end() :].lstrip("\n")
    return data, body


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def validate_relative_links(skill_dir: Path, body: str) -> list[str]:
    errors: list[str] = []
    root = skill_dir.resolve()
    for raw_target in MARKDOWN_LINK_PATTERN.findall(body):
        target = raw_target.strip().split("#", 1)[0].split("?", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        pure = PurePosixPath(target)
        if pure.is_absolute() or ".." in pure.parts or "\\" in target:
            errors.append(f"{skill_dir / 'SKILL.md'}: link escapes skill directory: {raw_target}")
            continue
        destination = (skill_dir / Path(*pure.parts)).resolve()
        if not _inside(root, destination):
            errors.append(f"{skill_dir / 'SKILL.md'}: link escapes skill directory: {raw_target}")
        elif not destination.exists():
            errors.append(f"{skill_dir / 'SKILL.md'}: broken relative link: {raw_target}")
    return errors


def validate_tree_safety(skills_dir: Path) -> list[str]:
    errors: list[str] = []
    seen: dict[str, Path] = {}
    for root, directory_names, file_names in os.walk(skills_dir, followlinks=False):
        root_path = Path(root)
        for name in sorted(directory_names + file_names):
            path = root_path / name
            relative = path.relative_to(skills_dir).as_posix()
            folded = relative.casefold()
            previous = seen.get(folded)
            if previous is not None and previous != path:
                errors.append(f"{path}: case-insensitive path collision with {previous}")
            else:
                seen[folded] = path
            if is_link_like(path):
                errors.append(f"{path}: symbolic links or junctions are not allowed")
    return errors


def load_catalog(skills_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    path = skills_dir / "catalog.json"
    errors: list[str] = []
    if not path.is_file() or is_link_like(path):
        return [], [f"{path}: missing regular catalog.json"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"{path}: invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return [], [f"{path}: catalog root must be an object"]
    if data.get("schema") != 1:
        errors.append(f"{path}: unsupported schema {data.get('schema')!r}")
    entries = data.get("skills")
    if not isinstance(entries, list):
        return [], errors + [f"{path}: skills must be an array"]

    normalized: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for index, entry in enumerate(entries):
        location = f"{path}: skills[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{location} must be an object")
            continue
        name = entry.get("name")
        skill_type = entry.get("type")
        activation = entry.get("activation")
        group = entry.get("compositionGroup")
        if not isinstance(name, str) or not name:
            errors.append(f"{location}.name must be a non-empty string")
            continue
        folded = name.casefold()
        if folded in seen_names:
            errors.append(f"{location}: duplicate skill name {name!r}")
        seen_names.add(folded)
        if skill_type not in ALLOWED_TYPES:
            errors.append(f"{location}.type must be one of {', '.join(sorted(ALLOWED_TYPES))}")
        if activation not in ALLOWED_ACTIVATIONS:
            errors.append(
                f"{location}.activation must be one of {', '.join(sorted(ALLOWED_ACTIVATIONS))}"
            )
        if group not in ALLOWED_GROUPS:
            errors.append(f"{location}.compositionGroup is unsupported: {group!r}")
        elif skill_type in GROUPS_BY_TYPE and group not in GROUPS_BY_TYPE[skill_type]:
            allowed = ", ".join(sorted(GROUPS_BY_TYPE[skill_type]))
            errors.append(f"{location}: type {skill_type!r} requires compositionGroup {allowed}")
        normalized.append(entry)
    return normalized, errors


def validate_activation(path: Path, frontmatter: dict[str, Any], activation: str) -> list[str]:
    errors: list[str] = []
    user_invocable = frontmatter.get("user-invocable", True)
    disable_model = frontmatter.get("disable-model-invocation", False)
    if not isinstance(user_invocable, bool):
        errors.append(f"{path}: user-invocable must be true or false")
    if not isinstance(disable_model, bool):
        errors.append(f"{path}: disable-model-invocation must be true or false")
    if errors:
        return errors
    if activation == "auto":
        if user_invocable is not False:
            errors.append(f"{path}: auto skills must set user-invocable: false")
        if disable_model is True:
            errors.append(f"{path}: auto skills cannot disable model invocation")
    elif activation == "manual":
        if user_invocable is False:
            errors.append(f"{path}: manual skills must remain user-invocable")
        if disable_model is not True:
            errors.append(f"{path}: manual skills must set disable-model-invocation: true")
    elif activation == "auto-and-user":
        if user_invocable is False:
            errors.append(f"{path}: auto-and-user skills must remain user-invocable")
        if disable_model is True:
            errors.append(f"{path}: auto-and-user skills cannot disable model invocation")
    return errors


def validate_skill(skills_dir: Path, entry: dict[str, Any]) -> tuple[Optional[str], list[str]]:
    name = entry.get("name")
    if not isinstance(name, str):
        return None, []
    skill_dir = skills_dir / name
    path = skill_dir / "SKILL.md"
    errors: list[str] = []

    if not NAME_PATTERN.fullmatch(name) or len(name) > MAX_NAME_LENGTH:
        errors.append(f"{skill_dir}: invalid skill directory name {name!r}")
    if not skill_dir.is_dir() or is_link_like(skill_dir):
        return None, errors + [f"{skill_dir}: missing regular skill directory"]
    if not path.is_file() or is_link_like(path):
        return None, errors + [f"{path}: missing regular SKILL.md"]

    try:
        frontmatter, body = parse_frontmatter(path)
    except (OSError, SyntaxError, ValueError) as exc:
        return None, errors + [f"{path}: {exc}"]

    declared_name = frontmatter.get("name")
    if declared_name != name:
        errors.append(f"{path}: frontmatter name {declared_name!r} must match directory {name!r}")
    if not isinstance(declared_name, str) or not NAME_PATTERN.fullmatch(declared_name or ""):
        errors.append(f"{path}: name must be lowercase kebab-case")

    description = frontmatter.get("description")
    normalized_description: Optional[str] = None
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{path}: description must be a non-empty string")
    else:
        description = " ".join(description.split())
        normalized_description = description.casefold()
        if len(description) > MAX_DESCRIPTION_LENGTH:
            errors.append(
                f"{path}: description exceeds {MAX_DESCRIPTION_LENGTH} characters"
            )
        lowered = description.casefold()
        if not any(
            marker in lowered
            for marker in ("use when", "use before", "dùng khi", "dùng trước khi")
        ):
            errors.append(f"{path}: description must state a positive use condition")
        if not any(marker in lowered for marker in ("do not use", "không dùng")):
            errors.append(f"{path}: description must state a negative activation boundary")

    activation = entry.get("activation")
    if isinstance(activation, str):
        errors.extend(validate_activation(path, frontmatter, activation))

    line_count = len(body.splitlines())
    if line_count > MAX_BODY_LINES:
        errors.append(f"{path}: body exceeds line budget ({line_count} > {MAX_BODY_LINES})")
    if len(body) > MAX_BODY_CHARACTERS:
        errors.append(
            f"{path}: body exceeds character budget ({len(body)} > {MAX_BODY_CHARACTERS})"
        )

    errors.extend(validate_relative_links(skill_dir, body))
    return normalized_description, errors


def validate(skills_dir: Path) -> list[str]:
    skills_dir = skills_dir.resolve()
    if not skills_dir.is_dir() or is_link_like(skills_dir):
        return [f"{skills_dir}: missing regular skills directory"]

    entries, errors = load_catalog(skills_dir)
    errors.extend(validate_tree_safety(skills_dir))

    catalog_names = {
        entry["name"]
        for entry in entries
        if isinstance(entry.get("name"), str) and entry.get("name")
    }
    directory_names = {
        path.name
        for path in skills_dir.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    }
    for name in sorted(catalog_names - directory_names):
        errors.append(f"{skills_dir / name}: cataloged skill directory is missing")
    for name in sorted(directory_names - catalog_names):
        errors.append(f"{skills_dir / name}: skill directory is missing from catalog.json")

    descriptions: dict[str, str] = {}
    for entry in entries:
        description, skill_errors = validate_skill(skills_dir, entry)
        errors.extend(skill_errors)
        if description:
            name = str(entry.get("name"))
            previous = descriptions.get(description)
            if previous is not None:
                errors.append(
                    f"{skills_dir / name / 'SKILL.md'}: duplicate normalized description with {previous}"
                )
            else:
                descriptions[description] = str(skills_dir / name / "SKILL.md")

    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default="skills", type=Path)
    args = parser.parse_args()
    errors = validate(args.directory)
    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    count = len([path for path in args.directory.iterdir() if path.is_dir()])
    print(f"Validated {count} Agent Skills successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

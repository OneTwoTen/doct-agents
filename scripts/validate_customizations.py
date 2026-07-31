#!/usr/bin/env python3
"""Validate all doct-agents customizations and package declarations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_agents import validate as validate_agents
from validate_skills import validate as validate_skills


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    errors = validate_agents(root / "agents")
    errors.extend(validate_skills(root / "skills"))

    package_path = root / "package.json"
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{package_path}: cannot read package metadata: {exc}")
    else:
        files = package.get("files")
        if not isinstance(files, list) or "skills" not in files:
            errors.append(f"{package_path}: package files must include 'skills'")
    return sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", type=Path)
    args = parser.parse_args()
    errors = validate_repository(args.root)
    if errors:
        print("Customization validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Validated agents, skills, and package declarations successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

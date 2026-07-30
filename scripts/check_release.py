#!/usr/bin/env python3
"""Validate npm release metadata without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

SEMVER_PATTERN = re.compile(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?\Z")


def read_package_version(package_path: Path) -> str:
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {package_path}: {exc}") from exc
    if not isinstance(package, dict):
        raise ValueError(f"{package_path} must contain a JSON object")
    version = package.get("version")
    if not isinstance(version, str) or not SEMVER_PATTERN.fullmatch(version):
        raise ValueError(f"{package_path} has an invalid version: {version!r}")
    return version


def validate_release_tag(tag: Optional[str], version: str) -> None:
    if not tag:
        return
    expected = f"v{version}"
    if tag != expected:
        raise ValueError(
            f"release tag {tag!r} does not match package version {version!r}; "
            f"expected {expected}"
        )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tag", nargs="?")
    parser.add_argument(
        "--package",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "package.json",
    )
    args = parser.parse_args(argv)

    try:
        version = read_package_version(args.package)
        tag = args.tag or os.environ.get("RELEASE_TAG")
        validate_release_tag(tag, version)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if tag:
        print(f"Release tag {tag} matches package version {version}.")
    else:
        print(f"Package version {version} is valid; no release tag was supplied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

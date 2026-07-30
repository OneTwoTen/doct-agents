#!/usr/bin/env python3
"""Install, update, inspect, or remove doct-agents without extra dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import NamedTuple

REPOSITORY = "OneTwoTen/doct-agents"
DEFAULT_REF = "main"
MANIFEST_NAME = ".doct-agents-manifest.json"


class InstallConflict(RuntimeError):
    """Raised when installation would overwrite an unmanaged or modified file."""


class InstallResult(NamedTuple):
    installed: int
    target: Path


class UninstallResult(NamedTuple):
    removed: int
    preserved: list[str]
    target: Path


class InstallStatus(NamedTuple):
    installed: list[str]
    modified: list[str]
    missing: list[str]
    target: Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(target_dir: Path) -> dict[str, object]:
    manifest_path = target_dir / MANIFEST_NAME
    if not manifest_path.exists():
        return {"schema": 1, "repository": REPOSITORY, "files": {}}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallConflict(f"Cannot read installer manifest: {manifest_path}: {exc}") from exc
    if not isinstance(data.get("files"), dict):
        raise InstallConflict(f"Invalid installer manifest: {manifest_path}")
    return data


def find_agent_files(source_dir: Path) -> list[Path]:
    files = sorted(source_dir.glob("*.agent.md"), key=lambda path: path.name)
    if not files:
        raise FileNotFoundError(f"No *.agent.md files found in {source_dir}")
    return files


def install_agents(source_dir: Path, target_dir: Path, *, force: bool = False) -> InstallResult:
    source_dir = source_dir.resolve()
    target_dir = target_dir.expanduser().resolve()
    sources = find_agent_files(source_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(target_dir)
    previous_files = manifest.get("files", {})
    assert isinstance(previous_files, dict)

    conflicts: list[str] = []
    for source in sources:
        target = target_dir / source.name
        if not target.exists():
            continue
        previous_hash = previous_files.get(source.name)
        current_hash = sha256(target)
        if previous_hash is None:
            conflicts.append(f"{source.name} already exists and is not managed by doct-agents")
        elif current_hash != previous_hash:
            conflicts.append(f"{source.name} was modified after installation")

    if conflicts and not force:
        details = "\n- ".join(conflicts)
        raise InstallConflict(
            f"Installation stopped to protect existing files:\n- {details}\n"
            "Re-run with --force only when replacing those files is intentional."
        )

    installed_files: dict[str, str] = {}
    for source in sources:
        target = target_dir / source.name
        shutil.copyfile(source, target)
        installed_files[source.name] = sha256(target)

    manifest_data = {
        "schema": 1,
        "repository": REPOSITORY,
        "files": installed_files,
    }
    (target_dir / MANIFEST_NAME).write_text(
        json.dumps(manifest_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return InstallResult(installed=len(installed_files), target=target_dir)


def get_status(target_dir: Path) -> InstallStatus:
    target_dir = target_dir.expanduser().resolve()
    manifest = load_manifest(target_dir)
    files = manifest.get("files", {})
    assert isinstance(files, dict)

    installed: list[str] = []
    modified: list[str] = []
    missing: list[str] = []
    for filename, expected_hash in sorted(files.items()):
        target = target_dir / filename
        if not target.exists():
            missing.append(filename)
        elif sha256(target) != expected_hash:
            modified.append(filename)
        else:
            installed.append(filename)
    return InstallStatus(installed, modified, missing, target_dir)


def uninstall_agents(target_dir: Path, *, force: bool = False) -> UninstallResult:
    target_dir = target_dir.expanduser().resolve()
    manifest = load_manifest(target_dir)
    files = manifest.get("files", {})
    assert isinstance(files, dict)

    removed = 0
    preserved: list[str] = []
    remaining: dict[str, str] = {}
    for filename, expected_hash in sorted(files.items()):
        target = target_dir / filename
        if not target.exists():
            continue
        if not force and sha256(target) != expected_hash:
            preserved.append(filename)
            remaining[filename] = str(expected_hash)
            continue
        target.unlink()
        removed += 1

    manifest_path = target_dir / MANIFEST_NAME
    if remaining:
        manifest["files"] = remaining
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    elif manifest_path.exists():
        manifest_path.unlink()

    return UninstallResult(removed, preserved, target_dir)


def default_target(scope: str, workspace: Path) -> Path:
    if scope == "user":
        return Path.home() / ".copilot" / "agents"
    return workspace.resolve() / ".github" / "agents"


def download_source(repository: str, ref: str, work_dir: Path) -> Path:
    archive_url = f"https://github.com/{repository}/archive/refs/heads/{ref}.zip"
    archive_path = work_dir / "doct-agents.zip"
    request = urllib.request.Request(
        archive_url,
        headers={"User-Agent": "doct-agents-installer"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            archive_path.write_bytes(response.read())
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Cannot download {archive_url}: {exc}") from exc

    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(work_dir / "source")
    candidates = list((work_dir / "source").glob("*/agents"))
    if len(candidates) != 1:
        raise RuntimeError("Downloaded archive does not contain one agents directory")
    return candidates[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage doct-agents in VS Code's standard agent locations."
    )
    parser.add_argument(
        "command",
        choices=("install", "update", "status", "uninstall"),
        nargs="?",
        default="install",
    )
    parser.add_argument("--scope", choices=("user", "workspace"), default="user")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--target", type=Path)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--repository", default=REPOSITORY)
    parser.add_argument("--ref", default=DEFAULT_REF)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target = args.target or default_target(args.scope, args.workspace)

    try:
        if args.command == "status":
            status = get_status(target)
            if not (status.installed or status.modified or status.missing):
                print(f"doct-agents is not installed in {status.target}")
                return 1
            print(f"Target: {status.target}")
            print(f"Installed: {len(status.installed)}")
            print(f"Modified: {', '.join(status.modified) if status.modified else 'none'}")
            print(f"Missing: {', '.join(status.missing) if status.missing else 'none'}")
            return 2 if status.modified or status.missing else 0

        if args.command == "uninstall":
            result = uninstall_agents(target, force=args.force)
            print(f"Removed {result.removed} managed agent files from {result.target}")
            if result.preserved:
                print("Preserved modified files: " + ", ".join(result.preserved))
                return 2
            return 0

        if args.source_dir:
            result = install_agents(args.source_dir, target, force=args.force)
        else:
            with tempfile.TemporaryDirectory(prefix="doct-agents-") as temp_dir:
                source_dir = download_source(args.repository, args.ref, Path(temp_dir))
                result = install_agents(source_dir, target, force=args.force)
        verb = "Updated" if args.command == "update" else "Installed"
        print(f"{verb} {result.installed} agents in {result.target}")
        print("Reload VS Code, open Copilot Chat, and select orchestrator or cli-executor.")
        return 0
    except (FileNotFoundError, InstallConflict, RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

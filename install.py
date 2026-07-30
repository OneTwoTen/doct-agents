#!/usr/bin/env python3
"""Install, update, inspect, or remove doct-agents without extra dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import NamedTuple, Optional

REPOSITORY = "OneTwoTen/doct-agents"
PACKAGE_NAME = "doct-agents"
DEFAULT_REF = "main"
MANIFEST_NAME = ".doct-agents-manifest.json"
SHA256_PATTERN = re.compile(r"[a-fA-F0-9]{64}\Z")


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


def canonical_manifest(files: dict[str, str]) -> dict[str, object]:
    return {
        "schema": 1,
        "package": PACKAGE_NAME,
        "repository": REPOSITORY,
        "files": files,
    }


def normalize_target(target_dir: Path) -> Path:
    return Path(os.path.abspath(str(target_dir.expanduser())))


def validate_managed_filename(filename: str) -> str:
    if (
        not isinstance(filename, str)
        or not filename
        or filename in {".", ".."}
        or Path(filename).is_absolute()
        or Path(filename).name != filename
        or any(character in filename for character in ("\0", "/", "\\", ":"))
        or not filename.endswith(".agent.md")
    ):
        raise InstallConflict(f"Unsafe managed agent filename: {filename!r}")
    return filename


def managed_path(target_dir: Path, filename: str) -> Path:
    validate_managed_filename(filename)
    destination = target_dir / filename
    if destination.parent != target_dir:
        raise InstallConflict(f"Managed path escapes target directory: {filename}")
    return destination


def assert_regular_managed_file(path: Path, filename: str) -> bool:
    if path.is_symlink():
        raise InstallConflict(f"Managed agent {filename} is a symbolic link")
    if not path.exists():
        return False
    if not path.is_file():
        raise InstallConflict(f"Managed agent {filename} is not a regular file")
    return True


def prepare_target(target_dir: Path) -> Path:
    target = normalize_target(target_dir)
    if target.is_symlink():
        raise InstallConflict(f"Target must not be a symbolic link: {target}")
    target.mkdir(parents=True, exist_ok=True)
    if not target.is_dir():
        raise InstallConflict(f"Target must be a directory: {target}")
    return target


def validate_existing_target(target_dir: Path) -> Path:
    target = normalize_target(target_dir)
    if target.is_symlink():
        raise InstallConflict(f"Target must not be a symbolic link: {target}")
    if target.exists() and not target.is_dir():
        raise InstallConflict(f"Target must be a directory: {target}")
    return target


def manifest_path(target_dir: Path) -> Path:
    return target_dir / MANIFEST_NAME


def write_manifest(target_dir: Path, files: dict[str, str]) -> None:
    path = manifest_path(target_dir)
    if path.is_symlink():
        raise InstallConflict(f"Installer manifest is a symbolic link: {path}")
    if path.exists() and not path.is_file():
        raise InstallConflict(f"Installer manifest is not a regular file: {path}")
    path.write_text(
        json.dumps(canonical_manifest(files), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(target_dir: Path) -> dict[str, object]:
    target_dir = validate_existing_target(target_dir)
    path = manifest_path(target_dir)
    if path.is_symlink():
        raise InstallConflict(f"Installer manifest is a symbolic link: {path}")
    if not path.exists():
        return canonical_manifest({})
    if not path.is_file():
        raise InstallConflict(f"Installer manifest is not a regular file: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallConflict(f"Cannot read installer manifest: {path}: {exc}") from exc

    try:
        if not isinstance(data, dict):
            raise ValueError("manifest root must be an object")
        if data.get("schema") != 1:
            raise ValueError(f"unsupported schema {data.get('schema')!r}")

        package_matches = data.get("package") == PACKAGE_NAME
        repository_matches = data.get("repository") == REPOSITORY
        if not package_matches and not repository_matches:
            raise ValueError("manifest identity does not match doct-agents")
        if "package" in data and not package_matches:
            raise ValueError(f"unexpected package {data.get('package')!r}")
        if "repository" in data and not repository_matches:
            raise ValueError(f"unexpected repository {data.get('repository')!r}")

        raw_files = data.get("files")
        if not isinstance(raw_files, dict):
            raise ValueError("files must be an object")

        files: dict[str, str] = {}
        for filename, expected_hash in raw_files.items():
            validate_managed_filename(filename)
            if not isinstance(expected_hash, str) or not SHA256_PATTERN.fullmatch(
                expected_hash
            ):
                raise ValueError(f"invalid SHA-256 for {filename}")
            files[filename] = expected_hash.lower()
        return canonical_manifest(files)
    except (InstallConflict, ValueError) as exc:
        raise InstallConflict(f"Invalid installer manifest: {path}: {exc}") from exc


def find_agent_files(source_dir: Path) -> list[Path]:
    files = sorted(source_dir.glob("*.agent.md"), key=lambda path: path.name)
    if not files:
        raise FileNotFoundError(f"No *.agent.md files found in {source_dir}")
    for source in files:
        validate_managed_filename(source.name)
        if source.is_symlink() or not source.is_file():
            raise InstallConflict(f"Bundled agent {source.name} must be a regular file")
    return files


def install_agents(source_dir: Path, target_dir: Path, *, force: bool = False) -> InstallResult:
    source_dir = source_dir.resolve()
    target_dir = prepare_target(target_dir)
    sources = find_agent_files(source_dir)
    current_names = {source.name for source in sources}

    manifest = load_manifest(target_dir)
    previous_files = manifest["files"]
    assert isinstance(previous_files, dict)

    conflicts: list[str] = []
    obsolete_to_remove: list[Path] = []
    preserved_obsolete: dict[str, str] = {}

    for source in sources:
        target = managed_path(target_dir, source.name)
        if not assert_regular_managed_file(target, source.name):
            continue
        previous_hash = previous_files.get(source.name)
        current_hash = sha256(target)
        if previous_hash is None:
            conflicts.append(f"{source.name} already exists and is not managed by doct-agents")
        elif current_hash != previous_hash:
            conflicts.append(f"{source.name} was modified after installation")

    for filename, expected_hash in sorted(previous_files.items()):
        if filename in current_names:
            continue
        target = managed_path(target_dir, filename)
        if not assert_regular_managed_file(target, filename):
            continue
        if sha256(target) == expected_hash:
            obsolete_to_remove.append(target)
        else:
            preserved_obsolete[filename] = str(expected_hash)

    if conflicts and not force:
        details = "\n- ".join(conflicts)
        raise InstallConflict(
            f"Installation stopped to protect existing files:\n- {details}\n"
            "Re-run with --force only when replacing those files is intentional."
        )

    for obsolete in obsolete_to_remove:
        obsolete.unlink()

    installed_files: dict[str, str] = dict(preserved_obsolete)
    for source in sources:
        target = managed_path(target_dir, source.name)
        shutil.copyfile(source, target)
        installed_files[source.name] = sha256(target)

    write_manifest(target_dir, installed_files)
    return InstallResult(installed=len(sources), target=target_dir)


def get_status(target_dir: Path) -> InstallStatus:
    target_dir = validate_existing_target(target_dir)
    manifest = load_manifest(target_dir)
    files = manifest["files"]
    assert isinstance(files, dict)

    installed: list[str] = []
    modified: list[str] = []
    missing: list[str] = []
    for filename, expected_hash in sorted(files.items()):
        target = managed_path(target_dir, filename)
        if not assert_regular_managed_file(target, filename):
            missing.append(filename)
        elif sha256(target) != expected_hash:
            modified.append(filename)
        else:
            installed.append(filename)
    return InstallStatus(installed, modified, missing, target_dir)


def uninstall_agents(target_dir: Path, *, force: bool = False) -> UninstallResult:
    target_dir = validate_existing_target(target_dir)
    manifest = load_manifest(target_dir)
    files = manifest["files"]
    assert isinstance(files, dict)

    preserved: list[str] = []
    remaining: dict[str, str] = {}
    remove_paths: list[Path] = []
    for filename, expected_hash in sorted(files.items()):
        target = managed_path(target_dir, filename)
        if not assert_regular_managed_file(target, filename):
            continue
        if not force and sha256(target) != expected_hash:
            preserved.append(filename)
            remaining[filename] = str(expected_hash)
        else:
            remove_paths.append(target)

    for target in remove_paths:
        target.unlink()

    path = manifest_path(target_dir)
    if remaining:
        write_manifest(target_dir, remaining)
    elif path.is_symlink():
        raise InstallConflict(f"Installer manifest is a symbolic link: {path}")
    elif path.exists():
        path.unlink()

    return UninstallResult(len(remove_paths), preserved, target_dir)


def default_target(scope: str, workspace: Path) -> Path:
    if scope == "user":
        return Path.home() / ".copilot" / "agents"
    return workspace.resolve() / ".github" / "agents"


def safe_extract_archive(archive: zipfile.ZipFile, destination: Path) -> None:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or not destination.is_dir():
        raise RuntimeError(f"Archive destination must be a real directory: {destination}")

    for member in archive.infolist():
        name = member.filename
        pure_path = PurePosixPath(name)
        if (
            not name
            or "\0" in name
            or "\\" in name
            or pure_path.is_absolute()
            or ".." in pure_path.parts
            or any(":" in part for part in pure_path.parts)
        ):
            raise RuntimeError(f"unsafe archive member: {name!r}")

        mode = (member.external_attr >> 16) & 0o170000
        if mode == stat.S_IFLNK:
            raise RuntimeError(f"archive member is a symbolic link: {name!r}")

        target = (destination / Path(*pure_path.parts)).resolve()
        try:
            target.relative_to(destination)
        except ValueError as exc:
            raise RuntimeError(f"unsafe archive member: {name!r}") from exc

        current = target.parent
        while current != destination:
            if current.is_symlink():
                raise RuntimeError(f"archive member crosses a symbolic link: {name!r}")
            current = current.parent

    archive.extractall(destination)


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
        safe_extract_archive(archive, work_dir / "source")
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


def main(argv: Optional[list[str]] = None) -> int:
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

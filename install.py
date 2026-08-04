#!/usr/bin/env python3
"""Install, update, inspect, or remove doct-agents without extra dependencies."""

from __future__ import annotations

import argparse
import ast
import copy
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
REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
PLAYWRIGHT_MCP = {
    "type": "local",
    "command": ["npx", "-y", "@playwright/mcp@0.0.78", "--isolated"],
    "enabled": True,
}
SOURCE_TOOL_PERMISSIONS = {
    "read": ("read",),
    "search": ("glob", "grep"),
    "edit": ("edit",),
    "execute": ("bash",),
    "agent": ("task",),
    "todo": ("todowrite",),
    "vscode/askQuestions": ("question",),
    "web": ("webfetch", "websearch"),
}
SIMPLE_PERMISSIONS = (
    "read",
    "glob",
    "grep",
    "edit",
    "bash",
    "todowrite",
    "webfetch",
    "websearch",
    "question",
)


class InstallConflict(RuntimeError):
    """Raised when installation would overwrite unmanaged or modified content."""


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


class OpenCodeConfigPatch(NamedTuple):
    text: str
    mcp_entry_sha256: str
    changed: bool


class OpenCodeStatus(NamedTuple):
    installed: list[str]
    modified: list[str]
    missing: list[str]
    target: Path
    config: str
    config_path: Path


class OpenCodeUninstallResult(NamedTuple):
    removed: int
    preserved: list[str]
    target: Path
    config_preserved: bool
    config_path: Optional[Path]


def validate_platform(platform: str) -> str:
    if platform not in {"copilot", "opencode"}:
        raise InstallConflict(f"Unsupported platform: {platform!r}")
    return platform


def normalize_target(target_dir: Path) -> Path:
    return Path(os.path.abspath(str(target_dir.expanduser())))


def is_link_like(stat_result: os.stat_result) -> bool:
    attributes = getattr(stat_result, "st_file_attributes", 0)
    return stat.S_ISLNK(stat_result.st_mode) or bool(
        attributes & REPARSE_POINT_ATTRIBUTE
    )


def lstat_or_none(path: Path) -> Optional[os.stat_result]:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None


def validate_path_components(target_dir: Path) -> Path:
    target = normalize_target(target_dir)
    parts = target.parts
    if not parts:
        raise InstallConflict(f"Invalid target path: {target}")
    current = Path(parts[0])
    for part in parts[1:]:
        current = current / part
        entry = lstat_or_none(current)
        if entry is None:
            break
        if is_link_like(entry):
            raise InstallConflict(
                f"Target path component is a symbolic link or junction: {current}"
            )
        if current != target and not stat.S_ISDIR(entry.st_mode):
            raise InstallConflict(f"Target path component is not a directory: {current}")
    return target


def validate_existing_target(target_dir: Path) -> Path:
    target = validate_path_components(target_dir)
    entry = lstat_or_none(target)
    if entry is not None and not stat.S_ISDIR(entry.st_mode):
        raise InstallConflict(f"Target must be a directory: {target}")
    return target


def prepare_target(target_dir: Path) -> Path:
    target = validate_existing_target(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    validate_path_components(target)
    entry = lstat_or_none(target)
    if entry is None or is_link_like(entry) or not stat.S_ISDIR(entry.st_mode):
        raise InstallConflict(f"Target must be a real directory: {target}")
    return target


def assert_regular_path(path: Path, label: str) -> bool:
    entry = lstat_or_none(path)
    if entry is None:
        return False
    if is_link_like(entry):
        raise InstallConflict(f"{label} is a symbolic link or junction")
    if not stat.S_ISREG(entry.st_mode):
        raise InstallConflict(f"{label} is not a regular file")
    return True


def assert_regular_managed_file(path: Path, filename: str) -> bool:
    return assert_regular_path(path, f"Managed agent {filename}")


def validate_config_metadata(config: object) -> Optional[dict[str, str]]:
    if config is None:
        return None
    if not isinstance(config, dict):
        raise InstallConflict("OpenCode manifest config must be an object")
    filename = config.get("filename")
    mcp_hash = config.get("mcpEntrySha256")
    if (
        filename not in {"opencode.json", "opencode.jsonc"}
        or not isinstance(filename, str)
        or Path(filename).name != filename
    ):
        raise InstallConflict(f"Unsafe OpenCode config filename: {filename!r}")
    if not isinstance(mcp_hash, str) or not SHA256_PATTERN.fullmatch(mcp_hash):
        raise InstallConflict("Invalid OpenCode MCP entry SHA-256")
    return {"filename": filename, "mcpEntrySha256": mcp_hash.lower()}


def canonical_manifest(
    files: dict[str, str],
    platform: str = "copilot",
    metadata: Optional[dict[str, object]] = None,
) -> dict[str, object]:
    validate_platform(platform)
    if platform == "copilot":
        return {
            "schema": 1,
            "package": PACKAGE_NAME,
            "repository": REPOSITORY,
            "files": files,
        }
    manifest: dict[str, object] = {
        "schema": 2,
        "package": PACKAGE_NAME,
        "repository": REPOSITORY,
        "platform": "opencode",
        "files": files,
    }
    config = validate_config_metadata(metadata.get("config") if metadata else None)
    if config is not None:
        manifest["config"] = config
    return manifest


def manifest_text(
    files: dict[str, str],
    platform: str = "copilot",
    metadata: Optional[dict[str, object]] = None,
) -> str:
    return json.dumps(
        canonical_manifest(files, platform, metadata), indent=2, sort_keys=True
    ) + "\n"


def validate_managed_filename(filename: str, platform: str = "copilot") -> str:
    validate_platform(platform)
    extension_matches = False
    if isinstance(filename, str):
        extension_matches = (
            filename.endswith(".agent.md")
            if platform == "copilot"
            else filename.endswith(".md") and not filename.endswith(".agent.md")
        )
    if (
        not isinstance(filename, str)
        or not filename
        or filename in {".", ".."}
        or Path(filename).is_absolute()
        or Path(filename).name != filename
        or any(character in filename for character in ("\0", "/", "\\", ":"))
        or not extension_matches
    ):
        raise InstallConflict(f"Unsafe managed agent filename: {filename!r}")
    return filename


def managed_path(target_dir: Path, filename: str, platform: str = "copilot") -> Path:
    validate_managed_filename(filename, platform)
    destination = target_dir / filename
    if destination.parent != target_dir:
        raise InstallConflict(f"Managed path escapes target directory: {filename}")
    return destination


def manifest_path(target_dir: Path) -> Path:
    return target_dir / MANIFEST_NAME


def write_manifest(
    target_dir: Path,
    files: dict[str, str],
    platform: str = "copilot",
    metadata: Optional[dict[str, object]] = None,
) -> None:
    path = manifest_path(target_dir)
    assert_regular_path(path, f"Installer manifest {path}")
    path.write_text(manifest_text(files, platform, metadata), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_json_value(value: object) -> str:
    return sha256_text(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    )


def load_manifest(target_dir: Path, platform: str = "copilot") -> dict[str, object]:
    validate_platform(platform)
    target_dir = validate_existing_target(target_dir)
    path = manifest_path(target_dir)
    if not assert_regular_path(path, f"Installer manifest {path}"):
        return canonical_manifest({}, platform)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallConflict(f"Cannot read installer manifest: {path}: {exc}") from exc
    try:
        if not isinstance(data, dict):
            raise ValueError("manifest root must be an object")
        package_matches = data.get("package") == PACKAGE_NAME
        repository_matches = data.get("repository") == REPOSITORY
        if not package_matches and not repository_matches:
            raise ValueError("manifest identity does not match doct-agents")
        if "package" in data and not package_matches:
            raise ValueError(f"unexpected package {data.get('package')!r}")
        if "repository" in data and not repository_matches:
            raise ValueError(f"unexpected repository {data.get('repository')!r}")

        metadata: Optional[dict[str, object]] = None
        if data.get("schema") == 1:
            manifest_platform = "copilot"
        elif data.get("schema") == 2:
            manifest_platform = data.get("platform")
            if manifest_platform != "opencode":
                raise ValueError(f"unsupported platform {manifest_platform!r}")
            if "config" in data:
                metadata = {"config": validate_config_metadata(data.get("config"))}
        else:
            raise ValueError(f"unsupported schema {data.get('schema')!r}")
        if manifest_platform != platform:
            raise ValueError(
                f"manifest platform {manifest_platform} does not match requested {platform}"
            )

        raw_files = data.get("files")
        if not isinstance(raw_files, dict):
            raise ValueError("files must be an object")
        files: dict[str, str] = {}
        for filename, expected_hash in raw_files.items():
            validate_managed_filename(filename, platform)
            if not isinstance(expected_hash, str) or not SHA256_PATTERN.fullmatch(
                expected_hash
            ):
                raise ValueError(f"invalid SHA-256 for {filename}")
            files[filename] = expected_hash.lower()
        return canonical_manifest(files, platform, metadata)
    except (InstallConflict, ValueError) as exc:
        raise InstallConflict(f"Invalid installer manifest: {path}: {exc}") from exc


def find_agent_files(source_dir: Path, platform: str = "copilot") -> list[Path]:
    validate_platform(platform)
    pattern = "*.agent.md" if platform == "copilot" else "*.md"
    files = sorted(source_dir.glob(pattern), key=lambda path: path.name)
    if platform == "opencode":
        files = [path for path in files if not path.name.endswith(".agent.md")]
    if not files:
        raise FileNotFoundError(f"No {pattern} files found in {source_dir}")
    for source in files:
        validate_managed_filename(source.name, platform)
        entry = lstat_or_none(source)
        if entry is None or is_link_like(entry) or not stat.S_ISREG(entry.st_mode):
            raise InstallConflict(f"Bundled agent {source.name} must be a regular file")
    return files


def stage_install(
    source_dir: Path,
    target_dir: Path,
    sources: list[Path],
    preserved_obsolete: dict[str, str],
    platform: str = "copilot",
    manifest_metadata: Optional[dict[str, object]] = None,
) -> Path:
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{target_dir.name}.doct-agents-stage-",
            dir=str(target_dir.parent),
        )
    )
    installed_files: dict[str, str] = dict(preserved_obsolete)
    try:
        for source in sources:
            staged = stage / source.name
            shutil.copyfile(source, staged)
            installed_files[source.name] = sha256(staged)
        (stage / MANIFEST_NAME).write_text(
            manifest_text(installed_files, platform, manifest_metadata), encoding="utf-8"
        )
        return stage
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def commit_staged_install(
    target_dir: Path,
    stage: Path,
    sources: list[Path],
    obsolete_to_remove: list[Path],
    platform: str = "copilot",
) -> None:
    backup = Path(
        tempfile.mkdtemp(
            prefix=f".{target_dir.name}.doct-agents-backup-",
            dir=str(target_dir.parent),
        )
    )
    records: list[dict[str, object]] = []
    preserve_backup = False

    def replace_from_stage(
        staged: Path, destination: Path, backup_name: str, label: str
    ) -> None:
        existing = assert_regular_path(destination, label)
        backup_path = backup / backup_name
        record: dict[str, object] = {
            "destination": destination,
            "backup": backup_path,
            "had_original": existing,
            "installed_new": False,
        }
        if existing:
            os.replace(destination, backup_path)
        records.append(record)
        os.replace(staged, destination)
        record["installed_new"] = True

    try:
        validate_path_components(target_dir)
        for source in sources:
            destination = managed_path(target_dir, source.name, platform)
            replace_from_stage(
                stage / source.name,
                destination,
                source.name,
                f"Managed agent {source.name}",
            )
        for destination in obsolete_to_remove:
            filename = destination.name
            assert_regular_managed_file(destination, filename)
            backup_path = backup / filename
            os.replace(destination, backup_path)
            records.append(
                {
                    "destination": destination,
                    "backup": backup_path,
                    "had_original": True,
                    "installed_new": False,
                }
            )
        destination_manifest = manifest_path(target_dir)
        replace_from_stage(
            stage / MANIFEST_NAME,
            destination_manifest,
            MANIFEST_NAME,
            f"Installer manifest {destination_manifest}",
        )
    except BaseException as exc:
        rollback_errors: list[str] = []
        for record in reversed(records):
            destination = record["destination"]
            backup_path = record["backup"]
            assert isinstance(destination, Path)
            assert isinstance(backup_path, Path)
            try:
                if bool(record["installed_new"]) and lstat_or_none(destination):
                    destination.unlink()
                if bool(record["had_original"]) and lstat_or_none(backup_path):
                    os.replace(backup_path, destination)
            except OSError as rollback_error:
                rollback_errors.append(str(rollback_error))
        if rollback_errors:
            preserve_backup = True
            raise InstallConflict(
                f"{exc}; rollback also failed: {'; '.join(rollback_errors)}; "
                f"backup preserved at {backup}"
            ) from exc
        raise
    finally:
        shutil.rmtree(stage, ignore_errors=True)
        if not preserve_backup:
            shutil.rmtree(backup, ignore_errors=True)


def install_agents(
    source_dir: Path,
    target_dir: Path,
    *,
    force: bool = False,
    platform: str = "copilot",
    manifest_metadata: Optional[dict[str, object]] = None,
) -> InstallResult:
    validate_platform(platform)
    source_dir = source_dir.resolve()
    target_dir = prepare_target(target_dir)
    sources = find_agent_files(source_dir, platform)
    current_names = {source.name for source in sources}
    manifest = load_manifest(target_dir, platform)
    previous_files = manifest["files"]
    assert isinstance(previous_files, dict)

    conflicts: list[str] = []
    obsolete_to_remove: list[Path] = []
    preserved_obsolete: dict[str, str] = {}
    for source in sources:
        target = managed_path(target_dir, source.name, platform)
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
        target = managed_path(target_dir, filename, platform)
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

    metadata = None
    if platform == "opencode":
        if manifest_metadata is not None:
            metadata = manifest_metadata
        elif isinstance(manifest.get("config"), dict):
            metadata = {"config": manifest["config"]}
    stage = stage_install(
        source_dir,
        target_dir,
        sources,
        preserved_obsolete,
        platform,
        metadata,
    )
    commit_staged_install(target_dir, stage, sources, obsolete_to_remove, platform)
    return InstallResult(installed=len(sources), target=target_dir)


def get_status(target_dir: Path, platform: str = "copilot") -> InstallStatus:
    target_dir = validate_existing_target(target_dir)
    manifest = load_manifest(target_dir, platform)
    files = manifest["files"]
    assert isinstance(files, dict)
    installed: list[str] = []
    modified: list[str] = []
    missing: list[str] = []
    for filename, expected_hash in sorted(files.items()):
        target = managed_path(target_dir, filename, platform)
        if not assert_regular_managed_file(target, filename):
            missing.append(filename)
        elif sha256(target) != expected_hash:
            modified.append(filename)
        else:
            installed.append(filename)
    return InstallStatus(installed, modified, missing, target_dir)


def uninstall_agents(
    target_dir: Path,
    *,
    force: bool = False,
    platform: str = "copilot",
) -> UninstallResult:
    target_dir = validate_existing_target(target_dir)
    manifest = load_manifest(target_dir, platform)
    files = manifest["files"]
    assert isinstance(files, dict)
    preserved: list[str] = []
    remaining: dict[str, str] = {}
    remove_paths: list[Path] = []
    for filename, expected_hash in sorted(files.items()):
        target = managed_path(target_dir, filename, platform)
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
        metadata = (
            {"config": manifest["config"]}
            if platform == "opencode" and isinstance(manifest.get("config"), dict)
            else None
        )
        write_manifest(target_dir, remaining, platform, metadata)
    elif lstat_or_none(path):
        assert_regular_path(path, f"Installer manifest {path}")
        path.unlink()
    return UninstallResult(len(remove_paths), preserved, target_dir)


def default_target(
    scope: str,
    workspace: Path,
    platform: str = "copilot",
    home: Optional[Path] = None,
) -> Path:
    validate_platform(platform)
    resolved_home = Path.home() if home is None else home
    if platform == "opencode":
        if scope == "user":
            return normalize_target(resolved_home / ".config" / "opencode" / "agents")
        return normalize_target(workspace) / ".opencode" / "agents"
    if scope == "user":
        return normalize_target(resolved_home / ".copilot" / "agents")
    return normalize_target(workspace) / ".github" / "agents"


def parse_source_scalar(value: str):
    value = value.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith("["):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise InstallConflict(f"Invalid source list: {exc}") from exc
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value[1:-1]
    return value


def parse_source_frontmatter(source_text: str) -> tuple[dict[str, object], str]:
    if not source_text.startswith("---\n"):
        raise InstallConflict("Agent source is missing YAML frontmatter")
    closing = source_text.find("\n---", 4)
    if closing < 0:
        raise InstallConflict("Agent source has unterminated YAML frontmatter")
    block = source_text[4:closing]
    body = source_text[closing + 4 :].lstrip("\r\n")
    data: dict[str, object] = {}
    for line_number, raw_line in enumerate(block.splitlines(), start=2):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise InstallConflict(f"Invalid agent frontmatter line {line_number}")
        key, value = line.split(":", 1)
        key = key.strip()
        if key in data:
            raise InstallConflict(f"Duplicate agent frontmatter field: {key}")
        data[key] = parse_source_scalar(value)
    return data, body


def render_opencode_agent(source_text: str, source_filename: str) -> tuple[str, str]:
    validate_managed_filename(source_filename, "copilot")
    data, body = parse_source_frontmatter(source_text)
    name = data.get("name")
    description = data.get("description")
    tools = data.get("tools")
    agents = data.get("agents")
    user_invocable = data.get("user-invocable")
    if not isinstance(name, str) or not name:
        raise InstallConflict(f"{source_filename} is missing a valid name")
    if not isinstance(description, str) or not description:
        raise InstallConflict(f"{source_filename} is missing a valid description")
    if not isinstance(tools, list) or not all(isinstance(item, str) for item in tools):
        raise InstallConflict(f"{source_filename} has invalid tools")
    if not isinstance(agents, list) or not all(isinstance(item, str) for item in agents):
        raise InstallConflict(f"{source_filename} has invalid agents")
    if not isinstance(user_invocable, bool):
        raise InstallConflict(f"{source_filename} has invalid user-invocable")

    granted: set[str] = set()
    for tool in tools:
        granted.update(SOURCE_TOOL_PERMISSIONS.get(tool, ()))
    is_orchestrator = name == "orchestrator"
    mode = "primary" if is_orchestrator else "all" if user_invocable else "subagent"
    lines = [
        "---",
        f"description: {json.dumps(description, ensure_ascii=False)}",
        f"mode: {mode}",
    ]
    if mode == "subagent":
        lines.append("hidden: true")
    lines.append("permission:")
    for permission in SIMPLE_PERMISSIONS:
        lines.append(
            f"  {permission}: {'allow' if permission in granted else 'deny'}"
        )
    if is_orchestrator:
        lines.extend(("  task:", '    "*": deny'))
        for agent in agents:
            lines.append(f"    {json.dumps(agent)}: allow")
    else:
        lines.append("  task: deny")
    lines.append(
        f'  "doct_playwright_*": {"allow" if name == "browser-agent" else "deny"}'
    )
    lines.extend(("---", "", body))
    filename = f"{name}.md"
    validate_managed_filename(filename, "opencode")
    return filename, "\n".join(lines)


def render_opencode_agents(source_dir: Path, output_dir: Path) -> list[Path]:
    output_dir = prepare_target(output_dir)
    rendered: list[Path] = []
    for source in find_agent_files(source_dir, "copilot"):
        filename, text = render_opencode_agent(
            source.read_text(encoding="utf-8"), source.name
        )
        destination = output_dir / filename
        destination.write_text(text, encoding="utf-8")
        rendered.append(destination)
    return sorted(rendered, key=lambda path: path.name)


def strip_jsonc(text: str) -> str:
    output: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            output.extend((" ", " "))
            index += 2
            while index < len(text) and text[index] != "\n":
                output.append(" ")
                index += 1
            continue
        if char == "/" and next_char == "*":
            output.extend((" ", " "))
            index += 2
            while index < len(text):
                if text[index : index + 2] == "*/":
                    output.extend((" ", " "))
                    index += 2
                    break
                output.append("\n" if text[index] == "\n" else " ")
                index += 1
            continue
        output.append(char)
        index += 1
    return re.sub(r",\s*([}\]])", r"\1", "".join(output))


def parse_json_or_jsonc(text: str) -> tuple[dict[str, object], bool]:
    try:
        parsed = json.loads(text)
        strict = True
    except json.JSONDecodeError:
        try:
            parsed = json.loads(strip_jsonc(text))
            strict = False
        except json.JSONDecodeError as exc:
            raise InstallConflict(f"Cannot parse OpenCode config: {exc}") from exc
    if not isinstance(parsed, dict):
        raise InstallConflict("OpenCode config root must be an object")
    return parsed, strict


def skip_trivia(text: str, start: int) -> int:
    index = start
    while index < len(text):
        if text[index].isspace():
            index += 1
            continue
        if text[index : index + 2] == "//":
            index += 2
            while index < len(text) and text[index] != "\n":
                index += 1
            continue
        if text[index : index + 2] == "/*":
            index += 2
            while index < len(text) and text[index : index + 2] != "*/":
                index += 1
            if index >= len(text):
                raise InstallConflict("Unterminated block comment in OpenCode config")
            index += 2
            continue
        break
    return index


def string_end(text: str, start: int) -> int:
    if text[start] != '"':
        raise InstallConflict("Expected JSON string")
    escaped = False
    index = start + 1
    while index < len(text):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            return index + 1
        index += 1
    raise InstallConflict("Unterminated string in OpenCode config")


def composite_end(text: str, start: int) -> int:
    opener = text[start]
    if opener not in "{[":
        raise InstallConflict("Expected JSON object or array")
    stack = ["}" if opener == "{" else "]"]
    index = start + 1
    while index < len(text):
        index = skip_trivia(text, index)
        if index >= len(text):
            break
        char = text[index]
        if char == '"':
            index = string_end(text, index)
            continue
        if char in "{[":
            stack.append("}" if char == "{" else "]")
            index += 1
            continue
        if char == stack[-1]:
            stack.pop()
            index += 1
            if not stack:
                return index
            continue
        index += 1
    raise InstallConflict("Unterminated composite value in OpenCode config")


def value_end(text: str, start: int) -> int:
    index = skip_trivia(text, start)
    if text[index] == '"':
        return string_end(text, index)
    if text[index] in "{[":
        return composite_end(text, index)
    cursor = index
    while cursor < len(text) and text[cursor] not in ",}]":
        cursor += 1
    while cursor > index and text[cursor - 1].isspace():
        cursor -= 1
    return cursor


def object_close(text: str, start: int) -> int:
    return composite_end(text, start) - 1


def find_object_property(
    text: str, object_start: int, target_key: str
) -> Optional[dict[str, int]]:
    if text[object_start] != "{":
        raise InstallConflict("Expected object while patching OpenCode config")
    close = object_close(text, object_start)
    cursor = object_start + 1
    while cursor < close:
        cursor = skip_trivia(text, cursor)
        if cursor >= close:
            break
        if text[cursor] == ",":
            cursor += 1
            continue
        if text[cursor] != '"':
            raise InstallConflict("OpenCode config object keys must be quoted")
        key_start = cursor
        key_end = string_end(text, cursor)
        try:
            key = json.loads(text[key_start:key_end])
        except json.JSONDecodeError as exc:
            raise InstallConflict(f"Invalid OpenCode config key: {exc}") from exc
        cursor = skip_trivia(text, key_end)
        if text[cursor] != ":":
            raise InstallConflict("Expected ':' after OpenCode config key")
        colon = cursor
        start = skip_trivia(text, cursor + 1)
        end = value_end(text, start)
        cursor = skip_trivia(text, end)
        comma = cursor if cursor < len(text) and text[cursor] == "," else -1
        if key == target_key:
            return {
                "key_start": key_start,
                "key_end": key_end,
                "colon": colon,
                "value_start": start,
                "value_end": end,
                "comma": comma,
                "object_close": close,
            }
        cursor = cursor if comma < 0 else comma + 1
    return None


def line_indent(text: str, position: int) -> str:
    line_start = text.rfind("\n", 0, position) + 1
    prefix = text[line_start:position]
    return prefix if not prefix.strip() else ""


def format_json_value(value: object, property_indent: str) -> str:
    rendered = json.dumps(value, indent=2, ensure_ascii=False)
    return rendered.replace("\n", "\n" + property_indent)


def insert_jsonc_property(text: str, object_start: int, key: str, value: object) -> str:
    close = object_close(text, object_start)
    close_line_start = text.rfind("\n", 0, close) + 1
    close_prefix = text[close_line_start:close]
    multiline_close = not close_prefix.strip()
    close_indent = close_prefix if multiline_close else line_indent(text, object_start)
    property_indent = close_indent + "  "
    entry = (
        f"{property_indent}{json.dumps(key)}: "
        f"{format_json_value(value, property_indent)},"
    )
    semantic = json.loads(strip_jsonc(text[object_start : close + 1]))
    insert_at = close_line_start if multiline_close else close
    if not semantic:
        insertion = f"{entry}\n" if multiline_close else f"\n{entry}\n{close_indent}"
        return text[:insert_at] + insertion + text[insert_at:]
    stripped_prefix = strip_jsonc(text[object_start:insert_at]).rstrip()
    has_trailing_comma = stripped_prefix.endswith(",")
    insertion = (
        f"{'' if has_trailing_comma else ','}\n{entry}\n"
        if multiline_close
        else f"{'' if has_trailing_comma else ','}\n{entry}\n{close_indent}"
    )
    return text[:insert_at] + insertion + text[insert_at:]


def replace_jsonc_property_value(
    text: str, property_info: dict[str, int], value: object
) -> str:
    indent = line_indent(text, property_info["key_start"])
    return (
        text[: property_info["value_start"]]
        + format_json_value(value, indent)
        + text[property_info["value_end"] :]
    )


def remove_jsonc_property(
    text: str, property_info: dict[str, int], object_start: int
) -> str:
    key_start = property_info["key_start"]
    line_start = text.rfind("\n", 0, key_start) + 1
    before_key = text[line_start:key_start]
    comma = property_info["comma"]
    if comma >= 0 and not before_key.strip():
        end = comma + 1
        while end < len(text) and text[end] in " \t":
            end += 1
        if end < len(text) and text[end] == "\r":
            end += 1
        if end < len(text) and text[end] == "\n":
            end += 1
        return text[:line_start] + text[end:]
    start = key_start
    if comma < 0:
        cursor = key_start - 1
        while cursor > object_start and text[cursor].isspace():
            cursor -= 1
        if text[cursor] == ",":
            start = cursor
    end = property_info["value_end"] if comma < 0 else comma + 1
    return text[:start] + text[end:]


def patch_opencode_config(
    text: str,
    *,
    expected_hash: Optional[str] = None,
    force: bool = False,
    remove: bool = False,
) -> OpenCodeConfigPatch:
    if not isinstance(text, str):
        raise InstallConflict("OpenCode config text must be a string")
    normalized_text = text or "{}\n"
    root, strict = parse_json_or_jsonc(normalized_text)
    mcp = root.get("mcp")
    if mcp is not None and not isinstance(mcp, dict):
        raise InstallConflict("OpenCode config mcp must be an object")
    current = mcp.get("doct_playwright") if isinstance(mcp, dict) else None
    current_hash = hash_json_value(current) if current is not None else None
    desired_hash = hash_json_value(PLAYWRIGHT_MCP)
    if (
        current is not None
        and expected_hash
        and current_hash != expected_hash.lower()
        and not force
    ):
        raise InstallConflict(
            "Managed OpenCode doct_playwright entry was modified after installation"
        )
    if (
        current is not None
        and not expected_hash
        and not force
        and current_hash != desired_hash
    ):
        raise InstallConflict(
            "OpenCode doct_playwright entry already exists and is not managed by doct-agents"
        )

    if strict:
        next_root = copy.deepcopy(root)
        next_mcp = next_root.get("mcp")
        if next_mcp is None and not remove:
            next_mcp = {}
            next_root["mcp"] = next_mcp
        if isinstance(next_mcp, dict):
            if remove:
                next_mcp.pop("doct_playwright", None)
            else:
                next_mcp["doct_playwright"] = copy.deepcopy(PLAYWRIGHT_MCP)
        rendered = json.dumps(next_root, indent=2, ensure_ascii=False) + "\n"
        return OpenCodeConfigPatch(
            rendered,
            desired_hash,
            current_hash != (None if remove else desired_hash),
        )

    root_start = skip_trivia(normalized_text, 0)
    if normalized_text[root_start] != "{":
        raise InstallConflict("OpenCode config root must be an object")
    mcp_property = find_object_property(normalized_text, root_start, "mcp")
    next_text = normalized_text
    if mcp_property is None:
        if not remove:
            next_text = insert_jsonc_property(
                normalized_text,
                root_start,
                "mcp",
                {"doct_playwright": PLAYWRIGHT_MCP},
            )
    else:
        mcp_start = mcp_property["value_start"]
        if normalized_text[mcp_start] != "{":
            raise InstallConflict("OpenCode config mcp must be an object")
        doct_property = find_object_property(
            normalized_text, mcp_start, "doct_playwright"
        )
        if remove:
            if doct_property is not None:
                next_text = remove_jsonc_property(
                    normalized_text, doct_property, mcp_start
                )
        elif doct_property is not None:
            next_text = replace_jsonc_property_value(
                normalized_text, doct_property, PLAYWRIGHT_MCP
            )
        else:
            next_text = insert_jsonc_property(
                normalized_text, mcp_start, "doct_playwright", PLAYWRIGHT_MCP
            )
    return OpenCodeConfigPatch(next_text, desired_hash, next_text != normalized_text)


def opencode_config_path(target_dir: Path) -> Path:
    config_dir = normalize_target(target_dir).parent
    jsonc = config_dir / "opencode.jsonc"
    json_path = config_dir / "opencode.json"
    if lstat_or_none(jsonc) is not None:
        return jsonc
    if lstat_or_none(json_path) is not None:
        return json_path
    return json_path


def detect_opencode(
    *,
    workspace: Path,
    home: Optional[Path] = None,
    path_env: Optional[str] = None,
) -> bool:
    resolved_home = Path.home() if home is None else home
    workspace_config = normalize_target(workspace) / ".opencode"
    user_config = normalize_target(resolved_home) / ".config" / "opencode"
    for directory in (workspace_config, user_config):
        entry = lstat_or_none(directory)
        if entry is not None and stat.S_ISDIR(entry.st_mode) and not is_link_like(entry):
            return True
    names = (
        (
            "opencode.exe",
            "opencode.cmd",
            "opencode.bat",
            "opencode2.exe",
            "opencode2.cmd",
            "opencode2.bat",
        )
        if os.name == "nt"
        else ("opencode", "opencode2")
    )
    effective_path = os.environ.get("PATH", "") if path_env is None else path_env
    for directory in filter(None, effective_path.split(os.pathsep)):
        for name in names:
            candidate = Path(directory) / name
            entry = lstat_or_none(candidate)
            if entry is not None and stat.S_ISREG(entry.st_mode) and not is_link_like(entry):
                return True
    return False


def config_path_from_manifest(target: Path, manifest: dict[str, object]) -> Path:
    config = manifest.get("config")
    if isinstance(config, dict) and isinstance(config.get("filename"), str):
        return normalize_target(target).parent / str(config["filename"])
    return opencode_config_path(target)


def read_regular_text(path: Path, fallback: Optional[str] = None) -> Optional[str]:
    entry = lstat_or_none(path)
    if entry is None:
        return fallback
    if is_link_like(entry):
        raise InstallConflict(f"Config is a symbolic link or junction: {path}")
    if not stat.S_ISREG(entry.st_mode):
        raise InstallConflict(f"Config is not a regular file: {path}")
    return path.read_text(encoding="utf-8")


def write_regular_text_atomic(path: Path, text: str) -> None:
    parent = prepare_target(path.parent)
    current = lstat_or_none(path)
    if current is not None:
        if is_link_like(current):
            raise InstallConflict(f"Config is a symbolic link or junction: {path}")
        if not stat.S_ISREG(current.st_mode):
            raise InstallConflict(f"Config is not a regular file: {path}")
    stage = Path(
        tempfile.mkdtemp(prefix=f".{path.name}.doct-agents-config-", dir=str(parent))
    )
    staged = stage / "next"
    backup = stage / "previous"
    staged.write_text(text, encoding="utf-8")
    moved_original = False
    preserve_stage = False
    try:
        if current is not None:
            os.replace(path, backup)
            moved_original = True
        os.replace(staged, path)
    except BaseException as exc:
        try:
            if lstat_or_none(path):
                path.unlink()
            if moved_original and lstat_or_none(backup):
                os.replace(backup, path)
        except OSError as rollback_error:
            preserve_stage = True
            raise InstallConflict(
                f"{exc}; config rollback also failed: {rollback_error}; backup at {stage}"
            ) from exc
        raise
    finally:
        if not preserve_stage:
            shutil.rmtree(stage, ignore_errors=True)


def restore_config(path: Path, previous_text: str, existed: bool) -> None:
    if existed:
        write_regular_text_atomic(path, previous_text)
        return
    entry = lstat_or_none(path)
    if entry is not None:
        if is_link_like(entry):
            raise InstallConflict(f"Config is a symbolic link or junction: {path}")
        path.unlink()


def install_opencode(
    source_dir: Path,
    target_dir: Path,
    *,
    force: bool = False,
) -> tuple[InstallResult, Path]:
    target = normalize_target(target_dir)
    previous_manifest = load_manifest(target, "opencode")
    config_path = config_path_from_manifest(target, previous_manifest)
    previous_text = read_regular_text(config_path, "{}\n")
    assert previous_text is not None
    config_existed = lstat_or_none(config_path) is not None
    config = previous_manifest.get("config")
    expected_hash = (
        str(config.get("mcpEntrySha256"))
        if isinstance(config, dict) and config.get("mcpEntrySha256")
        else None
    )
    patch = patch_opencode_config(
        previous_text,
        expected_hash=expected_hash,
        force=force,
    )

    parent = prepare_target(config_path.parent)
    render_dir = Path(
        tempfile.mkdtemp(prefix=".doct-agents-opencode-render-", dir=str(parent))
    )
    try:
        render_opencode_agents(source_dir, render_dir)
        write_regular_text_atomic(config_path, patch.text)
        try:
            result = install_agents(
                render_dir,
                target,
                force=force,
                platform="opencode",
                manifest_metadata={
                    "config": {
                        "filename": config_path.name,
                        "mcpEntrySha256": patch.mcp_entry_sha256,
                    }
                },
            )
            return result, config_path
        except BaseException:
            restore_config(config_path, previous_text, config_existed)
            raise
    finally:
        shutil.rmtree(render_dir, ignore_errors=True)


def get_opencode_status(target_dir: Path) -> OpenCodeStatus:
    target = normalize_target(target_dir)
    status = get_status(target, "opencode")
    manifest = load_manifest(target, "opencode")
    config = manifest.get("config")
    if not isinstance(config, dict):
        return OpenCodeStatus(
            status.installed,
            status.modified,
            status.missing,
            status.target,
            "missing",
            opencode_config_path(target),
        )
    config_path = config_path_from_manifest(target, manifest)
    text = read_regular_text(config_path, None)
    if text is None:
        config_status = "missing"
    else:
        try:
            probe = patch_opencode_config(
                text, expected_hash=str(config["mcpEntrySha256"])
            )
            config_status = "missing" if probe.changed else "installed"
        except InstallConflict as exc:
            if "modified" in str(exc).lower():
                config_status = "modified"
            else:
                raise
    return OpenCodeStatus(
        status.installed,
        status.modified,
        status.missing,
        status.target,
        config_status,
        config_path,
    )


def uninstall_opencode(
    target_dir: Path,
    *,
    force: bool = False,
) -> OpenCodeUninstallResult:
    target = normalize_target(target_dir)
    manifest = load_manifest(target, "opencode")
    config = manifest.get("config")
    config_path: Optional[Path] = None
    original_text: Optional[str] = None
    patch: Optional[OpenCodeConfigPatch] = None
    config_preserved = False
    if isinstance(config, dict):
        config_path = config_path_from_manifest(target, manifest)
        original_text = read_regular_text(config_path, None)
        if original_text is not None:
            try:
                patch = patch_opencode_config(
                    original_text,
                    expected_hash=str(config["mcpEntrySha256"]),
                    force=force,
                    remove=True,
                )
            except InstallConflict as exc:
                if not force and "modified" in str(exc).lower():
                    config_preserved = True
                else:
                    raise

    result = uninstall_agents(target, force=force, platform="opencode")
    if patch is not None and patch.changed and config_path is not None:
        write_regular_text_atomic(config_path, patch.text)
    return OpenCodeUninstallResult(
        result.removed,
        result.preserved,
        result.target,
        config_preserved,
        config_path,
    )


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
        description="Manage doct-agents for GitHub Copilot and OpenCode."
    )
    parser.add_argument(
        "command",
        choices=("install", "update", "status", "uninstall"),
        nargs="?",
        default="install",
    )
    parser.add_argument(
        "--platform", choices=("copilot", "opencode", "all"), default=None
    )
    parser.add_argument("--scope", choices=("user", "workspace"), default="user")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--target", type=Path)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--repository", default=REPOSITORY)
    parser.add_argument("--ref", default=DEFAULT_REF)
    parser.add_argument("--force", action="store_true")
    return parser


def selected_platforms(args: argparse.Namespace) -> list[str]:
    if args.platform == "all":
        return ["copilot", "opencode"]
    if args.platform:
        return [args.platform]
    if args.target:
        return ["copilot"]
    if args.command in {"status", "uninstall"}:
        return ["copilot"]
    return (
        ["copilot", "opencode"]
        if detect_opencode(workspace=args.workspace)
        else ["copilot"]
    )


def platform_target(args: argparse.Namespace, platform: str) -> Path:
    if args.target:
        return normalize_target(args.target)
    return default_target(args.scope, args.workspace, platform=platform)


def print_status(platform: str, status, prefix: str) -> None:
    print(f"{prefix}Target: {status.target}")
    print(f"{prefix}Installed: {len(status.installed)}")
    print(f"{prefix}Modified: {', '.join(status.modified) if status.modified else 'none'}")
    print(f"{prefix}Missing: {', '.join(status.missing) if status.missing else 'none'}")
    if platform == "opencode":
        print(f"{prefix}Browser MCP config: {status.config}")


def run_platform(
    args: argparse.Namespace,
    platform: str,
    source_dir: Optional[Path],
    multiple: bool,
) -> int:
    target = platform_target(args, platform)
    prefix = f"[{platform}] " if multiple else ""
    if args.command == "status":
        status = (
            get_opencode_status(target)
            if platform == "opencode"
            else get_status(target, "copilot")
        )
        if not (status.installed or status.modified or status.missing):
            print(f"{prefix}doct-agents is not installed in {status.target}")
            return 1
        print_status(platform, status, prefix)
        config_bad = platform == "opencode" and status.config in {"modified", "missing"}
        return 2 if status.modified or status.missing or config_bad else 0

    if args.command == "uninstall":
        result = (
            uninstall_opencode(target, force=args.force)
            if platform == "opencode"
            else uninstall_agents(target, force=args.force, platform="copilot")
        )
        print(f"{prefix}Removed {result.removed} managed agent files from {result.target}")
        if result.preserved:
            print(f"{prefix}Preserved modified files: {', '.join(result.preserved)}")
        config_preserved = bool(
            platform == "opencode" and getattr(result, "config_preserved", False)
        )
        if config_preserved:
            print(f"{prefix}Preserved modified OpenCode doct_playwright MCP config")
        return 2 if result.preserved or config_preserved else 0

    if source_dir is None:
        raise RuntimeError("Agent source is required for install/update")
    if platform == "opencode":
        result, config_path = install_opencode(source_dir, target, force=args.force)
    else:
        result = install_agents(source_dir, target, force=args.force, platform="copilot")
        config_path = None
    verb = "Updated" if args.command == "update" else "Installed"
    print(f"{prefix}{verb} {result.installed} agents in {result.target}")
    if config_path is not None:
        print(f"{prefix}Configured isolated Playwright MCP in {config_path}")
    return 0


def execute(args: argparse.Namespace, source_dir: Optional[Path]) -> int:
    if args.platform == "all" and args.target:
        raise InstallConflict("--target cannot be combined with --platform all")
    platforms = selected_platforms(args)
    exit_code = 0
    for platform in platforms:
        try:
            exit_code = max(
                exit_code,
                run_platform(args, platform, source_dir, len(platforms) > 1),
            )
        except (FileNotFoundError, InstallConflict, RuntimeError, OSError) as exc:
            if len(platforms) == 1:
                raise
            print(f"[{platform}] error: {exc}", file=sys.stderr)
            exit_code = max(exit_code, 1)
    return exit_code


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command in {"install", "update"}:
            if args.source_dir:
                return execute(args, args.source_dir)
            with tempfile.TemporaryDirectory(prefix="doct-agents-") as temp_dir:
                source_dir = download_source(args.repository, args.ref, Path(temp_dir))
                return execute(args, source_dir)
        return execute(args, None)
    except (FileNotFoundError, InstallConflict, RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate VS Code custom agent definitions without third-party dependencies."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_FIELDS = {"name", "description", "tools", "agents", "user-invocable"}
USER_INVOCABLE_ALLOWLIST = {"orchestrator", "cli-executor"}
EDIT_EXECUTE_ALLOWLIST = {"test-agent"}
SUBAGENT_ROUTER_ALLOWLIST = {"orchestrator"}
COMMON_WORKER_STATUSES = {"completed", "needs-info", "blocked", "failed"}
STATUS_LINE_PATTERN = re.compile(r"^\s*-\s*`?Status`?\s*:\s*(.+)$", re.MULTILINE)
BACKTICK_VALUE_PATTERN = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class Agent:
    path: Path
    name: str
    tools: tuple[str, ...]
    agents: tuple[str, ...]
    user_invocable: bool


def parse_scalar(value: str):
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


def parse_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", text, re.DOTALL)
    if not match:
        raise ValueError("missing YAML frontmatter")

    data: dict[str, object] = {}
    for line_number, raw_line in enumerate(match.group(1).splitlines(), start=2):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"line {line_number}: expected key: value")
        key, value = line.split(":", 1)
        key = key.strip()
        if key in data:
            raise ValueError(f"line {line_number}: duplicate field {key}")
        data[key] = parse_scalar(value)
    return data


def declared_status_values(text: str) -> set[str]:
    values: set[str] = set()
    for match in STATUS_LINE_PATTERN.finditer(text):
        for quoted in BACKTICK_VALUE_PATTERN.findall(match.group(1)):
            for value in quoted.split("|"):
                normalized = value.strip().strip(".,").lower()
                if normalized:
                    values.add(normalized)
    return values


def load_agents(directory: Path) -> tuple[list[Agent], list[str]]:
    loaded: list[Agent] = []
    errors: list[str] = []
    for path in sorted(directory.glob("*.agent.md")):
        try:
            data = parse_frontmatter(path)
            missing = sorted(REQUIRED_FIELDS - data.keys())
            if missing:
                raise ValueError(f"missing fields: {', '.join(missing)}")
            if not isinstance(data["name"], str) or not data["name"]:
                raise ValueError("name must be a non-empty string")
            if not isinstance(data["description"], str) or not data["description"]:
                raise ValueError("description must be a non-empty string")
            if not isinstance(data["tools"], list):
                raise ValueError("tools must be a string list")
            if not isinstance(data["agents"], list):
                raise ValueError("agents must be a string list")
            if not isinstance(data["user-invocable"], bool):
                raise ValueError("user-invocable must be true or false")
            loaded.append(
                Agent(
                    path=path,
                    name=data["name"],
                    tools=tuple(data["tools"]),
                    agents=tuple(data["agents"]),
                    user_invocable=data["user-invocable"],
                )
            )
        except (OSError, SyntaxError, ValueError) as exc:
            errors.append(f"{path}: {exc}")
    return loaded, errors


def validate(directory: Path) -> list[str]:
    agents, errors = load_agents(directory)
    by_name: dict[str, Agent] = {}

    for agent in agents:
        if agent.name in by_name:
            errors.append(f"{agent.path}: duplicate agent name '{agent.name}'")
        else:
            by_name[agent.name] = agent

    for agent in agents:
        unknown = sorted(set(agent.agents) - by_name.keys())
        for referenced in unknown:
            errors.append(f"{agent.path}: unknown agent reference '{referenced}'")

        if agent.name in agent.agents:
            errors.append(f"{agent.path}: agent cannot reference itself")
        if agent.agents and "agent" not in agent.tools:
            errors.append(f"{agent.path}: non-empty agents requires the 'agent' tool")
        if "agent" in agent.tools and not agent.agents:
            errors.append(f"{agent.path}: 'agent' tool requires at least one allowed agent")
        if agent.name not in SUBAGENT_ROUTER_ALLOWLIST and (
            agent.agents or "agent" in agent.tools
        ):
            errors.append(f"{agent.path}: only orchestrator may reference subagents")
        if agent.user_invocable and agent.name not in USER_INVOCABLE_ALLOWLIST:
            errors.append(f"{agent.path}: '{agent.name}' is not allowed to be user-invocable")
        if "edit" in agent.tools and "execute" in agent.tools and agent.name not in EDIT_EXECUTE_ALLOWLIST:
            errors.append(
                f"{agent.path}: edit+execute requires explicit allowlisting; "
                f"current allowlist: {', '.join(sorted(EDIT_EXECUTE_ALLOWLIST))}"
            )
        if len(agent.tools) != len(set(agent.tools)):
            errors.append(f"{agent.path}: duplicate tool entry")
        if len(agent.agents) != len(set(agent.agents)):
            errors.append(f"{agent.path}: duplicate agent reference")

        text = agent.path.read_text(encoding="utf-8")
        declared = declared_status_values(text)
        for status in sorted(declared - COMMON_WORKER_STATUSES):
            errors.append(
                f"{agent.path}: unsupported status value '{status}'; "
                f"worker statuses are {', '.join(sorted(COMMON_WORKER_STATUSES))}"
            )

    return sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default="agents", type=Path)
    args = parser.parse_args()

    errors = validate(args.directory)
    if errors:
        print("Agent validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    count = len(list(args.directory.glob("*.agent.md")))
    print(f"Validated {count} agent definitions successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

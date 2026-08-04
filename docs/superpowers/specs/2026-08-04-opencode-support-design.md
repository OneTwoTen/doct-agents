# OpenCode Support Design

## Goal

Add first-class OpenCode support to `doct-agents` without forking the agent prompts or regressing the existing GitHub Copilot installer behavior.

The same source files in `agents/*.agent.md` remain the single source of truth. Installation renders platform-specific output for OpenCode while Copilot keeps receiving the current files unchanged.

## Supported platforms

The CLI supports three explicit platform values:

- `copilot`
- `opencode`
- `all`

When `--platform` is omitted, the installer keeps Copilot behavior and additionally installs OpenCode when OpenCode is detected on the machine. Detection may use the `opencode`/`opencode2` executable or an existing OpenCode config directory. Explicit `--platform` always wins.

`--target` without an explicit platform preserves legacy semantics and targets Copilot only. A custom target with `--platform all` is rejected because one path cannot safely represent two platform layouts.

## Target locations

| Scope | Copilot | OpenCode |
| --- | --- | --- |
| `user` | `~/.copilot/agents` | `~/.config/opencode/agents` |
| `workspace` | `.github/agents` | `.opencode/agents` |

OpenCode output files use `<agent-name>.md`; Copilot keeps `<agent-name>.agent.md`.

## Source and rendering model

`agents/*.agent.md` stays platform-neutral in the body and Copilot-oriented in frontmatter. A renderer parses the existing frontmatter and emits OpenCode Markdown frontmatter plus the shared Markdown body.

The renderer does not maintain a second checked-in prompt tree. Generated OpenCode files exist only in install staging/targets.

### Agent mode mapping

- `orchestrator` => `mode: primary`
- `user-invocable: true` workers such as `cli-executor` => `mode: all`
- other workers => `mode: subagent`, `hidden: true`

OpenCode task routing is controlled through `permission.task`:

- orchestrator starts with `"*": "deny"` then explicitly allows every agent listed in the source `agents` frontmatter.
- workers deny `task` so they cannot route peer workers.

This preserves the repository invariant that orchestrator owns routing.

## Tool and permission mapping

The renderer maps Copilot capabilities to OpenCode permission keys rather than copying Copilot tool names literally.

| Source capability | OpenCode permission |
| --- | --- |
| `read` | `read` |
| `search` | `glob`, `grep` |
| `edit` | `edit` |
| `execute` | `bash` |
| `agent` | `task` |
| `todo` | `todowrite` |
| `vscode/askQuestions` | `question` |
| `web` | `webfetch`, `websearch` |

Permissions not granted by a source agent are explicitly denied for sensitive capabilities (`edit`, `bash`, `task`, browser MCP). This prevents global OpenCode defaults from accidentally expanding worker authority.

## Browser support

OpenCode browser validation uses the official Microsoft Playwright MCP package, pinned to `@playwright/mcp@0.0.78`.

The managed OpenCode MCP entry is named `doct_playwright` and uses:

```json
{
  "type": "local",
  "command": ["npx", "-y", "@playwright/mcp@0.0.78", "--isolated"],
  "enabled": true
}
```

Stable OpenCode stores server entries directly under `mcp`. The installer targets this V1-compatible shape because OpenCode 2 currently documents migration/compatibility separately and the project must not depend on beta-only config.

The rendered `browser-agent` receives `doct_playwright_*: allow`; other agents receive `doct_playwright_*: deny`.

The browser-agent body is made runtime-neutral: it describes browser automation capabilities instead of hard-coding VS Code Browser tool names. Copilot continues using its original Browser tools through frontmatter; OpenCode uses Playwright MCP through rendered permissions.

## OpenCode config management

The installer manages only `mcp.doct_playwright` in the OpenCode config and must preserve all unrelated user configuration.

Config selection:

- workspace: `.opencode/opencode.jsonc` when present, otherwise `.opencode/opencode.json` when present, otherwise create `.opencode/opencode.json`.
- user: use the corresponding OpenCode config directory and prefer an existing `opencode.jsonc`, then `opencode.json`, otherwise create `opencode.json`.

JSONC parsing supports comments and trailing commas sufficiently for normal OpenCode configuration. Writes must preserve unrelated semantic content; formatting/comments may be preserved when safely patching the single managed property. If safe structural patching is not possible, installation must stop rather than rewrite the entire user config destructively.

The installer tracks the exact managed MCP value in its manifest. Update/uninstall may replace or remove the entry only when it still matches the previously managed value. A locally modified `doct_playwright` entry is treated as modified and protected unless `--force` is used.

## Manifest compatibility

Existing schema-1 Copilot manifests remain readable and behave unchanged.

OpenCode installs use a manifest that can record:

- platform identity,
- managed generated agent filenames and hashes,
- managed OpenCode config path,
- managed MCP entry value/hash.

The implementation may introduce schema 2, but schema 1 remains fully supported for existing Copilot installs.

## Installer behavior

`install`, `update`, `status`, and `uninstall` operate per platform.

For `--platform all`, each platform reports independently. A failure in one platform must not silently report overall success. Installation should stage each platform before mutating that platform's target and retain the existing rollback/symlink protections.

Auto mode never silently removes a platform. `uninstall` without `--platform` follows legacy Copilot-only behavior; users must explicitly request `opencode` or `all` to remove OpenCode files/config.

Node and Python installers must expose equivalent platform behavior.

## Detection

Auto-install detection is intentionally conservative:

- Copilot is always included for backward compatibility.
- OpenCode is additionally included when `opencode` or `opencode2` is found on PATH, or when a standard OpenCode user/workspace config directory already exists.

Detection affects only `install` and `update`; explicit `--platform` is preferred for automation/CI.

## Validation

Required tests cover:

1. existing Copilot target and schema-1 behavior remain unchanged;
2. OpenCode user/workspace targets;
3. explicit `copilot`, `opencode`, `all`, plus auto-detection;
4. renderer emits every source agent with valid OpenCode frontmatter;
5. no Copilot-only frontmatter keys leak into OpenCode output;
6. orchestrator task allowlist matches its declared source agents;
7. workers cannot launch peer workers;
8. source tool permissions map correctly for implementation, CLI, research, and browser agents;
9. only browser-agent can access `doct_playwright_*`;
10. OpenCode JSON and JSONC merge preserves unrelated config and MCP entries;
11. modified managed MCP config is protected and reported by status;
12. uninstall removes only the unchanged managed MCP entry;
13. Node and Python implementations behave consistently;
14. existing path traversal, symlink/junction, staged-update, rollback, package smoke, and release checks do not regress.

## Non-goals

- no duplicated `agents-opencode/` source tree;
- no OpenCode provider/model configuration;
- no OpenCode 2 beta-only agent/config format;
- no browser authentication/profile persistence by default;
- no automatic installation of Node.js, OpenCode, browsers, or Playwright dependencies outside the MCP command lifecycle.

# OpenCode Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add first-class OpenCode agent installation, routing permissions, and Playwright MCP browser support while preserving existing Copilot behavior.

**Architecture:** Keep `agents/*.agent.md` as the only prompt source. Refactor the installer file-management core to accept a platform, render OpenCode Markdown into a temporary source directory, then reuse the same staged/checksummed install lifecycle. Manage only `mcp.doct_playwright` in the OpenCode config and protect local modifications through schema-2 manifest metadata.

**Tech Stack:** Node.js 18+ ESM, Python 3.9+ standard library, Node test runner, Python unittest, OpenCode Markdown agents, OpenCode V1-compatible config, `@playwright/mcp@0.0.78`.

## Global Constraints

- Existing Copilot installs and schema-1 manifests remain fully compatible.
- Source prompts remain only in `agents/*.agent.md`; do not add an `agents-opencode` source tree.
- OpenCode user agents: `~/.config/opencode/agents`; workspace agents: `.opencode/agents`.
- OpenCode generated filenames are `<name>.md`.
- Browser MCP entry is exactly `mcp.doct_playwright` with `@playwright/mcp@0.0.78` and `--isolated`.
- Orchestrator is the only agent allowed to invoke task subagents.
- Node and Python installers expose equivalent platform behavior.
- Existing path traversal, symlink/junction, staging, rollback, and modified-file protections must remain intact.

---

### Task 1: Define renderer and target contracts in Node tests

**Files:**
- Modify: `tests/test_cli.mjs`
- Modify: `bin/doct-agents.js`

**Interfaces:**
- Produces: `defaultTarget(scope, workspace, home, platform = "copilot") -> string`
- Produces: `renderOpenCodeAgent(sourceText, filename) -> { filename: string, text: string }`
- Produces: `renderOpenCodeAgents(sourceDir, outputDir) -> string[]`

- [ ] **Step 1: Add failing target tests**

Add assertions that Copilot defaults remain unchanged and OpenCode resolves to `~/.config/opencode/agents` for user scope and `.opencode/agents` for workspace scope.

- [ ] **Step 2: Add failing renderer tests using representative frontmatter**

Cover these exact cases:

```js
const orchestrator = `---
name: orchestrator
description: "route"
tools: ["agent", "read", "search", "todo", "vscode/askQuestions"]
agents: ["review-agent", "implementation-agent"]
user-invocable: true
---
body
`;
```

Expected output requirements:

```text
filename = orchestrator.md
mode = primary
permission.task["*"] = deny
permission.task["review-agent"] = allow
permission.task["implementation-agent"] = allow
permission.read = allow
permission.glob = allow
permission.grep = allow
permission.todowrite = allow
permission.question = allow
permission.edit = deny
permission.bash = deny
permission["doct_playwright_*"] = deny
```

Also test:

```text
implementation-agent: mode=subagent hidden=true edit=allow bash=deny task=deny
cli-executor: mode=all bash=allow edit=deny task=deny
research-agent: webfetch=allow websearch=allow edit=deny
browser-agent: doct_playwright_*=allow
```

Assert generated output does not contain `name:`, `tools:`, `agents:`, `user-invocable:`, or `argument-hint:` from Copilot frontmatter.

- [ ] **Step 3: Run the focused Node tests and confirm failure**

Run:

```bash
node --test tests/test_cli.mjs
```

Expected: new target/renderer tests fail because platform rendering does not exist.

- [ ] **Step 4: Implement the minimal frontmatter parser and OpenCode renderer**

In `bin/doct-agents.js`, reuse the source's simple flat frontmatter conventions and render nested OpenCode permission YAML. Map:

```js
const TOOL_PERMISSION_MAP = {
  read: ["read"],
  search: ["glob", "grep"],
  edit: ["edit"],
  execute: ["bash"],
  agent: ["task"],
  todo: ["todowrite"],
  "vscode/askQuestions": ["question"],
  web: ["webfetch", "websearch"],
};
```

Sensitive permissions default to deny when absent. `browser-agent` alone gets `"doct_playwright_*": "allow"`.

- [ ] **Step 5: Run focused Node tests**

```bash
node --test tests/test_cli.mjs
```

Expected: renderer and target tests pass, all pre-existing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add tests/test_cli.mjs bin/doct-agents.js
git commit -m "feat: render agents for OpenCode"
```

---

### Task 2: Generalize Node managed-file manifests for OpenCode

**Files:**
- Modify: `tests/test_cli.mjs`
- Modify: `bin/doct-agents.js`

**Interfaces:**
- `validateManagedFilename(filename, platform = "copilot")`
- `loadManifest(targetDir, platform = "copilot")`
- `installAgents({ sourceDir, targetDir, force = false, platform = "copilot", manifestMetadata = null })`
- `getStatus(targetDir, { platform = "copilot" } = {})`
- `uninstallAgents(targetDir, { force = false, platform = "copilot" } = {})`

- [ ] **Step 1: Add failing schema-2 tests**

Require schema 1 to remain accepted for Copilot and define OpenCode schema 2:

```json
{
  "schema": 2,
  "package": "doct-agents",
  "repository": "OneTwoTen/doct-agents",
  "platform": "opencode",
  "files": {"orchestrator.md": "<sha256>"},
  "config": {
    "filename": "opencode.json",
    "mcpEntrySha256": "<sha256>"
  }
}
```

Reject platform mismatch, unsafe config filenames, and `.agent.md`/`.md` extension mismatches for the selected platform.

- [ ] **Step 2: Add failing OpenCode staged install/update/status/uninstall tests**

Create rendered `.md` fixture files, install with `platform: "opencode"`, modify one, verify status, force update, and uninstall. Keep the existing Copilot fixture tests untouched.

- [ ] **Step 3: Run focused tests and confirm failure**

```bash
node --test tests/test_cli.mjs
```

Expected: schema-2/platform tests fail.

- [ ] **Step 4: Generalize filename/manifest helpers without changing default Copilot behavior**

Schema 1 stays the canonical default for Copilot. OpenCode writes schema 2 and persists supplied config metadata. Preserve all existing stage/backup/rollback code paths.

- [ ] **Step 5: Run focused tests**

```bash
node --test tests/test_cli.mjs
```

Expected: all Node installer tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/test_cli.mjs bin/doct-agents.js
git commit -m "refactor: support platform managed files"
```

---

### Task 3: Add safe OpenCode config management in Node

**Files:**
- Modify: `tests/test_cli.mjs`
- Modify: `bin/doct-agents.js`

**Interfaces:**
- `openCodeConfigPath(scope, workspace, home, targetDir = null) -> string`
- `planOpenCodeConfig(configPath, { force = false, previousManifest = null }) -> { text, filename, mcpEntrySha256, changed, restoreText }`
- `removeManagedOpenCodeConfig(configPath, expectedHash, { force = false })`
- Managed entry:

```js
const PLAYWRIGHT_MCP = {
  type: "local",
  command: ["npx", "-y", "@playwright/mcp@0.0.78", "--isolated"],
  enabled: true,
};
```

- [ ] **Step 1: Add failing JSON config merge tests**

Cover empty config, existing unrelated keys, existing unrelated MCP server, matching managed entry, and locally modified `doct_playwright` conflict.

- [ ] **Step 2: Add failing JSONC preservation tests**

Use a fixture containing comments and trailing commas:

```jsonc
{
  // keep this comment
  "model": "example/model",
  "mcp": {
    "other": {
      "type": "local",
      "command": ["other"],
    },
  },
}
```

After adding/removing `doct_playwright`, assert the comment, model, and `other` MCP block remain present.

- [ ] **Step 3: Run focused tests and confirm failure**

```bash
node --test tests/test_cli.mjs
```

- [ ] **Step 4: Implement a narrow JSON/JSONC object patcher**

The patcher must scan strings, escapes, `//` comments, and `/* */` comments so it can find the root object and `mcp` object without stripping unrelated text. It only inserts/replaces/removes the `doct_playwright` property. If the root or `mcp` value is not an object, throw `InstallConflict` instead of rewriting the config.

Write config changes atomically through a sibling temporary file plus rename. Before replacing an existing managed entry, compare canonical SHA-256 with the manifest; modified entries require `--force`.

- [ ] **Step 5: Run focused tests**

```bash
node --test tests/test_cli.mjs
```

Expected: JSON/JSONC merge and protection tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/test_cli.mjs bin/doct-agents.js
git commit -m "feat: manage OpenCode Playwright MCP config"
```

---

### Task 4: Wire Node CLI platform selection and auto-detection

**Files:**
- Modify: `tests/test_cli.mjs`
- Modify: `bin/doct-agents.js`
- Modify: `scripts/smoke_package.mjs`

**Interfaces:**
- CLI option: `--platform copilot|opencode|all`
- Auto selection for install/update only: Copilot always plus OpenCode when an `opencode`/`opencode2` executable or standard OpenCode config directory is detected.
- Status/uninstall without `--platform` remain Copilot-only.

- [ ] **Step 1: Add failing argument and auto-detection tests**

Test explicit values, invalid platform, legacy `--target` behavior, fake PATH detection for `opencode` and `opencode2`, and `.opencode` workspace-directory detection.

- [ ] **Step 2: Add failing end-to-end Node run tests**

Capture console output and verify `install --platform opencode`, `status --platform opencode`, `uninstall --platform opencode`, and `--platform all` report each platform distinctly.

- [ ] **Step 3: Run focused tests and confirm failure**

```bash
node --test tests/test_cli.mjs
```

- [ ] **Step 4: Implement platform orchestration**

For OpenCode install/update:

1. render agents to a temporary directory;
2. plan and atomically write the MCP config;
3. install rendered agents with schema-2 metadata;
4. restore the prior config if the staged agent install fails.

For all-platform operations, process platforms independently, collect results, and return non-zero if any platform fails.

- [ ] **Step 5: Extend packaged CLI smoke test**

Keep the legacy `--target` smoke test and add a temporary workspace invocation:

```bash
doct-agents install --platform opencode --scope workspace --workspace <tmp>
doct-agents status --platform opencode --scope workspace --workspace <tmp>
doct-agents uninstall --platform opencode --scope workspace --workspace <tmp>
```

Assert `.opencode/agents/orchestrator.md` and `.opencode/opencode.json` are created, and uninstall removes only managed agent/config content.

- [ ] **Step 6: Run Node tests and package smoke**

```bash
npm test
npm run smoke:package
```

Expected: both pass.

- [ ] **Step 7: Commit**

```bash
git add tests/test_cli.mjs bin/doct-agents.js scripts/smoke_package.mjs
git commit -m "feat: add OpenCode platform CLI support"
```

---

### Task 5: Port the same contracts to the Python installer

**Files:**
- Modify: `tests/test_install_agents.py`
- Modify: `install.py`

**Interfaces:**
- `default_target(scope, workspace, platform="copilot", home=None)`
- `render_opencode_agent(source_text, filename)`
- platform-aware `install_agents`, `get_status`, `uninstall_agents`
- the same schema-2 and Playwright MCP value as Node
- argparse option `--platform {copilot,opencode,all}`

- [ ] **Step 1: Add failing Python renderer/target tests**

Mirror the Node representative agents and permission assertions. Parse generated frontmatter with test helpers rather than requiring a YAML dependency.

- [ ] **Step 2: Add failing schema-2 and OpenCode file lifecycle tests**

Mirror Node's schema/platform cases while preserving all current schema-1 tests.

- [ ] **Step 3: Add failing JSON/JSONC MCP merge/protection tests**

Use the same fixtures and expected semantic behavior as Node.

- [ ] **Step 4: Add failing CLI platform tests**

Patch PATH/home/workspace in tests to verify explicit selection and conservative auto-detection.

- [ ] **Step 5: Run Python tests and confirm failure**

```bash
python -m unittest discover -s tests -v
```

- [ ] **Step 6: Implement Python parity using standard library only**

Port the same renderer, JSONC scanner/patcher, platform-aware manifest logic, config transaction ordering, and auto-detection. `download_source` continues downloading only the repository `agents` directory because rendering code lives in `install.py`.

- [ ] **Step 7: Run Python tests**

```bash
python -m unittest discover -s tests -v
```

Expected: all Python tests pass.

- [ ] **Step 8: Commit**

```bash
git add tests/test_install_agents.py install.py
git commit -m "feat: support OpenCode in Python installer"
```

---

### Task 6: Make browser instructions runtime-neutral and validate generated agents

**Files:**
- Modify: `agents/browser-agent.agent.md`
- Modify: `scripts/validate_agents.py`
- Modify: `tests/test_validate_agents.py`

**Interfaces:**
- Source frontmatter remains Copilot-compatible.
- Browser body may refer to "browser automation tools" and Playwright MCP capability but must not require VS Code-only tool names to understand the workflow.
- Validator gains an OpenCode render validation path or reusable checks that ensure all source agents can be rendered.

- [ ] **Step 1: Add failing validator tests for OpenCode renderability**

Require every source agent to have a supported source tool mapping and require only `browser-agent` to declare the VS Code browser tool set that maps to the Playwright MCP capability.

- [ ] **Step 2: Rewrite browser-agent body without changing its source tool frontmatter**

Keep the workflow semantics: open/navigate, read state, interact, screenshot evidence, run advanced browser code only when basic actions are insufficient, and never use a personal authenticated profile. Mention that runtime-specific tool names are supplied by the host platform.

- [ ] **Step 3: Run validator tests and agent validation**

```bash
python -m unittest tests.test_validate_agents -v
python scripts/validate_agents.py
```

Expected: pass and prompt budgets remain under current limits.

- [ ] **Step 4: Commit**

```bash
git add agents/browser-agent.agent.md scripts/validate_agents.py tests/test_validate_agents.py
git commit -m "refactor: make browser agent runtime neutral"
```

---

### Task 7: Document OpenCode installation and verify the full release gate

**Files:**
- Modify: `README.md`
- Modify: `package.json` only if package metadata needs OpenCode keywords/description

**Interfaces:**
- README documents auto mode and explicit `--platform` commands.
- README documents OpenCode target paths and the managed `doct_playwright` MCP entry.
- README states that Playwright MCP runs isolated and that existing OpenCode config is preserved.

- [ ] **Step 1: Update README usage tables and examples**

Include:

```bash
npx doct-agents@latest install --platform opencode --scope user
npx doct-agents@latest install --platform all --scope workspace
npx doct-agents@latest status --platform opencode --scope user
npx doct-agents@latest uninstall --platform opencode --scope user
```

Explain that install/update without `--platform` always include Copilot and additionally include detected OpenCode, while status/uninstall without `--platform` remain Copilot-only for backward compatibility.

- [ ] **Step 2: Run the complete project gate**

```bash
npm run check
```

Expected: Node tests, Python tests, agent validation, npm pack dry-run, and package smoke all pass.

- [ ] **Step 3: Inspect package contents**

```bash
npm pack --dry-run
```

Expected: package includes `agents`, `bin`, README, and installer-required runtime code; no generated OpenCode agent tree is packaged.

- [ ] **Step 4: Commit**

```bash
git add README.md package.json
git commit -m "docs: document OpenCode support"
```

---

### Task 8: Final compatibility review

**Files:**
- Review only unless fixes are required.

**Interfaces:**
- No new API beyond documented CLI/platform/render helper contracts.

- [ ] **Step 1: Compare branch against main**

Review for accidental prompt duplication, config overwrite behavior, permission expansion, and changed legacy CLI semantics.

- [ ] **Step 2: Verify security invariants**

Confirm:

```text
orchestrator: task allowlist only
implementation-agent: edit yes, bash no
cli-executor: bash yes, edit no
workers: task deny
browser-agent: doct_playwright_* allow
all other agents: doct_playwright_* deny
```

- [ ] **Step 3: Re-run full verification after any review fix**

```bash
npm run check
```

Expected: exit 0.

- [ ] **Step 4: Record final evidence in the PR description**

Include exact commands, pass/fail result, browser MCP version, config compatibility notes, and any unverified OpenCode runtime behavior.

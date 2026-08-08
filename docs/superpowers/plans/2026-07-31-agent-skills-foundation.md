# Agent Skills Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Productize workflow, language, and framework Agent Skills so `doct-agents` can validate, package, install, update, inspect, and uninstall them safely alongside existing custom agents.

**Architecture:** Keep the runtime directories flat under `skills/<skill-name>/`, with taxonomy stored in `skills/catalog.json`. Generalize both installers around component specifications so agents remain flat files while skills are recursive file trees; keep one manifest per target root and coordinate selected components as one rollback-capable operation. Preserve schema-1 agent manifests on read and write schema 2 after a successful update.

**Tech Stack:** Node.js 18+ ESM, Python 3.9+ standard library, Node test runner, Python unittest, VS Code custom agents, Agent Skills `SKILL.md` format.

## Global Constraints

- Do not add runtime dependencies.
- Node.js minimum remains 18.
- Python minimum remains 3.9.
- Preserve current agent routing and least-privilege guardrails.
- Preserve `--target` as the legacy alias for the agent target.
- Reject symlinks, junctions, path traversal, case-insensitive collisions, and unmanaged overwrite.
- A failed multi-component update must roll back all committed component changes.
- Runtime skill directories are direct children of `skills/`; taxonomy is metadata, not path nesting.
- `SKILL.md` body limit is 500 lines and 8,000 characters.
- Foundation composition target is one primary workflow, one language, one framework, and an optional risk skill.

---

### Task 1: Define customization and skill validation contracts

**Files:**
- Create: `scripts/validate_customizations.py`
- Modify: `scripts/validate_agents.py`
- Create: `tests/test_validate_skills.py`
- Modify: `tests/test_validate_agents.py`
- Modify: `package.json`

**Interfaces:**
- Consumes: existing agent frontmatter parser and agent guardrails.
- Produces: `validate_repository(root: Path) -> list[str]`, `validate_agents(directory: Path) -> list[str]`, and `validate_skills(directory: Path) -> list[str]`.

- [ ] **Step 1: Write failing tests for valid skill catalog and skill definitions**

Create fixtures with `skills/catalog.json` and direct child skill directories. Assert that valid workflow/language/framework skills return no errors.

- [ ] **Step 2: Write failing tests for invalid skill structures**

Cover directory/name mismatch, missing `SKILL.md`, invalid kebab-case, missing or overlong description, invalid activation mapping, duplicate catalog entry, uncatalogued directory, escaping Markdown link, case-insensitive path collision, body line budget, and body character budget.

- [ ] **Step 3: Run validator tests and confirm RED**

Run:

```bash
python -m unittest tests.test_validate_skills -v
```

Expected: failure because `validate_customizations.py` does not exist.

- [ ] **Step 4: Implement generic frontmatter parsing and skill validation**

Keep the parser dependency-free. Parse scalar booleans, quoted strings, inline lists, and folded/literal description blocks needed by shipped skills. Validate catalog schema 1 and enum values `workflow|language|framework|risk`, `auto|manual|auto-and-user`, and composition groups.

- [ ] **Step 5: Turn `validate_agents.py` into a compatibility wrapper**

Keep current CLI behavior while importing and delegating agent validation from `validate_customizations.py`.

- [ ] **Step 6: Add the new validator to package checks**

Change `npm run validate` to execute `python scripts/validate_customizations.py` while preserving direct compatibility with `python scripts/validate_agents.py`.

- [ ] **Step 7: Run validation tests and full current tests**

Run:

```bash
python -m unittest tests.test_validate_skills tests.test_validate_agents -v
npm test
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/validate_customizations.py scripts/validate_agents.py tests/test_validate_skills.py tests/test_validate_agents.py package.json
git commit -m "feat: validate agent skills"
```

### Task 2: Add generic manifest and managed-path support in the Node installer

**Files:**
- Modify: `bin/doct-agents.js`
- Modify: `tests/test_cli.mjs`

**Interfaces:**
- Produces: `defaultTargets(scope, workspace, home)`, `discoverComponentFiles(spec)`, `installCustomizations(options)`, `getCustomizationStatus(options)`, and `uninstallCustomizations(options)`.
- Preserves: `installAgents`, `getStatus`, `uninstallAgents`, and `defaultTarget` as compatibility APIs.

- [ ] **Step 1: Write failing Node tests for schema-2 nested skill paths**

Assert manifest paths use `/`, nested skill files install correctly, catalog is not installed, schema 1 agent manifests load as component `agents`, and schema 1 is rejected for skills.

- [ ] **Step 2: Write failing Node tests for path safety**

Cover `..`, absolute paths, drive prefixes, empty segments, backslashes, symlinked source/destination components, and case-insensitive collisions.

- [ ] **Step 3: Write failing tests for default targets and component selection**

Assert user/workspace agent and skill targets and `all|agents|skills` selection. Assert `--target` plus `--agents-target` is rejected.

- [ ] **Step 4: Run Node tests and confirm RED**

Run:

```bash
node --test tests/test_cli.mjs
```

Expected: failures for missing multi-component APIs.

- [ ] **Step 5: Implement component specifications and schema normalization**

Define component specs for agents and skills. Agents discover direct `*.agent.md` files; skills discover files recursively under direct child directories that contain `SKILL.md`, excluding `catalog.json`.

- [ ] **Step 6: Implement nested managed-path safety**

Normalize manifest paths to POSIX separators, verify every existing path component with `lstat`, reject link-like entries, and create only required real directories.

- [ ] **Step 7: Implement multi-component staging and rollback journal**

Calculate conflicts for all selected components before mutation. Stage every file and manifest, then commit through one journal; on failure restore replaced/removed files across every selected component.

- [ ] **Step 8: Keep compatibility wrappers green**

Map old single-agent APIs onto the new generic installer so existing callers and tests remain valid.

- [ ] **Step 9: Run Node tests**

Run:

```bash
node --test tests/test_cli.mjs
```

Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add bin/doct-agents.js tests/test_cli.mjs
git commit -m "feat: install agent skills with node cli"
```

### Task 3: Bring the Python installer to feature parity

**Files:**
- Modify: `install.py`
- Modify: `tests/test_install_agents.py`

**Interfaces:**
- Mirrors Node component specs, schema normalization, path validation, component selection, status grouping, transaction and compatibility wrappers.

- [ ] **Step 1: Write failing Python tests matching Node behavior**

Cover nested skill install, schema migration, selected components, target aliases, path collisions, source links, update conflicts, obsolete skill resources, and rollback across agent/skill roots.

- [ ] **Step 2: Run Python tests and confirm RED**

Run:

```bash
python -m unittest tests.test_install_agents -v
```

Expected: failures for missing skill and multi-component behavior.

- [ ] **Step 3: Implement generic component and manifest helpers**

Use `NamedTuple`/plain dictionaries compatible with Python 3.9. Store manifest paths with `PurePosixPath` semantics and map to local `Path` only after validation.

- [ ] **Step 4: Implement recursive skill discovery and link rejection**

Walk direct child skill directories without following links. Require regular `SKILL.md` and reject any symbolic link or reparse point in the source tree.

- [ ] **Step 5: Implement coordinated staging and rollback**

Stage adjacent to each target parent, keep one package-level rollback journal, remove only empty managed directories, and preserve backup paths when rollback itself fails.

- [ ] **Step 6: Preserve public compatibility functions**

Keep `install_agents`, `get_status`, `uninstall_agents`, and `default_target` working for external callers.

- [ ] **Step 7: Run Python tests**

Run:

```bash
python -m unittest tests.test_install_agents -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add install.py tests/test_install_agents.py
git commit -m "feat: install agent skills with python cli"
```

### Task 4: Add foundation workflow, language, and framework skills

**Files:**
- Create: `skills/catalog.json`
- Create: `skills/repository-discovery/SKILL.md`
- Create: `skills/code-review/SKILL.md`
- Create: `skills/implementation-workflow/SKILL.md`
- Create: `skills/verification-before-completion/SKILL.md`
- Create: `skills/java/SKILL.md`
- Create: `skills/java/references/concurrency.md`
- Create: `skills/spring-boot/SKILL.md`
- Create: `skills/spring-boot/references/transactions.md`

**Interfaces:**
- `repository-discovery`, `code-review`, `implementation-workflow`, and `verification-before-completion` are workflow skills.
- `java` is a language skill.
- `spring-boot` is a framework skill and requires Java evidence in its activation boundary.

- [ ] **Step 1: Add catalog entries with non-overlapping composition groups**

Use `primary-workflow` for review/implementation, `supporting-workflow` for discovery/verification, `language` for Java, and `framework` for Spring Boot.

- [ ] **Step 2: Author activation descriptions with negative boundaries**

Each description must state when to use the skill and when not to use it. Do not duplicate agent persona, permission, routing, or result contracts.

- [ ] **Step 3: Author compact procedural bodies**

Keep `SKILL.md` focused on procedure. Put Java concurrency and Spring transaction details in references and link to them from the body.

- [ ] **Step 4: Validate shipped skills**

Run:

```bash
python scripts/validate_customizations.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills
git commit -m "feat: add foundation agent skills"
```

### Task 5: Integrate skill routing policy into agents without duplicating workflows

**Files:**
- Modify: `agents/orchestrator.agent.md`
- Modify: `agents/review-agent.agent.md`
- Modify: `agents/implementation-agent.agent.md`
- Modify: `agents/cli-executor.agent.md`
- Modify: `agents/agent-authoring.agent.md`
- Modify: `tests/test_validate_agents.py`

**Interfaces:**
- Orchestrator owns phase and worker selection.
- Workflow skills define the procedure inside a phase.
- Language/framework skills add focused checks based on task file/dependency evidence.

- [ ] **Step 1: Write failing repository contract tests**

Assert orchestrator includes the one-primary-workflow rule and evidence-based language/framework selection. Assert agent prompts do not contain full copied skill procedures.

- [ ] **Step 2: Add compact skill-composition policy to orchestrator**

Specify one primary workflow, at most one language and one framework, risk only when relevant, and normal FAST_FIX cap of 3–4 active skills.

- [ ] **Step 3: Add worker-specific skill usage boundaries**

Review uses `code-review`; implementation uses `implementation-workflow`; CLI finalization uses `verification-before-completion`; authoring reads skill conventions before creating/updating a skill. Keep these as routing hints, not copied procedures.

- [ ] **Step 4: Run agent/customization validation tests**

Run:

```bash
python -m unittest tests.test_validate_agents tests.test_validate_skills -v
python scripts/validate_customizations.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add agents tests/test_validate_agents.py
git commit -m "refactor: route agent work through skills"
```

### Task 6: Package, smoke-test, document, and release-check the feature

**Files:**
- Modify: `package.json`
- Modify: `scripts/smoke_package.mjs`
- Modify: `README.md`
- Modify: `tests/test_cli.mjs`
- Modify: `tests/test_install_agents.py`

**Interfaces:**
- npm package contains `agents/` and `skills/`.
- Installed package CLI supports all components and reports component-specific status.

- [ ] **Step 1: Add failing package smoke assertions**

Assert the tarball contains `skills/catalog.json`, each foundation `SKILL.md`, nested references, and excludes unrelated docs/test files.

- [ ] **Step 2: Add `skills` to package files and bump minor version**

Set version to `0.3.0` because the CLI gains new behavior while retaining compatibility.

- [ ] **Step 3: Document installation and routing**

Explain default agent/skill targets, component selection, lazy loading, workflow/language/framework composition, manual slash invocation, schema migration, and update conflict behavior.

- [ ] **Step 4: Run complete verification**

Run:

```bash
npm run check
```

Expected: Node tests, Python tests, customization validation, package dry run, and package smoke test all PASS.

- [ ] **Step 5: Inspect package contents**

Run:

```bash
npm pack --dry-run
```

Expected: agents, skills, bin, README, LICENSE, and package metadata only.

- [ ] **Step 6: Commit**

```bash
git add package.json scripts/smoke_package.mjs README.md tests/test_cli.mjs tests/test_install_agents.py
git commit -m "docs: publish and explain agent skills"
```

### Task 7: Final cross-platform review and completion evidence

**Files:**
- Update: `docs/superpowers/plans/2026-07-31-agent-skills-foundation.md`

**Interfaces:**
- Consumes all prior task outputs.
- Produces final checkpoint and remaining-risk record.

- [ ] **Step 1: Review the complete branch diff**

Check manifest migration, path safety, rollback, Node/Python parity, activation overlap, prompt growth, and package contents.

- [ ] **Step 2: Run complete verification on the final revision**

Run:

```bash
npm run check
```

Expected: PASS on the exact final revision.

- [ ] **Step 3: Record completion evidence in this plan**

Add final commit SHA, commands, outcomes, known platform limitations, and remaining risks. Do not mark complete without fresh evidence.

- [ ] **Step 4: Commit checkpoint**

```bash
git add docs/superpowers/plans/2026-07-31-agent-skills-foundation.md
git commit -m "docs: complete agent skills foundation plan"
```

# Installer and Release Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Secure both installers, make upgrades remove obsolete agents safely, standardize worker results, and make release validation equivalent to pull-request validation.

**Architecture:** Add small path/manifest validation helpers to each installer and perform a complete preflight before any target mutation. Keep schema 1 compatible across Node and Python, then centralize repository checks in scripts that both validation and publishing workflows invoke.

**Tech Stack:** Node.js 18+ ESM, Python 3.9+ standard library, Node test runner, Python unittest, GitHub Actions.

## Global Constraints

- Keep `todo` as the orchestrator tool name.
- Add no third-party runtime dependency.
- Never let `--force` bypass path or symlink safety.
- Preserve locally modified files unless explicit force applies to a checksum conflict.
- Maintain compatibility with existing schema-1 manifests from both installers.
- Use status values only from `completed | needs-info | blocked | failed`.

---

### Task 1: Define installer security and obsolete-file behavior with tests

**Files:**
- Modify: `tests/test_cli.mjs`
- Modify: `tests/test_install_agents.py`

**Interfaces:**
- Consumes: existing `installAgents`, `getStatus`, `uninstallAgents`, `install_agents`, `get_status`, and `uninstall_agents` APIs.
- Produces: executable specifications for manifest validation, symlink rejection, compatibility, and obsolete-file cleanup.

- [ ] Add Node tests that reject `../outside.agent.md`, absolute paths, invalid checksums, unsupported schemas, and symlink destinations.
- [ ] Add Node tests showing unchanged obsolete agents are removed and modified obsolete agents are preserved and retained in the manifest.
- [ ] Add Python equivalents for every Node security and lifecycle test.
- [ ] Add compatibility tests showing each installer accepts schema-1 manifests containing only `package` or only `repository`.
- [ ] Push tests before production changes and verify CI fails for the expected missing protections.

### Task 2: Harden the Node installer

**Files:**
- Modify: `bin/doct-agents.js`

**Interfaces:**
- Produces: `validateManagedFilename(filename)`, safe destination resolution, strict manifest parsing, symlink rejection, and obsolete-file preflight/removal.

- [ ] Validate manifest root fields, schema, identifiers, filenames, and SHA-256 values in `loadManifest`.
- [ ] Reject symbolic links before hash, overwrite, or unlink operations.
- [ ] Compute conflicts and obsolete actions before copying any bundled file.
- [ ] Delete unchanged obsolete files; preserve modified obsolete files in the new manifest.
- [ ] Write the canonical schema-1 manifest with both `package` and `repository`.
- [ ] Run Node tests and confirm they pass.

### Task 3: Harden the Python installer and archive extraction

**Files:**
- Modify: `install.py`

**Interfaces:**
- Produces: Python equivalents of Node path/manifest behavior plus `safe_extract_archive`.

- [ ] Implement strict manifest and managed-filename validation compatible with older schema-1 manifests.
- [ ] Reject symbolic links before hash, overwrite, or unlink operations.
- [ ] Preflight and process obsolete managed files with the same semantics as Node.
- [ ] Validate every ZIP member for containment and symlink metadata before extraction.
- [ ] Write the canonical schema-1 manifest with both identifiers.
- [ ] Run Python tests and confirm they pass.

### Task 4: Standardize agent result statuses

**Files:**
- Modify: `agents/test-agent.agent.md`
- Modify: `agents/browser-agent.agent.md`
- Modify: `agents/security-agent.agent.md`
- Modify: `agents/research-agent.agent.md`
- Modify: `agents/refactor-agent.agent.md`
- Modify: `scripts/validate_agents.py`
- Modify: `tests/test_validate_agents.py`

**Interfaces:**
- Produces: repository-wide status contract validated from agent body text.

- [ ] Add failing validator tests for custom status values such as `done` and `needs-fix`.
- [ ] Extend validator to reject output status vocabularies outside the common enum when an agent declares a status contract.
- [ ] Update affected workers to use the common status values and structured `Next` handoffs.
- [ ] Run validator tests and repository validation.

### Task 5: Centralize checks and add packaged CLI smoke coverage

**Files:**
- Create: `scripts/check_release.py`
- Create: `scripts/smoke_package.mjs`
- Modify: `package.json`
- Modify: `.github/workflows/validate-agents.yml`
- Modify: `.github/workflows/publish-npm.yml`

**Interfaces:**
- Produces: `npm run check`, `npm run smoke:package`, and `python scripts/check_release.py [tag]` used by both workflows.

- [ ] Create a tarball smoke script that runs `npm pack`, installs the tarball into a temporary project, and executes install/status/uninstall through the packaged binary.
- [ ] Add a release checker that compares a supplied `vX.Y.Z` tag with `package.json.version` and treats no tag as a manual-dispatch validation.
- [ ] Update `package.json` scripts so one command runs Node tests, Python tests, agent validation, package dry-run, and smoke testing.
- [ ] Add Ubuntu minimum/current and Windows compatibility jobs using an explicit include matrix.
- [ ] Make publish call the same check and run tag/version validation before `npm publish`.

### Task 6: Update documentation and version

**Files:**
- Modify: `README.md`
- Modify: `package.json`

**Interfaces:**
- Produces: documented obsolete-file behavior, safety guarantees, CI commands, and patch release metadata.

- [ ] Document safe update behavior for removed upstream agents.
- [ ] Document that unsafe manifests/symlinks abort even with `--force`.
- [ ] Document the unified validation command.
- [ ] Bump the package patch version.

### Task 7: Final verification and review

**Files:**
- Review all changed files.

**Interfaces:**
- Consumes: all deliverables from Tasks 1-6.
- Produces: a merge-ready pull request with CI evidence.

- [ ] Run or obtain CI evidence for Node tests, Python tests, agent validation, package dry-run, packaged CLI smoke, Windows lane, and release-tag check.
- [ ] Review the diff for path containment, symlink handling, partial-write risk, Node/Python parity, and workflow permission scope.
- [ ] Fix every critical/high issue found and re-run validation.
- [ ] Open a pull request with behavior, security, compatibility, and validation summaries.

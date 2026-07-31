# Installer and Release Hardening Implementation Plan

> **Status:** Completed
>
> **Pull request:** #5 — `fix/harden-installer-release`
>
> **Final validation:** GitHub Actions run `30515516557`

**Goal:** Secure both installers, make upgrades remove obsolete agents safely, standardize worker results, and make release validation equivalent to pull-request validation.

**Architecture:** Validate every target-path component, managed filename, manifest field, checksum, and archive member before mutation. Stage all replacement files and the next manifest on the target filesystem, commit with rename operations, and restore backups in reverse order if commit fails. Keep schema 1 compatible across Node and Python, then centralize repository checks in scripts used by both validation and publishing workflows.

**Tech Stack:** Node.js 18+ ESM, Python 3.9+ standard library, Node test runner, Python unittest, GitHub Actions.

## Global Constraints

- Keep `todo` as the orchestrator tool name.
- Add no third-party runtime dependency.
- Never let `--force` bypass path, symlink, junction, or reparse-point safety.
- Preserve locally modified files unless explicit force applies to a checksum conflict.
- Maintain compatibility with existing schema-1 manifests from both installers.
- Use worker result status values only from `completed | needs-info | blocked | failed`.

---

### Task 1: Define installer security and obsolete-file behavior with tests

**Files:**
- Modify: `tests/test_cli.mjs`
- Modify: `tests/test_install_agents.py`

**Interfaces:**
- Consumes: existing `installAgents`, `getStatus`, `uninstallAgents`, `install_agents`, `get_status`, and `uninstall_agents` APIs.
- Produces: executable specifications for manifest validation, linked-path rejection, compatibility, transactional updates, and obsolete-file cleanup.

- [x] Add Node tests that reject `../outside.agent.md`, absolute paths, invalid checksums, unsupported schemas, symlink destinations, and linked target ancestors.
- [x] Add Node tests showing unchanged obsolete agents are removed and modified obsolete agents are preserved and retained in the manifest.
- [x] Add Node regression coverage showing source staging failure does not mutate installed files or the manifest.
- [x] Add Python equivalents for Node security, lifecycle, and staging behavior.
- [x] Add compatibility tests showing each installer accepts schema-1 manifests containing only `package` or only `repository`.
- [x] Push tests before production changes and verify CI fails for the expected missing protections.

**Evidence:** Initial regression run `30514596751` failed on linked ancestors and mutation-before-staging before the production fixes were applied.

### Task 2: Harden the Node installer

**Files:**
- Modify: `bin/doct-agents.js`

**Interfaces:**
- Produces: `validateManagedFilename(filename)`, safe target-component validation, strict manifest parsing, linked-path rejection, transactional staging/rollback, and obsolete-file processing.

- [x] Validate manifest root fields, schema, identifiers, filenames, and SHA-256 values in `loadManifest`.
- [x] Reject symbolic links, junctions, and reparse-point ancestors before hash, overwrite, rename, or unlink operations.
- [x] Compute conflicts and obsolete actions before copying any bundled file.
- [x] Stage all bundled files and the next manifest before target mutation.
- [x] Commit through same-filesystem renames and roll back previous files when a later commit operation fails.
- [x] Delete unchanged obsolete files; preserve modified obsolete files in the new manifest.
- [x] Write the canonical schema-1 manifest with both `package` and `repository`.
- [x] Run Node tests and confirm they pass.

### Task 3: Harden the Python installer and archive extraction

**Files:**
- Modify: `install.py`

**Interfaces:**
- Produces: Python equivalents of Node path, manifest, staging, rollback, and obsolete-file behavior plus `safe_extract_archive`.

- [x] Implement strict manifest and managed-filename validation compatible with older schema-1 manifests.
- [x] Reject symbolic links and linked target ancestors before hash, overwrite, rename, or unlink operations.
- [x] Preflight and process obsolete managed files with the same semantics as Node.
- [x] Stage replacement files and manifest before mutation, then restore backups if commit fails.
- [x] Validate every ZIP member for containment and symlink metadata before extraction.
- [x] Write the canonical schema-1 manifest with both identifiers.
- [x] Run Python tests and confirm they pass.

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
- Produces: repository-wide worker status contract validated from agent body text while retaining the explicit documentation-impact status vocabulary.

- [x] Add failing validator tests for custom status values such as `done`, `needs-fix`, `success`, and `retry-later`.
- [x] Extend validator to reject worker output status vocabularies outside the common enum.
- [x] Allow only the separately declared documentation-impact vocabulary `required | not-required | uncertain` outside the worker enum.
- [x] Update affected workers to use the common status values and structured `Next` handoffs.
- [x] Run validator tests and repository validation.

### Task 5: Centralize checks and add packaged CLI smoke coverage

**Files:**
- Create: `scripts/check_release.py`
- Create: `scripts/smoke_package.mjs`
- Create: `bin/cli.js`
- Modify: `package.json`
- Modify: `.github/workflows/validate-agents.yml`
- Modify: `.github/workflows/publish-npm.yml`

**Interfaces:**
- Produces: `npm run check`, `npm run smoke:package`, and `python scripts/check_release.py [tag]` used by validation and publishing workflows.

- [x] Create a tarball smoke script that runs `npm pack`, installs the tarball into a temporary project, and executes install/status/uninstall through the packaged binary.
- [x] Add a dedicated npm executable entrypoint that works through npm's generated command shim.
- [x] Add a release checker that requires a `vX.Y.Z` tag and compares it with `package.json.version`.
- [x] Require manual dispatch to provide an explicit tag and checkout that tag before validation and publishing.
- [x] Update `package.json` scripts so one command runs Node tests, Python tests, agent validation, package dry-run, and smoke testing.
- [x] Add Ubuntu minimum/current and Windows compatibility jobs using an explicit include matrix.
- [x] Make publish call the same complete check and run tag/version validation before `npm publish`.

### Task 6: Update documentation and version

**Files:**
- Modify: `README.md`
- Modify: `package.json`
- Modify: `docs/superpowers/specs/2026-07-30-installer-release-hardening-design.md`

**Interfaces:**
- Produces: documented obsolete-file behavior, transactional update behavior, safety guarantees, release rules, CI commands, and patch release metadata.

- [x] Document safe update behavior for removed upstream agents.
- [x] Document transactional staging, rollback, and retained backup behavior.
- [x] Document that unsafe manifests and linked target paths abort even with `--force`.
- [x] Document explicit-tag manual publishing and the unified validation command.
- [x] Correct the documented npm executable entrypoint.
- [x] Bump the package patch version to `0.2.1`.

### Task 7: Final verification and review

**Files:**
- Review all changed files.

**Interfaces:**
- Consumes: all deliverables from Tasks 1–6.
- Produces: a merge-ready pull request with CI evidence.

- [x] Obtain CI evidence for Node tests, Python tests, agent validation, release metadata tests, package dry-run, packaged CLI smoke, and the Windows lane.
- [x] Review the diff for path containment, linked-path handling, partial-write risk, Node/Python parity, workflow permission scope, and release-ref selection.
- [x] Fix every critical/high issue found and re-run validation.
- [x] Open a pull request with behavior, security, compatibility, and validation summaries.

## Completion Evidence

- Pull request: `https://github.com/OneTwoTen/doct-agents/pull/5`
- Final verified head before this documentation-only update: `341a09d66b2d970ab3373762910cc2f19859d085`
- GitHub Actions run `30515516557` completed successfully on:
  - Ubuntu minimum: Node.js 18 and Python 3.9
  - Ubuntu current: Node.js 24 and Python 3.13
  - Windows current: Node.js 24 and Python 3.13, including the junction-ancestor regression test
- Each lane ran `npm run check`, covering Node tests, Python tests, agent validation, `npm pack --dry-run`, and the installed-tarball CLI smoke test.
- Release tests cover matching tags, mismatched tags, missing tags, required manual-dispatch input, and checkout of the selected release tag.

## Remaining Work

- None within this implementation plan.
- Publishing `v0.2.1` and merging PR #5 are release/maintainer actions outside the implementation checklist.

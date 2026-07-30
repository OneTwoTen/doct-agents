# Installer and Release Hardening Design

## Goal

Harden the Node and Python installation paths without changing the public CLI, preserve user modifications during upgrades, and ensure every published npm release passes the same validation as pull requests.

## Scope

- Keep the existing commands and flags: `install`, `update`, `status`, `uninstall`, `--scope`, `--workspace`, `--target`, and `--force`.
- Keep `todo` as the orchestrator tool name.
- Protect manifest-driven file operations from path traversal, absolute paths, unexpected extensions, symbolic links, and Windows junction/reparse-point ancestors.
- Remove obsolete managed agents during update only when their installed checksum is unchanged; preserve locally modified obsolete files.
- Make Node and Python manifests use one compatible schema while continuing to read schema-1 manifests produced by either installer.
- Safely extract the Python-downloaded GitHub archive.
- Standardize worker status values on `completed | needs-info | blocked | failed`.
- Run package, Node, Python, repository-agent, and packaged-CLI checks before publishing.
- Require an explicit release tag and verify it matches `package.json.version`.

## Non-goals

- Changing VS Code agent behavior beyond result-contract consistency.
- Adding third-party runtime dependencies.
- Replacing the Node or Python installer.
- Automatically deleting unmanaged files.
- Automatically overwriting locally modified files.

## Installer design

Both installers validate every manifest filename before resolving a destination. A valid managed filename is a basename ending in `.agent.md`, with no slash, backslash, `.`/`..` segment, null byte, or absolute-path semantics. The resolved destination must remain directly under the selected target directory.

Before reading, copying, hashing, or deleting a managed destination, each installer rejects symbolic links. Every existing component of the target path is checked before directory creation and again before commit. Python additionally treats Windows reparse points as link-like so directory junctions cannot redirect writes outside the selected target. `--force` may bypass checksum conflicts but never bypass path containment or link checks.

The canonical manifest remains schema 1 for compatibility and contains both identifiers:

```json
{
  "schema": 1,
  "package": "doct-agents",
  "repository": "OneTwoTen/doct-agents",
  "files": {
    "orchestrator.agent.md": "<sha256>"
  }
}
```

Readers accept older manifests containing only `package` or only `repository`, but reject unsupported schemas, invalid identifiers, invalid filenames, and non-SHA-256 checksum values.

## Update lifecycle

For an update, each installer computes `previous managed files - bundled files`.

- Missing obsolete file: remove it from the new manifest.
- Unchanged obsolete file: delete it and remove it from the new manifest.
- Modified obsolete file: preserve it and keep its previous checksum in the new manifest so `status` and a later `uninstall` still report/manage it.
- Symlink or unsafe obsolete path: abort without deleting anything.

Conflict and obsolete analysis happens before writes. The installer then copies every bundled agent and the next manifest into a sibling staging directory on the same filesystem as the target. A staging failure leaves the target untouched.

During commit, existing managed files and the previous manifest are moved into a sibling backup directory before staged files are atomically renamed into the target. Unchanged obsolete files are moved into the same backup. If any commit operation fails, completed operations are rolled back in reverse order. When rollback also fails, the backup is preserved and its path is included in the error instead of being silently removed.

## Python archive extraction

Every ZIP member is validated before extraction. Absolute paths, paths escaping the extraction root, and symlink entries are rejected. Only after all members pass validation is the archive extracted.

## Agent result contract

Workers use only these status values:

```text
completed | needs-info | blocked | failed
```

A discovered production defect is represented as `Status: completed` with `Next: handoff` to `implementation-agent`, rather than a custom `needs-fix` status. Existing domain-specific status vocabularies such as documentation impact are not interpreted as worker result statuses.

## CI and release

The validation workflow covers:

- minimum supported runtimes on Ubuntu;
- current runtimes on Ubuntu;
- a Windows compatibility lane;
- Node unit tests;
- Python unit tests;
- repository agent validation;
- `npm pack --dry-run`;
- an installed-tarball CLI smoke test.

The publish workflow runs the same comprehensive check. A GitHub Release uses its release tag. Manual dispatch requires an explicit tag input. In both cases the workflow checks out that exact tag, verifies it is exactly `v${package.json.version}`, and only then publishes. A branch head cannot be published through manual dispatch without an existing matching tag.

## Acceptance criteria

1. Malicious manifest paths, linked target ancestors, and linked managed files cannot redirect reads, writes, or deletes outside the selected target.
2. Locally modified managed files remain protected during install, update, and uninstall.
3. Removed upstream agents do not remain active when unchanged, while modified obsolete agents remain visible in status.
4. Update staging failures leave the target untouched; commit failures roll back or preserve a recoverable backup with an explicit path.
5. Old Node- and Python-generated schema-1 manifests remain readable.
6. Unsafe ZIP archives are rejected before extraction.
7. Worker result status declarations use the common vocabulary without rejecting unrelated domain-specific status fields.
8. Pull-request and publish workflows run equivalent validation, and an explicit release tag/version mismatch fails before publish.
9. Node 18+, Python 3.9+, Windows, and the packaged executable are covered by CI.

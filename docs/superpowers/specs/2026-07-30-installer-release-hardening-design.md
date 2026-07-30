# Installer and Release Hardening Design

## Goal

Harden the Node and Python installation paths without changing the public CLI, preserve user modifications during upgrades, and ensure every published npm release passes the same validation as pull requests.

## Scope

- Keep the existing commands and flags: `install`, `update`, `status`, `uninstall`, `--scope`, `--workspace`, `--target`, and `--force`.
- Keep `todo` as the orchestrator tool name.
- Protect manifest-driven file operations from path traversal, absolute paths, unexpected extensions, and symbolic links.
- Remove obsolete managed agents during update only when their installed checksum is unchanged; preserve locally modified obsolete files.
- Make Node and Python manifests use one compatible schema while continuing to read schema-1 manifests produced by either installer.
- Safely extract the Python-downloaded GitHub archive.
- Standardize worker status values on `completed | needs-info | blocked | failed`.
- Run package, Node, Python, repository-agent, and packaged-CLI checks before publishing.
- Verify the release tag matches `package.json.version`.

## Non-goals

- Changing VS Code agent behavior beyond result-contract consistency.
- Adding third-party runtime dependencies.
- Replacing the Node or Python installer.
- Automatically deleting unmanaged files.
- Automatically overwriting locally modified files.

## Installer design

Both installers validate every manifest filename before resolving a destination. A valid managed filename is a basename ending in `.agent.md`, with no slash, backslash, `.`/`..` segment, null byte, or absolute-path semantics. The resolved destination must remain directly under the selected target directory.

Before reading, copying, hashing, or deleting a managed destination, the installer rejects symbolic links. `--force` may bypass checksum conflicts but never bypass path containment or symlink checks.

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

Conflict and obsolete analysis happens before writes so a failed update does not partially modify the target.

## Python archive extraction

Every ZIP member is validated before extraction. Absolute paths, paths escaping the extraction root, and symlink entries are rejected. Only after all members pass validation is the archive extracted.

## Agent result contract

Workers use only these status values:

```text
completed | needs-info | blocked | failed
```

A discovered production defect is represented as `Status: completed` with `Next: handoff` to `implementation-agent`, rather than a custom `needs-fix` status. Existing domain-specific evidence fields remain unchanged.

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

The publish workflow runs the same comprehensive check, verifies that a release tag is exactly `v${package.json.version}`, then publishes. Manual dispatch may publish the current package version after all checks pass.

## Acceptance criteria

1. Malicious manifest paths and symlink targets cannot be read, overwritten, or deleted by either installer.
2. Locally modified managed files remain protected during install, update, and uninstall.
3. Removed upstream agents do not remain active when unchanged, while modified obsolete agents remain visible in status.
4. Old Node- and Python-generated schema-1 manifests remain readable.
5. Unsafe ZIP archives are rejected before extraction.
6. All worker files use the common status vocabulary.
7. Pull-request and publish workflows run equivalent validation, and release tag/version mismatch fails before publish.
8. Node 18+, Python 3.9+, Windows, and the packaged executable are covered by CI.

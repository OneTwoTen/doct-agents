# Doct Spec Workspace Progress

Spec: `.doct/specs/doct-spec-workspace/`
Status: completed

## Completed milestones

- M1 — Repository contract test added.
- M2 — `planning-agent` moved to executor-neutral `.doct/specs/<feature>/` ownership.
- M3 — LONG_RUNNING gained requirements/design review gates, executor selection and feature impact lifecycle.
- M4 — `docs-agent` gained separate `feature-update` mode.
- M5 — `.doct/project.md`, feature catalog/current-state record and README guidance added.
- M6 — Repository CI validation passed on all configured runtime lanes.

## Current milestone

None.

## Blocked items

None.

## Validation evidence

GitHub Actions run `30891155471`, workflow `Validate agents`:

- `Validate (ubuntu-current)`: PASS.
- `Validate (ubuntu-minimum)`: PASS.
- `Validate (windows-current)`: PASS.
- Each lane completed `npm run check`, which owns the repository Node tests, Python tests, agent validator, package dry-run and smoke validation configured by the repository.

## Architecture decisions

- Canonical LONG_RUNNING state belongs to `.doct/`, not Superpowers.
- Requirements, design, work plan and runtime progress are separate artifacts.
- Feature registry is current-state project memory; specs are change history.
- Executor mechanics are below the doct-agents orchestration boundary.
- Documentation impact and feature impact are independent lifecycle gates.

## Docs impact

Completed: README LONG_RUNNING workflow, resume instructions, executor boundary and repository structure now use `.doct/` as canonical state.

## Feature impact

Added:
- Executor-neutral spec workspace.
- Feature registry and project capability catalog.

Changed:
- LONG_RUNNING planning/checkpoint lifecycle.
- Docs agent supports feature-registry synthesis separately from public docs impact.

Removed:
- New LONG_RUNNING work no longer uses `docs/superpowers/plans/...` as canonical state. Historical files remain unchanged.

## Remaining risks

- Feature registry is Markdown-only; there is no machine-readable manifest yet.
- Executor adapters beyond the currently available agent environment require their own implementation/validation specs.

## Next

None for this spec. Future executor integrations should create a new `.doct/specs/<feature>/` and update existing feature records only after validation.

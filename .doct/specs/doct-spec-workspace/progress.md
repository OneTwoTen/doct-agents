# Doct Spec Workspace Progress

Spec: `.doct/specs/doct-spec-workspace/`
Status: implementing

## Completed milestones

- M1 — Repository contract test added and reconciled to `tests/test_spec_workspace_contract.py`.
- M2 — `planning-agent` moved to executor-neutral `.doct/specs/<feature>/` ownership.
- M3 — LONG_RUNNING gained requirements/design review gates, executor selection, feature impact lifecycle and final reconciliation contract.
- M4 — `docs-agent` gained separate `feature-update` mode.
- M5 — `.doct/project.md`, feature catalog/current-state record and README guidance added; project view no longer duplicates current capability list.

## Current milestone

M6 — Final verification and reconciliation.

## Blocked items

None.

## Validation evidence

Previous evidence: GitHub Actions run `30891444582` passed all configured lanes before the review-fix changes.

Current validation revision candidate: `f1e6fd9641d1ad48e31e5a7ad6078b47247623a2`, containing the latest orchestrator + regression-test changes. Fresh CI evidence for this validation revision is not recorded yet, so this spec remains `implementing` and related new capabilities remain `experimental` until validation completes.

Metadata-only reconciliation commits after the validation revision do not require rerunning the same command unless they change code, test, config, environment contract, requirements/design behavior or validation criteria.

## Architecture decisions

- Canonical LONG_RUNNING state belongs to `.doct/`, not Superpowers.
- Requirements, design, work plan and runtime progress are separate artifacts.
- Feature registry is current-state project memory; specs are change history.
- Executor mechanics are below the doct-agents orchestration boundary.
- Documentation impact and feature impact are independent lifecycle gates.
- Before FINALIZE, requirements/design/tasks/progress/feature registry must be reconciled with actual implementation and validation evidence.
- Validation freshness is tied to the latest relevant validation revision, not metadata-only evidence commits, to avoid a self-referential CI loop.

## Docs impact

Completed: README LONG_RUNNING workflow, resume instructions, executor boundary and repository structure use `.doct/` as canonical state.

## Feature impact

Added candidates:
- Executor-neutral spec workspace.
- Feature registry and project capability catalog.

Changed candidates:
- LONG_RUNNING planning/checkpoint lifecycle.
- Final reconciliation and validation-revision semantics.
- Docs agent supports feature-registry synthesis separately from public docs impact.

Removed:
- New LONG_RUNNING work no longer uses `docs/superpowers/plans/...` as canonical state. Historical files remain unchanged.

## Remaining risks

- Final CI evidence for the current validation revision is not recorded yet.
- Feature registry is Markdown-only; there is no machine-readable manifest yet.
- Executor adapters beyond the currently available agent environment require their own implementation/validation specs.

## Next

Record fresh final validation evidence for the current validation revision; then mark M6/spec completed and promote the new LONG_RUNNING/spec-workspace/feature-registry capabilities from `experimental` to `stable`.

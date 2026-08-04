# Doct Spec Workspace Progress

Spec: `.doct/specs/doct-spec-workspace/`
Status: implementing

## Completed milestones

- Spec requirements approved.
- Spec design approved.
- Implementation tasks defined.

## Current milestone

M1 — Lock repository contract.

## Blocked items

None.

## Validation evidence

No new validation run yet. Repository-supported commands are recorded in `tasks.md`.

## Architecture decisions

- Canonical LONG_RUNNING state belongs to `.doct/`, not Superpowers.
- Requirements, design, work plan and runtime progress are separate artifacts.
- Feature registry is current-state project memory; specs are change history.
- Executor mechanics are below the doct-agents orchestration boundary.

## Docs impact

Required: README LONG_RUNNING guidance changes.

## Feature impact

Added candidates:
- Executor-neutral spec workspace.
- Feature registry and project capability catalog.

Changed candidates:
- LONG_RUNNING planning/checkpoint lifecycle.

## Remaining risks

- Static prompt contracts must remain below validator budgets.
- Historical docs under `docs/superpowers/` remain as history and must not be mistaken for canonical new workflow.

## Next

Add repository contract tests, then refactor agent prompts to satisfy them.

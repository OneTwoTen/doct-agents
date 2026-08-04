# Doct Spec Workspace Progress

Spec: `.doct/specs/doct-spec-workspace/`
Status: implementing

## Completed milestones

- M4 — `docs-agent` gained separate `feature-update` mode.
- M5 — `.doct/project.md`, feature catalog/current-state record and README guidance added; project view no longer duplicates current capability list.

M1-M3 đã có implementation chính nhưng được reopen một phần để bổ sung strict checklist contract; completion authoritative nằm ở checkbox của `tasks.md`, không suy ra từ danh sách prose này.

## Current milestone

M1-M3 checklist contract reconciliation, sau đó M6 final verification.

## Current task

Reconcile strict evidence-backed checklist semantics across planning/orchestration/spec contracts.

## Current checklist item

`M1-T5`, `M2-T4`, `M3-T5`, `M3-T6` đang chờ fresh validation evidence; tiếp theo là `M6-T1`.

## Blocked items

None.

## Deferred items

None.

## Validation evidence

Previous evidence: GitHub Actions run `30891444582` passed all configured lanes trước các review/checklist-contract changes.

Current validation revision phải là revision gần nhất chứa `tests/test_spec_workspace_contract.py`, `agents/planning-agent.agent.md` và `agents/orchestrator.agent.md` strict checklist contract. Fresh CI evidence chưa được ghi, vì vậy các checklist item mới vẫn `- [ ]`, spec giữ `implementing` và capability mới chưa được promote `stable`.

Metadata-only reconciliation commits sau validation revision không yêu cầu rerun cùng command nếu không thay đổi code, test, config, environment contract, requirement/design behavior hoặc validation criteria.

## Architecture decisions

- Canonical LONG_RUNNING state belongs to `.doct/`, not Superpowers.
- Requirements, design, work plan and runtime progress are separate artifacts.
- `tasks.md` checkbox là authoritative execution completion ledger; `progress.md` là runtime/evidence journal và không duplicate checklist.
- Checkbox chỉ được tick qua evidence-backed `CHECKLIST_RECONCILE`; worker `Status: completed` hoặc prose summary không phải completion evidence.
- Item blocked/deferred giữ `- [ ]` với explicit reason; không dùng `[x]` để che work chưa hoàn tất.
- Nếu implementation/evidence mâu thuẫn checkbox, evidence thắng và checkbox phải downgrade về `[ ]`.
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
- Strict evidence-backed task checklist and reconciliation gate.

Changed candidates:
- LONG_RUNNING planning/checkpoint lifecycle.
- Final reconciliation and validation-revision semantics.
- `tasks.md` now owns execution completion while `progress.md` owns state/evidence.
- Docs agent supports feature-registry synthesis separately from public docs impact.

Removed:
- New LONG_RUNNING work no longer uses `docs/superpowers/plans/...` as canonical state. Historical files remain unchanged.

## Remaining risks

- Fresh CI evidence for the strict checklist validation revision is not recorded yet.
- Markdown checklist consistency is enforced by prompt + regression contract, not yet by a structural parser/validator.
- Feature registry is Markdown-only; there is no machine-readable manifest yet.
- Executor adapters beyond the currently available agent environment require their own implementation/validation specs.

## Next

Wait for fresh CI evidence on the strict checklist contract revision. Then run CHECKLIST_RECONCILE: tick only items whose implementation + required validation evidence are valid, finish M6, promote capability status only if all required items are `[x]`, and mark spec `completed` last.

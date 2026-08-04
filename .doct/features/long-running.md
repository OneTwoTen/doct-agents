# LONG_RUNNING

Status: experimental

## Capability

LONG_RUNNING điều phối yêu cầu nhiều phase/module bằng requirements review, architecture deliberation, executor-neutral planning, milestone execution, validation, documentation impact, evidence-backed checklist reconciliation, checkpoint/resume, final feature synthesis và spec reconciliation.

## Implemented

- Canonical spec workspace `.doct/specs/<feature>/`.
- Tách `requirements.md` (WHAT), `design.md` (HOW), `tasks.md` (WORK), `progress.md` (STATE).
- Requirements review và design review trước implementation.
- Architecture independent-analysis/challenge qua orchestrator.
- Tối đa 6 milestone trước khi tách phase.
- Allowed/Forbidden file ownership cho milestone.
- Executor selection sau khi canonical spec ổn định.
- `tasks.md` dùng stable task IDs + Markdown checkbox làm authoritative execution completion ledger.
- `CHECKLIST_RECONCILE` bắt buộc trước CHECKPOINT/FINALIZE: chỉ tick khi có implementation evidence, fresh required validation và không còn finding critical/high liên quan.
- Blocked/deferred giữ `[ ]` với explicit reason; evidence invalid có thể downgrade `[x]` về `[ ]`.
- `progress.md` chỉ lưu current item, evidence, blockers/deferred và next work; không duplicate checklist.
- Milestone review/validation/docs-impact/checklist-reconcile/checkpoint loop.
- Resume từ `progress.md`, sau đó đối chiếu authoritative checkbox state trong `tasks.md`.
- Final `FEATURE_IMPACT` và feature registry update contract.
- Final reconciliation giữa requirements/design/tasks/progress/feature registry và implementation thực tế.
- Validation revision semantics: metadata-only evidence reconciliation không tự làm stale validation đã pass cho cùng code/test/config/criteria state.

## Not implemented

- Machine-readable spec/feature manifest.
- Structural parser/validator cho semantic consistency của Markdown checklist ngoài regression prompt contract.
- Generic runtime adapter implementation cho mọi executor bên ngoài agent environment.
- Automatic dependency-graph scheduler độc lập với orchestrator prompt contract.

## Important constraints

- Chỉ orchestrator có quyền route subagent.
- Canonical spec không chứa executor-specific directive.
- Global fix/review budget thuộc orchestrator, không thuộc executor.
- Worker `Status: completed`/`Outcome: change-made` không đủ để tick checklist.
- Documentation impact và feature impact là hai gate độc lập.
- Feature registry chỉ phản ánh validated/current capability và không thay thế public docs.
- `stable` chỉ được ghi sau successful final validation cho validation revision liên quan và mọi required checklist item đã reconcile thành `[x]`.

## Validation

Previous GitHub Actions run `30891444582` passed all configured lanes before the latest review/checklist-contract changes. Current validation revision is the latest revision that changes `tests/test_spec_workspace_contract.py`, `agents/planning-agent.agent.md` or `agents/orchestrator.agent.md`; fresh final CI evidence has not yet been recorded in the spec, therefore this capability remains `experimental`.

## Related specs

- `.doct/specs/doct-spec-workspace/`
- Historical design/plan under `docs/superpowers/` cho LONG_RUNNING phiên bản trước.

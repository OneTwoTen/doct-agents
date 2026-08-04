# LONG_RUNNING

Status: experimental

## Capability

LONG_RUNNING điều phối yêu cầu nhiều phase/module bằng requirements review, architecture deliberation, executor-neutral planning, milestone execution, validation, documentation impact, checkpoint/resume, final feature synthesis và spec reconciliation.

## Implemented

- Canonical spec workspace `.doct/specs/<feature>/`.
- Tách `requirements.md` (WHAT), `design.md` (HOW), `tasks.md` (WORK), `progress.md` (STATE).
- Requirements review và design review trước implementation.
- Architecture independent-analysis/challenge qua orchestrator.
- Tối đa 6 milestone trước khi tách phase.
- Allowed/Forbidden file ownership cho milestone.
- Executor selection sau khi canonical spec ổn định.
- Milestone review/validation/docs-impact/checkpoint loop.
- Resume từ `progress.md` mà không dispatch lại completed work.
- Final `FEATURE_IMPACT` và feature registry update contract.
- Final reconciliation giữa requirements/design/tasks/progress/feature registry và implementation thực tế.
- Validation revision semantics: metadata-only evidence reconciliation không tự làm stale validation đã pass cho cùng code/test/config/criteria state.

## Not implemented

- Machine-readable spec/feature manifest.
- Generic runtime adapter implementation cho mọi executor bên ngoài agent environment.
- Automatic dependency-graph scheduler độc lập với orchestrator prompt contract.

## Important constraints

- Chỉ orchestrator có quyền route subagent.
- Canonical spec không chứa executor-specific directive.
- Global fix/review budget thuộc orchestrator, không thuộc executor.
- Documentation impact và feature impact là hai gate độc lập.
- Feature registry chỉ phản ánh validated/current capability và không thay thế public docs.
- `stable` chỉ được ghi sau successful final validation cho validation revision liên quan.

## Validation

Previous GitHub Actions run `30891444582` passed all configured lanes before the latest review fixes. Current validation revision candidate is `f1e6fd9641d1ad48e31e5a7ad6078b47247623a2`; fresh final CI evidence has not yet been recorded in the spec, therefore this capability remains `experimental`.

## Related specs

- `.doct/specs/doct-spec-workspace/`
- Historical design/plan under `docs/superpowers/` cho LONG_RUNNING phiên bản trước.

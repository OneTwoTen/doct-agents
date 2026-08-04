# LONG_RUNNING

Status: experimental

## Capability

LONG_RUNNING điều phối yêu cầu nhiều phase/module bằng requirements review, architecture deliberation, executor-neutral planning, milestone execution, validation, documentation impact, checkpoint/resume và final feature synthesis.

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

## Validation

Repository static contract tests và agent validator khóa path/lifecycle/tool boundaries. Capability chỉ chuyển sang `stable` sau khi full repository validation của thay đổi spec-workspace pass.

## Related specs

- `.doct/specs/doct-spec-workspace/`
- Historical design/plan under `docs/superpowers/` cho LONG_RUNNING phiên bản trước.

# LONG_RUNNING

Status: experimental

## Capability

LONG_RUNNING điều phối yêu cầu nhiều phase/module bằng requirements review, architecture deliberation, executor-neutral planning, milestone execution, validation, documentation impact, evidence-backed checklist reconciliation, checkpoint/resume, final feature synthesis và spec reconciliation.

## Đã triển khai

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
- Tương thích với browser-driven implementation loop trên `main`: writer có thể tự reproduce/verify web UI; `browser-agent` dùng cho independent validation.

## Chưa triển khai

- Machine-readable spec/feature manifest.
- Structural parser/validator đầy đủ cho semantic consistency của Markdown checklist ngoài regression prompt contract.
- Generic runtime adapter implementation cho mọi executor bên ngoài agent environment.
- Automatic dependency-graph scheduler độc lập với orchestrator prompt contract.

## Ràng buộc quan trọng

- Chỉ orchestrator có quyền route subagent.
- Canonical spec không chứa executor-specific directive.
- Global fix/review budget thuộc orchestrator, không thuộc executor.
- Worker `Status: completed`/`Outcome: change-made` không đủ để tick checklist.
- Documentation impact và feature impact là hai gate độc lập.
- Feature registry chỉ phản ánh validated/current capability và không thay thế public docs.
- `stable` chỉ được ghi sau successful final validation cho validation revision liên quan và mọi required checklist item đã reconcile thành `[x]`.

## Validation

Fresh validation sau conflict resolution với `main` chưa được ghi nhận. Capability giữ `experimental` cho tới khi `npm run check` pass trên validation revision mới và `CHECKLIST_RECONCILE` hoàn tất.

## Related specs

- `.doct/specs/doct-spec-workspace/`
- Historical design/plan dưới `docs/superpowers/` cho LONG_RUNNING phiên bản trước.

# LONG_RUNNING

Status: stable

## Capability

LONG_RUNNING điều phối yêu cầu nhiều phase/module bằng requirements review, architecture analysis, planning, milestone execution, validation, documentation impact, đối chiếu checklist, checkpoint/resume và cập nhật feature state.

## Đã triển khai

- Với spec mới: dùng `docs/specs/<feature>/` nếu project đã có `docs/`; nếu chưa có `docs/` thì dùng `.doct/specs/<feature>/`.
- Spec đã tồn tại tiếp tục dùng `Spec path` cũ; không tự di chuyển giữa hai vị trí.
- Tách `requirements.md` (WHAT), `design.md` (HOW), `tasks.md` (WORK), `progress.md` (STATE).
- Requirements review và design review trước implementation.
- Architecture independent-analysis/challenge qua orchestrator.
- Tối đa 6 milestone trước khi tách phase.
- Allowed/Forbidden file ownership cho milestone.
- Executor selection sau khi spec ổn định.
- `tasks.md` dùng stable task IDs + Markdown checkbox làm nguồn chính để xác định task đã hoàn tất.
- `CHECKLIST_RECONCILE` bắt buộc trước CHECKPOINT/FINALIZE: chỉ tick khi có implementation evidence, fresh required validation và không còn finding critical/high liên quan.
- Blocked/deferred giữ `[ ]` với explicit reason; evidence invalid có thể downgrade `[x]` về `[ ]`.
- `progress.md` chỉ lưu current item, evidence, blockers/deferred và next work; không duplicate checklist.
- Milestone review/validation/docs-impact/checklist-reconcile/checkpoint loop.
- Resume từ `progress.md`, sau đó đối chiếu checkbox state trong `tasks.md`.
- Final `FEATURE_IMPACT` và feature registry update.
- Đối chiếu cuối giữa requirements/design/tasks/progress/feature registry và implementation thực tế.
- Validation revision semantics: thay đổi chỉ để đồng bộ metadata/evidence không tự làm stale validation đã pass cho cùng code/test/config/criteria state.
- Tương thích với browser-driven implementation loop trên `main`: writer có thể tự reproduce/verify web UI; `browser-agent` dùng cho independent validation.

## Chưa triển khai

- Machine-readable spec/feature manifest.
- Structural parser/validator đầy đủ cho semantic consistency của Markdown checklist ngoài regression prompt checks.
- Generic runtime adapter implementation cho mọi executor bên ngoài agent environment.
- Automatic dependency-graph scheduler độc lập với orchestrator.

## Ràng buộc quan trọng

- Chỉ orchestrator có quyền route subagent.
- Các file đặc tả không chứa executor-specific directive.
- Global fix/review budget thuộc orchestrator, không thuộc executor.
- Worker `Status: completed`/`Outcome: change-made` không đủ để tick checklist.
- Documentation impact và feature impact là hai bước độc lập.
- Feature registry chỉ phản ánh validated/current capability và không thay thế public docs.
- `stable` chỉ được ghi sau successful final validation cho validation revision liên quan và mọi required checklist item đã reconcile thành `[x]`.

## Validation

Behavior revision `9e9d7f641c62ec9448b7c28c074fa2aad9e988ed` đã pass GitHub Actions run `30971295108` trên Ubuntu current, Ubuntu minimum và Windows current. Mỗi lane hoàn thành full `npm run check`, gồm regression cho flexible `Spec path`, agent result fields, validator, package dry-run và smoke test. Các commit sau revision này chỉ cập nhật feature/plan metadata và có thể reuse evidence theo validation-revision rule.

## Related specs

- `.doct/specs/doct-spec-workspace/` — lịch sử thiết kế workspace ban đầu.
- Historical design/plan dưới `docs/superpowers/` cho LONG_RUNNING phiên bản trước.

# Yêu cầu cho Doct Spec Workspace

Status: completed

## Mục tiêu

Tách LONG_RUNNING khỏi Superpowers bằng một spec workspace do doct-agents sở hữu, đồng thời có feature registry tổng hợp capability hiện tại của project.

## Ngoài phạm vi

- Không thay đổi router-only subagent ownership.
- Không thay đổi validation ownership hoặc worker outcome vocabulary.
- Không biến FAST_FIX thành spec-driven workflow.
- Không bắt buộc user approve giữa mọi phase nếu không có ambiguity ảnh hưởng behavior.

## Yêu cầu

1. LONG_RUNNING lưu state chuẩn tại `.doct/specs/<feature>/` với `requirements.md`, `design.md`, `tasks.md`, `progress.md`.
2. `requirements.md` là source of truth cho WHAT; không chứa implementation task chi tiết.
3. `design.md` là source of truth cho HOW và Architecture decisions.
4. `tasks.md` là executable roadmap/milestone plan, tối đa 6 milestone trước khi phải tách phase, đồng thời là authoritative checklist ledger.
5. `progress.md` là runtime/checkpoint/evidence state và không sao chép checklist.
6. Project có `.doct/features/index.md` để tổng hợp capability và status.
7. Feature quan trọng có `.doct/features/<feature>.md` mô tả current-state behavior, phần đã có/chưa có và Related specs.
8. LONG_RUNNING có `FEATURE_IMPACT` trước `FINALIZE` để cập nhật feature registry khi capability thay đổi.
9. Superpowers, OpenCode hoặc executor khác chỉ là execution mechanism; canonical spec không phụ thuộc executor.
10. `.doct/` được commit vào Git để resume qua session, máy và agent.
11. Mọi executable task trong `tasks.md` có ID ổn định và Markdown checkbox `- [ ]`/`- [x]`.
12. Checkbox chỉ được tick sau `CHECKLIST_RECONCILE` dựa trên implementation evidence, fresh required validation và review state; worker status không phải bằng chứng hoàn tất.
13. Blocked/deferred giữ `- [ ]` với lý do rõ; evidence mất hiệu lực phải hạ `[x]` về `[ ]`.

## Acceptance Criteria

- `planning-agent` không còn ghi plan mới vào `docs/superpowers/plans/...`.
- `planning-agent` tạo/cập nhật đúng bốn artifact `.doct/specs/<feature>/` với ownership rõ.
- `orchestrator` có lifecycle requirements/design/tasks/progress, `CHECKLIST_RECONCILE` và `FEATURE_IMPACT -> UPDATE_FEATURE_REGISTRY`.
- `docs-agent` phân biệt documentation impact với feature registry impact.
- README mô tả workspace mới, checklist contract và cách resume.
- Repository contract tests khóa các path/token quan trọng của workflow mới.

## Ràng buộc

- Giữ prompt budget hiện tại của validator.
- Không cấp thêm `agent` tool cho worker.
- Không thêm runtime dependency.
- Không làm thay đổi semantics của FAST_FIX.

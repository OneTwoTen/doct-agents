# Doct Spec Workspace Requirements

Status: approved

## Goal

Tách LONG_RUNNING khỏi Superpowers bằng một spec workspace do doct-agents sở hữu, đồng thời có feature registry tổng hợp trạng thái capability hiện tại của project.

## Non-goals

- Không thay đổi router-only subagent ownership.
- Không thay đổi validation ownership hoặc worker outcome vocabulary.
- Không biến FAST_FIX thành spec-driven workflow.
- Không bắt buộc người dùng approve giữa mọi phase nếu không có ambiguity quyết định behavior.

## Requirements

1. LONG_RUNNING phải lưu state chuẩn tại `.doct/specs/<feature>/` với `requirements.md`, `design.md`, `tasks.md`, `progress.md`.
2. `requirements.md` là source of truth cho WHAT; không chứa implementation task chi tiết.
3. `design.md` là source of truth cho HOW và architecture decisions.
4. `tasks.md` là executable roadmap/milestone plan, tối đa 6 milestone trước khi phải tách phase.
5. `progress.md` là runtime/checkpoint state và không được dùng thay cho requirements/design/tasks.
6. Project phải có `.doct/features/index.md` để tổng hợp capability và status.
7. Feature quan trọng phải có `.doct/features/<feature>.md` mô tả current-state behavior, implemented/not implemented và related specs.
8. LONG_RUNNING phải có `FEATURE_IMPACT` trước FINALIZE để cập nhật feature registry khi capability thay đổi.
9. Superpowers, OpenCode hoặc executor khác chỉ là execution mechanism; canonical spec không được phụ thuộc executor.
10. `.doct/` được commit vào Git để resume qua session/máy/agent.

## Acceptance Criteria

- `planning-agent` không còn ghi plan vào `docs/superpowers/plans/...`.
- `planning-agent` tạo/cập nhật đúng bốn artifact `.doct/specs/<feature>/` với ownership rõ.
- `orchestrator` có lifecycle requirements/design/tasks/progress và `FEATURE_IMPACT -> UPDATE_FEATURE_REGISTRY`.
- `docs-agent` phân biệt documentation impact với feature registry impact.
- README mô tả workspace mới và cách resume.
- Repository contract tests khóa các path/token quan trọng của workflow mới.

## Constraints

- Giữ prompt budget hiện tại của validator.
- Không cấp thêm `agent` tool cho worker.
- Không thêm runtime dependency.
- Không làm thay đổi semantics của FAST_FIX.

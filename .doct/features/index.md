# Danh mục tính năng

| Feature | Status | Related spec | Last changed |
| --- | --- | --- | --- |
| Orchestrator-only routing | stable | historical | 2026-07-30 |
| FAST_FIX workflow | stable | historical | 2026-07-30 |
| Browser-driven implementation loop | stable | historical/main | 2026-08-04 |
| LONG_RUNNING workflow | in-progress | `.doct/specs/doct-spec-workspace/` | 2026-08-05 |
| Documentation impact lifecycle | stable | historical | 2026-07-30 |
| Executor-neutral spec workspace | in-progress | `.doct/specs/doct-spec-workspace/` | 2026-08-05 |
| Feature registry | stable | `.doct/specs/doct-spec-workspace/` | 2026-08-04 |
| Evidence-backed task checklist | stable | `.doct/specs/doct-spec-workspace/` | 2026-08-04 |
| Validation ownership | stable | historical | 2026-07-31 |

## Ý nghĩa status

- `planned`: đã được chấp thuận nhưng chưa triển khai.
- `in-progress`: implementation chưa hoàn tất hoặc thay đổi hiện tại chưa có final validation.
- `experimental`: đã có implementation nhưng stability evidence còn thiếu.
- `stable`: capability hiện tại đã được validate.
- `deprecated`: chỉ giữ để tương thích và dự kiến loại bỏ.
- `removed`: không còn được hỗ trợ.

Feature records trong thư mục này mô tả current-state behavior. LONG_RUNNING specs có thể nằm ở `docs/specs/<feature>/` hoặc `.doct/specs/<feature>/` theo `Spec path` đã chọn; các spec cũ giữ nguyên vị trí lịch sử.

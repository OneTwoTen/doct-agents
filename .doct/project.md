# Tổng quan project doct-agents

## Mục đích

doct-agents cung cấp custom agents và orchestration contracts để phân tích, triển khai, review, validate và document thay đổi kỹ thuật theo least-privilege routing.

File này chỉ mô tả kiến trúc và knowledge model tương đối tĩnh. Danh sách capability hiện tại nằm ở `.doct/features/index.md` để tránh duplicate và drift.

## Sơ đồ kiến trúc

```text
orchestrator
├── requirements / architecture / planning
├── implementation / refactor / test
├── review / security / dependency / performance / browser
├── docs
└── execution environment
    ├── native agent tools
    ├── Superpowers-compatible execution
    └── other supported executors
```

Orchestrator sở hữu lifecycle, routing, review budget, validation evidence, checklist reconciliation và checkpoint. Executor chỉ sở hữu mechanics triển khai.

## Knowledge model cho LONG_RUNNING

```text
.doct/project.md
    ↓
.doct/features/index.md
    ↓
.doct/features/<feature>.md
    ↑ Related specs
.doct/specs/<feature>/
├── requirements.md
├── design.md
├── tasks.md
└── progress.md
```

- Specs lưu change intent/history.
- `tasks.md` là authoritative execution checklist.
- `progress.md` là runtime/evidence journal.
- Feature records lưu current-state truth.

## Đang tiếp tục chuẩn hóa

- Executor adapters ngoài native workflow là capability riêng và chỉ được ghi `stable` khi có implementation + validation evidence.
- Machine-readable manifest và structural checklist validator có thể được triển khai bằng spec riêng sau này.

## Giới hạn hiện tại

- Feature registry là Markdown contract, chưa có generated machine-readable manifest.
- Historical plans dưới `docs/superpowers/` vẫn được giữ làm lịch sử; LONG_RUNNING mới không dùng chúng làm canonical state.

## Catalog

Xem `.doct/features/index.md`.

# doct-agents Project View

## Purpose

doct-agents cung cấp custom agents và orchestration contracts để phân tích, triển khai, review, validate và document thay đổi kỹ thuật theo least-privilege routing.

## Current capabilities

- Orchestrator-only subagent routing.
- FAST_FIX cho thay đổi cục bộ một change-validation cycle.
- LONG_RUNNING cho roadmap/milestone/checkpoint dài hơi.
- Requirement extraction và architecture proposal/challenge.
- Dedicated implementation, review, test, security, dependency, performance, browser và docs workers.
- Validation ownership để tránh chạy lặp cùng command trên cùng revision.
- Documentation impact lifecycle.
- Executor-neutral spec workspace tại `.doct/specs/<feature>/` cho LONG_RUNNING.
- Feature registry tại `.doct/features/` để tổng hợp current-state capability.

## Architecture map

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

Orchestrator sở hữu lifecycle, routing, review budget, validation evidence và checkpoint. Executor chỉ sở hữu mechanics triển khai.

## Long-running knowledge model

```text
.doct/project.md
    ↓
.doct/features/index.md
    ↓
.doct/features/<feature>.md
    ↑ related specs
.doct/specs/<feature>/
├── requirements.md
├── design.md
├── tasks.md
└── progress.md
```

Specs lưu change intent/history; feature records lưu current-state truth.

## In progress

- Chuẩn hóa executor adapters ngoài native workflow là capability riêng và chỉ được ghi stable khi có implementation + validation evidence.

## Known limitations

- Feature registry là Markdown contract, chưa có generated machine-readable manifest.
- Historical plans dưới `docs/superpowers/` vẫn được giữ làm lịch sử; workflow LONG_RUNNING mới không dùng chúng làm canonical state.

## Catalog

Xem `.doct/features/index.md`.

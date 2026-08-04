# doct-agents Project View

## Purpose

doct-agents cung cấp custom agents và orchestration contracts để phân tích, triển khai, review, validate và document thay đổi kỹ thuật theo least-privilege routing.

Current capability/status không duplicate trong file này. Xem `.doct/features/index.md` để lấy project capability catalog hiện tại.

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
    ↓ architecture / knowledge model
.doct/features/index.md
    ↓ current capability catalog
.doct/features/<feature>.md
    ↑ related specs
.doct/specs/<feature>/
├── requirements.md
├── design.md
├── tasks.md
└── progress.md
```

Specs lưu change intent/history; feature records lưu current-state truth. `.doct/project.md` chỉ giữ project purpose, architecture và knowledge-model conventions tương đối ổn định để tránh drift với feature catalog.

## Canonical ownership

- `.doct/specs/<feature>/requirements.md`: WHAT.
- `.doct/specs/<feature>/design.md`: HOW.
- `.doct/specs/<feature>/tasks.md`: WORK.
- `.doct/specs/<feature>/progress.md`: STATE.
- `.doct/features/index.md`: danh mục capability/status hiện tại.
- `.doct/features/<feature>.md`: current-state behavior của capability quan trọng.

## Known limitations

- Feature registry là Markdown contract, chưa có generated machine-readable manifest.
- Historical plans dưới `docs/superpowers/` vẫn được giữ làm lịch sử; workflow LONG_RUNNING mới không dùng chúng làm canonical state.
- Executor adapter cụ thể phải có implementation + validation riêng trước khi được ghi stable trong feature catalog.

## Catalog

Xem `.doct/features/index.md` để biết project hiện có những capability nào, status và related spec tương ứng.

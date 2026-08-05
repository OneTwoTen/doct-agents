# Tổng quan project doct-agents

## Mục đích

doct-agents cung cấp custom agents và quy tắc điều phối để phân tích, triển khai, review, validate và document thay đổi kỹ thuật theo least-privilege routing.

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

Orchestrator quản lý lifecycle, routing, review budget, validation evidence, đối chiếu checklist và checkpoint. Executor chỉ xử lý cách thực thi.

## Knowledge model cho LONG_RUNNING

```text
.doct/project.md
    ↓
.doct/features/index.md
    ↓
.doct/features/<feature>.md
    ↑ Related specs
<spec-path>/
├── requirements.md
├── design.md
├── tasks.md
└── progress.md
```

Với spec mới, `<spec-path>` là:

- `docs/specs/<feature>/` nếu project đã có `docs/`;
- `.doct/specs/<feature>/` nếu project chưa có `docs/`.

Spec đã tồn tại tiếp tục dùng path cũ, không tự di chuyển giữa hai vị trí.

- Specs lưu change intent/history.
- `tasks.md` là checklist chính để xác định công việc đã hoàn tất.
- `progress.md` lưu vị trí hiện tại và validation evidence để resume.
- Feature records lưu current-state truth.

## Đang tiếp tục chuẩn hóa

- Executor adapters ngoài native workflow là capability riêng và chỉ được ghi `stable` khi có implementation + validation evidence.
- Machine-readable manifest và structural checklist validator có thể được triển khai bằng spec riêng sau này.

## Giới hạn hiện tại

- Feature registry là Markdown, chưa có generated machine-readable manifest.
- Historical plans dưới `docs/superpowers/` vẫn được giữ làm lịch sử; LONG_RUNNING mới dùng `Spec path` được chọn theo cấu trúc project.

## Catalog

Xem `.doct/features/index.md`.

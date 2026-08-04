# Tiến độ Doct Spec Workspace

Spec: `.doct/specs/doct-spec-workspace/`
Status: implementing

## Milestone đã có implementation

- M1 — Repository contract test đã được triển khai trước rebase và đang chờ fresh validation.
- M2 — `planning-agent` đã chuyển sang executor-neutral `.doct/specs/<feature>/` ownership và đang chờ fresh validation.
- M3 — LONG_RUNNING đã có requirements/design review gates, executor selection, feature impact, strict checklist reconciliation và final reconciliation; browser-driven implementation loop từ `main` được giữ khi resolve conflict.
- M4 — `docs-agent` đã có mode `feature-update` riêng.
- M5 — `.doct/project.md`, feature catalog/current-state record và README guidance đang được khôi phục trên `main` mới.

Các dòng trên là implementation references, **không đồng nghĩa checkbox trong `tasks.md` đã completed**. Checklist chỉ được tick bởi `CHECKLIST_RECONCILE` sau fresh validation.

## Current milestone

M6 — Kiểm chứng cuối và reconciliation.

## Current task

Resolve conflict với `main`, chuẩn hóa ngôn ngữ và chạy fresh repository validation.

## Current checklist item

`M6-T1` — `npm run check` pass cho validation revision sau conflict resolution.

## Blocked/deferred items

Không có blocker bên ngoài. Toàn bộ required checkbox M1-M6 đang giữ `[ ]` cho tới khi fresh validation + reconciliation hoàn tất.

## Validation evidence

Evidence cũ: GitHub Actions run `30891444582` đã pass trước các review/checklist/conflict-resolution changes và không được dùng để tick checklist hiện tại.

Validation revision hiện tại sẽ là revision gần nhất thay đổi agent/test/README contract sau khi conflict resolution hoàn tất. Fresh CI evidence chưa được ghi nhận nên spec vẫn `implementing` và capability mới vẫn `experimental`.

Metadata-only reconciliation sau successful validation có thể reuse evidence nếu không thay đổi code, test, config, environment contract, requirement/design behavior hoặc Validation criteria.

## Quyết định kiến trúc

- Canonical LONG_RUNNING state thuộc `.doct/`, không thuộc Superpowers.
- Requirements, design, work plan và runtime progress là artifact tách biệt.
- `tasks.md` là authoritative completion ledger; `progress.md` là runtime/evidence journal.
- Checkbox chỉ được tick qua `CHECKLIST_RECONCILE`; evidence thắng prose/status.
- Feature registry là current-state project memory; specs là change history.
- Executor mechanics nằm dưới ranh giới orchestration của doct-agents.
- Documentation impact và feature impact là hai gate độc lập.
- Browser-driven implementation loop trên `main` phải được bảo toàn khi tích hợp LONG_RUNNING mới.
- Validation freshness gắn với validation revision có thay đổi liên quan, không gắn với metadata-only commit.

## Docs impact

Required: README phải mô tả canonical `.doct/specs`, strict checklist/reconciliation và đồng thời giữ browser-driven implementation guidance của `main`.

## Feature impact

Added candidates:
- Executor-neutral spec workspace.
- Feature registry và project capability catalog.
- Evidence-backed authoritative task checklist.

Changed candidates:
- LONG_RUNNING planning/checkpoint lifecycle.
- Final reconciliation và validation-revision semantics.
- Docs agent hỗ trợ feature-registry synthesis tách khỏi public docs impact.

Removed:
- LONG_RUNNING mới không dùng `docs/superpowers/plans/...` làm canonical state. Historical files vẫn được giữ.

## Rủi ro còn lại

- Fresh CI evidence sau conflict resolution chưa có.
- Feature registry vẫn là Markdown-only; chưa có machine-readable manifest.
- Chưa có structural parser/validator đầy đủ cho semantic consistency của mọi Markdown checklist ngoài regression contract.

## Next work

Hoàn tất reapply/merge README + orchestrator + agent contract trên `main` mới, chạy fresh validation, sau đó `CHECKLIST_RECONCILE` từng item M1-M6. Chỉ khi toàn bộ required item thành `[x]` mới đổi spec sang `completed` và capability sang `stable`.

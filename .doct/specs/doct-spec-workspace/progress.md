# Tiến độ Doct Spec Workspace

Spec: `.doct/specs/doct-spec-workspace/`
Status: completed

## Milestone đã hoàn tất

- M1 — Repository contract tests cho spec workspace/checklist đã được triển khai và validate.
- M2 — `planning-agent` đã chuyển sang executor-neutral `.doct/specs/<feature>/` ownership.
- M3 — LONG_RUNNING đã có requirements/design review gates, executor selection, feature impact, strict checklist reconciliation và final reconciliation; browser-driven implementation loop từ `main` được bảo toàn.
- M4 — `docs-agent` có mode `feature-update` riêng.
- M5 — `.doct/project.md`, feature catalog/current-state record và README guidance đã được cập nhật và chuẩn hóa ngôn ngữ.
- M6 — Conflict resolution, fresh validation và final checklist reconciliation đã hoàn tất.

## Current milestone

None.

## Current task

None.

## Current checklist item

None — mọi required checklist item trong `tasks.md` đã được reconcile thành `[x]`.

## Blocked/deferred items

Không có required blocker/deferred item.

## Validation evidence

Validation revision: `90a8b375e0e8d380859feb0fae6af5429c5623b9`.
GitHub Actions run: `30903392325`, workflow `Validate agents`.

- `Validate (ubuntu-current)`: PASS.
- `Validate (ubuntu-minimum)`: PASS.
- `Validate (windows-current)`: PASS.
- Mỗi lane hoàn thành `npm run check`, bao gồm Node tests, Python tests, agent validator, package dry-run và package smoke test theo repository scripts.

Các commit sau validation revision chỉ reconcile metadata trong `.doct/`; chúng không đổi code, tests, config, environment contract, requirement/design behavior hoặc Validation criteria nên reuse evidence theo validation-revision rule.

## Quyết định kiến trúc

- Canonical LONG_RUNNING state thuộc `.doct/`, không thuộc Superpowers.
- Requirements, design, work plan và runtime progress là artifact tách biệt.
- `tasks.md` là authoritative completion ledger; `progress.md` là runtime/evidence journal.
- Checkbox chỉ được tick qua `CHECKLIST_RECONCILE`; evidence thắng prose/status.
- Feature registry là current-state project memory; specs là change history.
- Executor mechanics nằm dưới ranh giới orchestration của doct-agents.
- Documentation impact và feature impact là hai gate độc lập.
- Browser-driven implementation loop trên `main` được bảo toàn khi tích hợp LONG_RUNNING mới.
- Validation freshness gắn với validation revision có thay đổi liên quan, không gắn với metadata-only commit.

## Docs impact

Completed: README mô tả canonical `.doct/specs`, strict checklist/reconciliation, cách resume và browser-driven implementation loop. Prose mới được ưu tiên tiếng Việt; tiếng Anh được giữ cho key, stage/status enum, path/command, tên agent và thuật ngữ kỹ thuật cần thiết.

## Feature impact

Added:
- Executor-neutral spec workspace.
- Feature registry và project capability catalog.
- Evidence-backed authoritative task checklist.

Changed:
- LONG_RUNNING planning/checkpoint lifecycle.
- Final reconciliation và validation-revision semantics.
- Docs agent hỗ trợ feature-registry synthesis tách khỏi public docs impact.

Removed:
- LONG_RUNNING mới không dùng `docs/superpowers/plans/...` làm canonical state. Historical files vẫn được giữ.

## Rủi ro còn lại

- Feature registry vẫn là Markdown-only; chưa có machine-readable manifest.
- Chưa có structural parser/validator đầy đủ cho semantic consistency của mọi Markdown checklist ngoài regression contract.
- Generic executor adapters ngoài environment hiện tại cần spec/validation riêng.

## Next work

None cho spec này. Feature mới hoặc executor integration mới phải tạo spec riêng, dùng authoritative checklist và chỉ cập nhật feature registry sau validation.

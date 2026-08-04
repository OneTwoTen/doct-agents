# Danh sách triển khai Doct Spec Workspace

Status: implementing

## Ràng buộc chung

- Không đổi FAST_FIX semantics.
- Chỉ orchestrator có subagent routing.
- Không thêm runtime dependency.
- Giữ validator prompt budgets và validation ownership hiện có.
- Checklist trong file này là authoritative completion ledger; `progress.md` chỉ lưu current state/evidence.
- Sau rebase/conflict resolution, checkbox chỉ được tick lại sau fresh validation và `CHECKLIST_RECONCILE`.

## M1 — Khóa contract của repository

Objective: thêm regression assertions cho `.doct/specs`, feature registry, checklist và LONG_RUNNING lifecycle mới.

Allowed files: `tests/test_spec_workspace_contract.py`.

Checklist:
- [ ] `M1-T1` Test yêu cầu `planning-agent` chứa `.doct/specs/<feature>/` và bốn artifact names.
- [ ] `M1-T2` Test yêu cầu orchestrator chứa `REQUIREMENTS_REVIEW`, `DESIGN_REVIEW`, `SELECT_EXECUTOR`, `FEATURE_IMPACT`, `UPDATE_FEATURE_REGISTRY`.
- [ ] `M1-T3` Test yêu cầu final reconciliation contract trước khi LONG_RUNNING được kết luận hoàn tất.
- [ ] `M1-T4` Test yêu cầu feature catalog contract và README dùng canonical `.doct/specs/...` path.
- [ ] `M1-T5` Test khóa strict checklist contract: evidence-backed tick, blocked/deferred semantics và progress không duplicate checklist.

Validation: `python -m unittest tests.test_spec_workspace_contract -v`.

## M2 — Tách ownership của planning

Objective: biến `planning-agent` thành owner của executor-neutral spec workspace.

Allowed files: `agents/planning-agent.agent.md`.

Checklist:
- [ ] `M2-T1` Không còn canonical path `docs/superpowers/plans/...` cho LONG_RUNNING mới.
- [ ] `M2-T2` Tách WHAT/HOW/WORK/STATE ownership.
- [ ] `M2-T3` Checkpoint chỉ cập nhật `progress.md`; requirements/design/tasks chỉ thay đổi khi source-of-truth tương ứng thay đổi.
- [ ] `M2-T4` Checklist contract quy định `- [ ]`/`- [x]`, ID ổn định, evidence gate, blocked/deferred và downgrade khi evidence invalid.

Validation: repository contract test + agent validator.

## M3 — Mở rộng điều phối LONG_RUNNING

Objective: orchestration dùng spec phases, executor selection, browser-loop compatibility, feature impact, checklist reconciliation và final reconciliation lifecycle.

Allowed files: `agents/orchestrator.agent.md`, `agents/req-extractor.agent.md`.

Checklist:
- [ ] `M3-T1` State machine có requirements/design review gates và executor selection.
- [ ] `M3-T2` Milestone handoff dùng Spec path/Task/Milestone thay vì Plan path cũ.
- [ ] `M3-T3` Feature impact candidates được checkpoint.
- [ ] `M3-T4` Trước FINALIZE reconcile requirements/design/tasks/progress/feature registry với implementation và validation evidence thực tế.
- [ ] `M3-T5` Mỗi milestone bắt buộc qua `CHECKLIST_RECONCILE` trước CHECKPOINT; không advance từ worker status/prose.
- [ ] `M3-T6` Checkbox chỉ được tick khi có implementation evidence + fresh required validation + không còn finding critical/high liên quan.
- [ ] `M3-T7` Browser-driven implementation loop từ `main` vẫn được giữ: `implementation-agent` tự reproduce/verify web UI; `browser-agent` dùng cho independent validation.

Validation: repository contract test + browser capability ownership test + agent validator.

## M4 — Tách docs impact và feature registry impact

Objective: `docs-agent` có mode cập nhật current-state feature record mà không trộn user-facing docs.

Allowed files: `agents/docs-agent.agent.md`.

Checklist:
- [ ] `M4-T1` Có mode `feature-update`.
- [ ] `M4-T2` Chỉ update `.doct/features` từ validated feature impact synthesis.
- [ ] `M4-T3` Không dùng feature registry thay cho README/public docs.

Validation: repository contract test + agent validator.

## M5 — Tạo project knowledge và cập nhật tài liệu người dùng

Objective: tạo project architecture overview + feature catalog và cập nhật README.

Allowed files: `.doct/project.md`, `.doct/features/index.md`, `.doct/features/long-running.md`, `README.md`.

Checklist:
- [ ] `M5-T1` `.doct/project.md` mô tả purpose, architecture và knowledge model nhưng không duplicate current capabilities.
- [ ] `M5-T2` Agent mới đọc `.doct/project.md` + feature index để biết architecture và capability hiện tại.
- [ ] `M5-T3` LONG_RUNNING feature record mô tả phần đã triển khai, phần chưa triển khai và current spec model.
- [ ] `M5-T4` README mô tả cách resume bằng `.doct/specs/<feature>/progress.md` và strict checklist contract.
- [ ] `M5-T5` README giữ đầy đủ browser-driven implementation loop đã có trên `main`.

Validation: link/path consistency review + package tests.

## M6 — Kiểm chứng cuối và reconciliation

Objective: chạy toàn bộ regression/package contract trên branch đã resolve conflict, rồi reconcile canonical spec state với implementation thực tế.

Checklist:
- [ ] `M6-T1` `npm run check` pass cho validation revision sau conflict resolution.
- [ ] `M6-T2` `CHECKLIST_RECONCILE` xác nhận mọi required item M1-M5 có implementation + validation evidence hợp lệ và tick chúng sang `[x]`.
- [ ] `M6-T3` `progress.md` phản ánh đúng current item, blockers/deferred và validation revision; không duplicate checklist.
- [ ] `M6-T4` `.doct/features/*` chỉ promote capability sang `stable` sau final validation + reconciliation.
- [ ] `M6-T5` Spec status đổi `completed` chỉ sau khi mọi required checklist item là `- [x]`.

Validation command:
- `npm run check`

Validation revision: revision gần nhất thay đổi agent/test/README contract liên quan; final evidence pending.

Final reconciliation:
- `requirements.md` phản ánh final intended behavior.
- `design.md` phản ánh Architecture decisions cuối.
- `tasks.md` phản ánh roadmap/work thực tế và authoritative checkbox state.
- `progress.md` phản ánh validation revision/evidence tương ứng, Current checklist item và blockers/deferred.
- `.doct/features/*` chỉ ghi stable/current capability sau successful final validation.

Definition of done: `npm run check` pass cho validation revision cuối, mọi required checklist item là `- [x]`, không còn canonical LONG_RUNNING instruction trỏ sang `docs/superpowers/plans`, spec artifacts không mâu thuẫn trạng thái và feature registry phản ánh behavior mới.

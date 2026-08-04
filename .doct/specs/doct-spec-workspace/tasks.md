# Doct Spec Workspace Implementation Tasks

Status: completed

## Global constraints

- Không đổi FAST_FIX semantics.
- Chỉ orchestrator có subagent routing.
- Không thêm runtime dependency.
- Giữ validator prompt budgets và validation ownership hiện có.

## M1 — Lock repository contract

Objective: thêm regression assertions cho `.doct/specs`, feature registry và LONG_RUNNING lifecycle mới.

Allowed files: `tests/test_spec_workspace_contract.py`.

Acceptance criteria:
- Test yêu cầu `planning-agent` chứa `.doct/specs/<feature>/` và bốn artifact names.
- Test yêu cầu orchestrator chứa `REQUIREMENTS_REVIEW`, `DESIGN_REVIEW`, `SELECT_EXECUTOR`, `FEATURE_IMPACT`, `UPDATE_FEATURE_REGISTRY`.
- Test yêu cầu final reconciliation contract trước khi LONG_RUNNING được kết luận hoàn tất.
- Test yêu cầu feature catalog contract và README dùng canonical `.doct/specs/...` path.

Validation: `python -m unittest tests.test_spec_workspace_contract -v`.

## M2 — Refactor planning ownership

Objective: biến planning-agent thành owner của executor-neutral spec workspace.

Allowed files: `agents/planning-agent.agent.md`.

Acceptance criteria:
- Không còn canonical path `docs/superpowers/plans/...`.
- Tách WHAT/HOW/WORK/STATE ownership.
- Checkpoint chỉ cập nhật `progress.md`; requirements/design/tasks chỉ thay đổi khi source-of-truth tương ứng thay đổi.

Validation: repository contract test + agent validator.

## M3 — Extend LONG_RUNNING orchestration

Objective: orchestration dùng spec phases, executor selection, feature impact và final reconciliation lifecycle.

Allowed files: `agents/orchestrator.agent.md`, `agents/req-extractor.agent.md`.

Acceptance criteria:
- State machine mới có review gates và executor selection.
- Milestone handoff dùng Spec path/Task/Milestone thay vì plan path.
- Feature impact candidates được checkpoint.
- Trước FINALIZE phải reconcile requirements/design/tasks/progress/feature registry với implementation và validation evidence thực tế.

Validation: repository contract test + agent validator.

## M4 — Separate docs impact and feature registry impact

Objective: docs-agent có mode cập nhật current-state feature record mà không trộn user-facing docs.

Allowed files: `agents/docs-agent.agent.md`.

Acceptance criteria:
- Có mode `feature-update`.
- Chỉ update `.doct/features` từ validated feature impact synthesis.
- Không dùng feature registry thay cho README/public docs.

Validation: repository contract test + agent validator.

## M5 — Bootstrap project knowledge and user docs

Objective: tạo project architecture overview + feature catalog và cập nhật README.

Allowed files: `.doct/project.md`, `.doct/features/index.md`, `.doct/features/long-running.md`, `README.md`.

Acceptance criteria:
- `.doct/project.md` mô tả purpose, architecture và knowledge model nhưng không duplicate danh sách current capabilities vốn thuộc `.doct/features/index.md`.
- Agent mới đọc `.doct/project.md` + feature index để biết architecture và capability hiện tại.
- LONG_RUNNING feature record mô tả implemented/not implemented/current spec model.
- README mô tả cách resume bằng `.doct/specs/<feature>/progress.md`.

Validation: link/path consistency review + package tests.

## M6 — Final verification and reconciliation

Objective: verify toàn bộ regression suite/package contracts và reconcile canonical spec state với implementation thực tế.

Validation commands:
- `npm run check`

Final reconciliation:
- `requirements.md` phản ánh final intended behavior.
- `design.md` phản ánh architecture decisions cuối.
- `tasks.md` phản ánh roadmap/work thực tế và có `Status: completed` khi toàn bộ work hoàn tất.
- `progress.md` phản ánh fresh validation evidence trên final revision.
- `.doct/features/*` chỉ ghi stable/current capability dựa trên cùng fresh evidence.

Definition of done: `npm run check` pass trên final revision, không còn canonical LONG_RUNNING instruction trỏ sang `docs/superpowers/plans`, spec artifacts không mâu thuẫn trạng thái và feature registry phản ánh behavior mới.

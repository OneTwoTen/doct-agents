# Doct Spec Workspace Implementation Tasks

Status: implementing

## Global constraints

- Không đổi FAST_FIX semantics.
- Chỉ orchestrator có subagent routing.
- Không thêm runtime dependency.
- Giữ validator prompt budgets và validation ownership hiện có.

## M1 — Lock repository contract

Objective: thêm regression assertions cho `.doct/specs`, feature registry và LONG_RUNNING lifecycle mới.

Allowed files: `tests/test_validate_agents.py`.

Acceptance criteria:
- Test yêu cầu `planning-agent` chứa `.doct/specs/<feature>/` và bốn artifact names.
- Test yêu cầu orchestrator chứa `REQUIREMENTS_REVIEW`, `DESIGN_REVIEW`, `SELECT_EXECUTOR`, `FEATURE_IMPACT`, `UPDATE_FEATURE_REGISTRY`.
- Test yêu cầu feature catalog contract.

Validation: `python -m unittest tests.test_validate_agents.ValidateAgentsTest.test_repository_supports_long_running_workflow -v`.

## M2 — Refactor planning ownership

Objective: biến planning-agent thành owner của executor-neutral spec workspace.

Allowed files: `agents/planning-agent.agent.md`.

Acceptance criteria:
- Không còn canonical path `docs/superpowers/plans/...`.
- Tách WHAT/HOW/WORK/STATE ownership.
- Checkpoint chỉ cập nhật `progress.md`; requirements/design/tasks chỉ thay đổi khi source-of-truth tương ứng thay đổi.

Validation: repository contract test + agent validator.

## M3 — Extend LONG_RUNNING orchestration

Objective: orchestration dùng spec phases, executor selection và feature impact lifecycle.

Allowed files: `agents/orchestrator.agent.md`, `agents/req-extractor.agent.md`.

Acceptance criteria:
- State machine mới có review gates và executor selection.
- Milestone handoff dùng Spec path/Task/Milestone thay vì plan path.
- Feature impact candidates được checkpoint.

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

Objective: tạo project summary + feature catalog và cập nhật README.

Allowed files: `.doct/project.md`, `.doct/features/index.md`, `.doct/features/long-running.md`, `README.md`.

Acceptance criteria:
- Agent mới có thể đọc `.doct/project.md` + index để biết capability hiện tại.
- LONG_RUNNING feature record mô tả implemented/not implemented/current spec model.
- README mô tả cách resume bằng `.doct/specs/<feature>/progress.md`.

Validation: link/path consistency review + package tests.

## M6 — Final verification

Objective: verify toàn bộ regression suite và package/agent contracts.

Validation commands (đã có evidence trong repo):
- `npm test`
- `python -m unittest discover -s tests -v`
- `python scripts/validate_agents.py`
- `npm pack --dry-run`

Definition of done: tất cả command pass, không còn canonical LONG_RUNNING instruction trỏ sang `docs/superpowers/plans`, feature registry phản ánh behavior mới.

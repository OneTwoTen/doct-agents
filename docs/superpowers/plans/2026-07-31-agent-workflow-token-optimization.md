# Agent Workflow and Token Optimization Implementation Plan

> **Execution status:** completed on branch `feat/optimize-agent-workflow-tokens`.

**Goal:** Giảm token và xung đột workflow bằng outcome semantics, validation ownership, compact contracts và validator guardrails.

**Architecture:** Giữ orchestrator trung tâm và least privilege. Invariant quan trọng được bảo vệ bằng validator/tests; worker prompt chỉ giữ rule thuộc domain của chính nó.

**Tech Stack:** Markdown custom agents, Python 3.9 validator/unittest, Node.js package checks, GitHub Actions.

## Global Constraints

- [x] Chỉ orchestrator được gọi subagent.
- [x] Chỉ `test-agent` được đồng thời `edit + execute`.
- [x] Không thêm dependency runtime mới.
- [x] Python 3.9 được hỗ trợ.
- [x] Không tự động sửa dependency version ngoài scope do orchestrator cung cấp.

## Task 1: Define failing workflow contract tests

- [x] Thêm Outcome vocabulary tests.
- [x] Thêm repository tests cho compact handoff và validation ownership.
- [x] Thêm prompt-size budget test.
- [x] Chạy TDD RED.

Evidence:

- CI run `30599239250` fail đúng 4 assertion mới: Outcome parser, required Outcome, prompt budget và repository compact contract.
- Node/installer tests vẫn pass; không có lỗi môi trường hoặc syntax.

## Task 2: Extend validator guardrails

- [x] Thêm parser và allowlist cho `Outcome`.
- [x] Bắt buộc mọi agent có Outcome contract.
- [x] Thêm prompt body budget: orchestrator 12.000, browser 9.000, worker khác 7.000 ký tự.
- [x] Giữ nguyên validation cho subagent routing, user-invocable và edit/execute allowlist.

## Task 3: Optimize orchestration and validation ownership

- [x] Rút gọn orchestrator nhưng giữ FAST_FIX, LONG_RUNNING, DOCS_IMPACT, checkpoint, blocker và anti-loop.
- [x] Giới hạn handoff context tối đa 10 bullet, không copy nguyên worker result.
- [x] Giới hạn Summary tối đa 120 từ và dùng optional fields.
- [x] Phân biệt worker execution `Status` với business `Outcome`.
- [x] Chuẩn hóa command signature và tái sử dụng fresh validation evidence.
- [x] Tách owner:
  - `test-agent`: test vừa thêm/sửa;
  - `review-agent`: reuse evidence, command hẹp khi thiếu;
  - `cli-executor`: build/lint/typecheck/integration/final;
  - domain agents: audit/benchmark/browser runtime.
- [x] Làm rõ dependency flow: dependency audit-only, implementation sửa manifest trong Allowed files, CLI regenerate lockfile theo command đã giao.

## Task 4: Standardize remaining worker results

- [x] Toàn bộ 17 agent có Outcome contract hợp lệ.
- [x] Loại bỏ prose điều phối lặp khỏi worker nhưng giữ domain safety rules.
- [x] Giữ worker không tự gọi worker ngang hàng.
- [x] Giữ tool set theo least privilege.

Static prompt diff so với `main` tại `5e619d6`:

- 17 agent definitions: 795 dòng cũ bị thay thế bằng 373 dòng mới, net giảm 422 dòng prompt.
- Orchestrator: 230 dòng cũ bị thay thế bằng 65 dòng mới, net giảm 165 dòng.
- Validator chặn prompt tăng vượt budget trong các lần thay đổi sau.

Số token thực tế không suy ra chính xác từ line/character count vì còn phụ thuộc model, context, tool output và session history. Hướng dẫn đo runtime được thêm tại `docs/token-metrics.md`.

## Task 5: Document and verify

- [x] README giải thích Status/Outcome, validation ownership, compact handoff và prompt budget.
- [x] Thêm `docs/token-metrics.md` hướng dẫn đo input/output token bằng VS Code Agent Debug Logs.
- [x] Chạy full `npm run check` trên CI matrix.

GREEN evidence:

- CI run `30599664305`.
- `Validate (ubuntu-minimum)`: success.
- `Validate (ubuntu-current)`: success.
- `Validate (windows-current)`: success.
- Mỗi lane chạy Node tests, Python tests, agent validator, package dry-run và packaged CLI smoke test qua `npm run check`.

## Progress checkpoint

- `Completed milestones`: tests/validator; core workflow; all worker contracts; documentation; full verification.
- `Current milestone`: completed.
- `Blocked items`: none.
- `Validation evidence`: CI run `30599664305`, all three lanes success.
- `Architecture decisions`: orchestrator-only routing; Status/Outcome split; single-owner validation; compact handoff; prompt budgets.
- `Docs impact result`: required and completed (`README.md`, design spec, token metrics guide).
- `Remaining risks`: runtime token savings must be measured over representative sessions; static prompt reduction alone does not guarantee lower total tokens when attached code/log context dominates.
- `Next milestone`: collect at least five Agent Debug sessions per workflow and compare median input/output tokens, tool calls, duration and pass rate.

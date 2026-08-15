# Adaptive FAST_FIX Implementation Plan

> **Execution status:** completed on branch `feat/adaptive-fast-fix`.

**Goal:** Làm FAST_FIX adaptive để task nhỏ mặc định đi direct path với ít worker/handoff hơn, nhưng vẫn tăng validation theo risk và escalate sang LONG_RUNNING khi discovery cho thấy scope không còn bounded.

**Architecture:** Giữ `FAST_FIX` và `LONG_RUNNING` là hai lifecycle cấp cao. `direct`/`guarded` là execution strategy bên trong FAST_FIX, không phải workflow mới. Production change vẫn qua `implementation-agent`; optional worker và validation depth được chọn theo evidence/risk.

## Global Constraints

- [x] Không thêm workflow `SMALL/MEDIUM/LARGE` mới.
- [x] Production code change vẫn bắt buộc qua `implementation-agent`.
- [x] Planning-agent không được dùng trong FAST_FIX.
- [x] Validation depth phụ thuộc risk, không phụ thuộc số dòng diff.
- [x] Giữ validation ownership/fresh evidence rules hiện có.
- [x] Giữ browser-driven implementation behavior hiện có.
- [x] Không thêm dependency runtime mới.

## Task 1: Define adaptive FAST_FIX contract tests

- [x] Thêm repository contract tests cho `direct`/`guarded`, escalation, optional workers, worker budget và FAST_FIX-specific implementation preconditions.
- [x] Xác nhận RED trước implementation.
- [x] Bổ sung regression assertions cho specialized routes `browser-agent`, `refactor-agent`, test-only, explicit `planning-agent = 0` và migration/rollback escalation sau diff review.

Evidence:

- Run `31140501604`: các FAST_FIX contract mới fail đúng vì prompt cũ chưa có adaptive behavior; existing tests không phát hiện regression ngoài scope.
- Run `31141116441`: regression tests mới fail đúng ở explicit planning rule và specialized routes, giúp bắt phần contract bị rơi trong lần refactor đầu.
- Run `31141812176`: regression test mới fail đúng vì `migration/rollback` chưa nằm trực tiếp trong escalation rule.

## Task 2: Implement adaptive FAST_FIX routing and handoff

- [x] `FAST_FIX direct`: `DISCOVER -> IMPLEMENT -> VALIDATE -> FINALIZE`.
- [x] `FAST_FIX guarded`: `DISCOVER -> IMPLEMENT -> optional TEST/REVIEW/DOMAIN -> VALIDATE -> FINALIZE`.
- [x] Thêm explicit escalation sang LONG_RUNNING khi discovery cho thấy task không còn bounded, gồm migration/rollback.
- [x] Review/test/docs/domain worker chỉ được thêm theo risk/evidence; planning-agent không chạy trong FAST_FIX.
- [x] Direct tối đa 2 worker; guarded tối đa 3 worker, worker thứ tư chỉ khi có domain risk rõ; mặc định 1 worker tại một thời điểm.
- [x] FAST_FIX implementation handoff chỉ bắt buộc `Objective`, `Scope`, `Expected behavior`; `Validation plan` trở thành conditional.
- [x] Giữ specialized routing cũ và browser-driven implementation loop.
- [x] Giữ orchestrator prompt dưới budget 12,000 ký tự thay vì tăng budget.

Intermediate evidence:

- Run `31141218314`: 62 Python tests pass nhưng validator chặn prompt `12580 > 12000`, dẫn tới rút prompt thay vì nâng guardrail.
- Các vòng sau bắt exact contract-string regressions trước final GREEN.

## Task 3: Document, measure and verify

- [x] README mô tả FAST_FIX direct/guarded, risk-based validation và escalation.
- [x] `docs/token-metrics.md` tách benchmark direct/guarded và đặt target runtime:
  - `planning-agent calls = 0`;
  - `review-agent default = 0`;
  - `docs-agent default = 0`;
  - median worker count direct `<= 2`;
  - duplicate validation signature `= 0`;
  - một change/validate loop trong trường hợp bình thường.
- [x] Thêm `.doct/features/fast-fix.md` và cập nhật feature index từ validated behavior evidence.
- [x] Review diff để bảo toàn README ngoài scope và các route FAST_FIX đã tồn tại.
- [x] Chạy full repository validation trên Ubuntu current, Ubuntu minimum và Windows current.

## Final validation evidence

Behavior revision: `b7a7ed3f07778d1ec992e0146278bf95aefb7c13`.

GitHub Actions run `31141889762`:

- `Validate (ubuntu-current)`: success.
- `Validate (ubuntu-minimum)`: success.
- `Validate (windows-current)`: success.

Mỗi lane chạy full `npm run check`, gồm Node tests, 62 Python tests, agent validator/prompt-size budget, package dry-run và packaged CLI smoke test.

Các commit sau behavior revision chỉ đồng bộ feature registry/plan evidence; không đổi agent behavior hoặc validation criteria nên behavior evidence trên vẫn hợp lệ theo validation-revision rule. CI của branch vẫn được dùng để kiểm tra metadata head trước khi hoàn tất PR.

## Remaining risk / next measurement

Static contract và cross-platform repository validation đã pass, nhưng mức giảm token/latency runtime chưa được chứng minh bằng session thực. Thu tối thiểu 5 Agent Debug sessions cho mỗi FAST_FIX path trên cùng model/repo revision và so sánh median input/output token, worker count, tool calls, duration và pass rate.

# Agent Orchestration Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Giảm handoff thừa, chuẩn hóa kết quả worker và tự động phát hiện cấu hình agent sai trước khi merge.

**Architecture:** Orchestrator sở hữu state transition và execution budget; worker chỉ xử lý scope được giao và trả contract thống nhất. Một validator Python dùng standard library kiểm tra frontmatter, tham chiếu agent, quyền cơ bản và self-cycle; GitHub Actions chạy validator trên mọi pull request.

**Tech Stack:** VS Code custom agent Markdown, Python 3.11 standard library, GitHub Actions.

## Global Constraints

- Không pin model chưa được xác nhận tồn tại trong workspace.
- Giữ nguyên nguyên tắc least privilege.
- Không thêm dependency runtime cho validator.
- Không cho worker tự mở rộng scope hoặc tự điều phối worker ngang hàng.
- Mọi thay đổi phải có validation hẹp nhất liên quan.

---

### Task 1: Chuẩn hóa orchestration contract

**Files:**
- Modify: `agents/orchestrator.agent.md`
- Modify: `agents/review-agent.agent.md`
- Modify: `agents/aggregator.agent.md`
- Modify: `agents/refactor-agent.agent.md`
- Modify: `agents/test-agent.agent.md`

**Interfaces:**
- Consumes: custom-agent frontmatter và handoff contract hiện có.
- Produces: state machine, execution budget, finding signature và worker result contract thống nhất.

- [ ] **Step 1:** Thêm workflow routing và state machine vào orchestrator.
- [ ] **Step 2:** Thêm giới hạn worker, parallelism, handoff depth và fix cycles.
- [ ] **Step 3:** Quy định worker đề xuất `next`, orchestrator quyết định handoff.
- [ ] **Step 4:** Chuẩn hóa output `Status`, `Summary`, `Scope`, `Findings`, `Changes`, `Validation`, `Next`.
- [ ] **Step 5:** Giới hạn aggregator chỉ dùng khi có ít nhất 3 result sets hoặc 8 findings.

### Task 2: Thêm validator cấu hình agent

**Files:**
- Create: `scripts/validate_agents.py`
- Create: `tests/test_validate_agents.py`

**Interfaces:**
- Consumes: thư mục `agents/*.agent.md`.
- Produces: exit code 0 khi hợp lệ; exit code 1 và danh sách lỗi khi cấu hình sai.

- [ ] **Step 1:** Viết test cho duplicate name, missing reference, invalid edit/execute policy và self-cycle.
- [ ] **Step 2:** Chạy test để xác nhận validator chưa tồn tại.
- [ ] **Step 3:** Implement parser frontmatter không dùng PyYAML.
- [ ] **Step 4:** Implement validation và deterministic error output.
- [ ] **Step 5:** Chạy `python -m unittest discover -s tests -v`.
- [ ] **Step 6:** Chạy `python scripts/validate_agents.py` trên repo thật.

### Task 3: Bật CI và cập nhật tài liệu

**Files:**
- Create: `.github/workflows/validate-agents.yml`
- Modify: `README.md`

**Interfaces:**
- Consumes: validator từ Task 2.
- Produces: required validation signal trên push/PR và hướng dẫn chạy local.

- [ ] **Step 1:** Thêm workflow Python 3.11 chạy unit test và validator.
- [ ] **Step 2:** Cập nhật README với state machine, execution budget và lệnh validation.
- [ ] **Step 3:** Kiểm tra diff chỉ chứa thay đổi đúng scope.
- [ ] **Step 4:** Mở pull request kèm test evidence.

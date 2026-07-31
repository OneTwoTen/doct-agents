# Agent Workflow and Token Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Giảm token và xung đột workflow bằng outcome semantics, validation ownership, compact contracts và validator guardrails.

**Architecture:** Giữ mô hình orchestrator trung tâm và least privilege hiện tại. Thêm invariant vào validator/tests trước, sau đó rút gọn prompt và chuẩn hóa ownership để thay đổi có thể được kiểm chứng tự động.

**Tech Stack:** Markdown custom agents, Python 3.9 validator/unittest, Node.js package checks, GitHub Actions.

## Global Constraints

- Chỉ orchestrator được gọi subagent.
- Chỉ `test-agent` được đồng thời `edit + execute`.
- Không thêm dependency runtime mới.
- Python 3.9 phải được hỗ trợ.
- Không tự động sửa dependency version ngoài scope do orchestrator cung cấp.

---

### Task 1: Define failing workflow contract tests

**Files:**
- Modify: `tests/test_validate_agents.py`

**Interfaces:**
- Consumes: `validate_agents.validate(Path)` và repository agent files.
- Produces: regression tests cho outcome vocabulary, validation ownership, compact handoff và prompt budgets.

- [ ] **Step 1: Add outcome vocabulary tests**

Thêm test chấp nhận `passed | change-made | defect-found | validation-failed | no-change` và từ chối giá trị không khai báo.

- [ ] **Step 2: Add repository workflow tests**

Kiểm tra orchestrator có `fresh validation evidence`, `không copy nguyên worker result`, giới hạn context 10 bullet; review/test/CLI có ownership riêng.

- [ ] **Step 3: Add prompt budget test**

Kiểm tra `validate_agents.validate()` báo lỗi khi body orchestrator hoặc worker vượt budget.

- [ ] **Step 4: Run tests and verify RED**

Run: `python -m unittest tests.test_validate_agents -v`
Expected: FAIL vì validator chưa hiểu Outcome và prompt hiện tại chưa có contract mới.

- [ ] **Step 5: Commit**

```bash
git add tests/test_validate_agents.py
git commit -m "test: define workflow and token optimization contracts"
```

### Task 2: Extend validator guardrails

**Files:**
- Modify: `scripts/validate_agents.py`
- Test: `tests/test_validate_agents.py`

**Interfaces:**
- Consumes: agent frontmatter và Markdown body.
- Produces: `declared_outcome_groups(text)`, outcome allowlist và prompt character budgets.

- [ ] **Step 1: Add outcome parser and allowlist**

Dùng regex tương tự Status để parse dòng `Outcome` và chỉ chấp nhận vocabulary được thiết kế.

- [ ] **Step 2: Add prompt-size validation**

Tính số ký tự body sau frontmatter. Budget: orchestrator 12,000 ký tự; browser 9,000; worker khác 7,000. Báo path, size và limit.

- [ ] **Step 3: Run validator tests**

Run: `python -m unittest tests.test_validate_agents -v`
Expected: outcome/budget unit tests PASS; repository contract tests vẫn FAIL.

- [ ] **Step 4: Commit**

```bash
git add scripts/validate_agents.py tests/test_validate_agents.py
git commit -m "feat: validate outcome vocabulary and prompt budgets"
```

### Task 3: Optimize orchestration and validation ownership

**Files:**
- Modify: `agents/orchestrator.agent.md`
- Modify: `agents/review-agent.agent.md`
- Modify: `agents/test-agent.agent.md`
- Modify: `agents/cli-executor.agent.md`
- Modify: `agents/implementation-agent.agent.md`
- Modify: `agents/dependency-agent.agent.md`

**Interfaces:**
- Consumes: existing worker routing and result contracts.
- Produces: compact handoff/result schema and single-owner validation policy.

- [ ] **Step 1: Refactor orchestrator**

Giữ state machine và safety invariants, nhưng loại bỏ mô tả lặp. Thêm command signature reuse, 10-bullet context limit và compact result behavior.

- [ ] **Step 2: Refine validation agents**

Review tái sử dụng evidence; test chỉ chạy test do nó thay đổi; CLI sở hữu validation tổng và lockfile regeneration được chỉ định.

- [ ] **Step 3: Clarify dependency update path**

Dependency agent audit-only; implementation sửa manifest nếu nằm trong Allowed files; CLI regenerate lockfile theo command đã giao.

- [ ] **Step 4: Add Outcome to changed workers**

Mỗi worker khai báo outcome phù hợp và summary tối đa 120 từ.

- [ ] **Step 5: Run validator tests**

Run: `python -m unittest tests.test_validate_agents -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add agents scripts tests
git commit -m "refactor: reduce agent workflow conflicts and token usage"
```

### Task 4: Standardize remaining worker results

**Files:**
- Modify: remaining `agents/*.agent.md` that lack `Outcome`.

**Interfaces:**
- Consumes: common outcome vocabulary.
- Produces: consistent compact worker result contract across repository.

- [ ] **Step 1: Add compact Outcome field**

Chọn subset phù hợp nhưng chỉ dùng vocabulary chung.

- [ ] **Step 2: Remove duplicated prose**

Không xóa domain-specific safety rules; bỏ các câu permission/handoff lặp khi invariant đã rõ.

- [ ] **Step 3: Run repository validator**

Run: `python scripts/validate_agents.py`
Expected: `Validated 17 agent definitions successfully.`

- [ ] **Step 4: Commit**

```bash
git add agents
git commit -m "refactor: standardize compact worker outcomes"
```

### Task 5: Document and verify

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-07-31-agent-workflow-token-optimization.md`

**Interfaces:**
- Produces: operator guidance and completed checkpoint.

- [ ] **Step 1: Document ownership and token policy**

Thêm bảng validation owner, giải thích Status/Outcome và compact handoff.

- [ ] **Step 2: Run full verification**

Run: `npm run check`
Expected: Node tests, Python tests, agent validator, package dry-run và package smoke đều exit 0.

- [ ] **Step 3: Compare prompt sizes**

Ghi baseline và after character counts cho orchestrator và các worker chính trong PR description.

- [ ] **Step 4: Update checklist and commit**

```bash
git add README.md docs/superpowers/plans/2026-07-31-agent-workflow-token-optimization.md
git commit -m "docs: explain optimized agent workflow contracts"
```

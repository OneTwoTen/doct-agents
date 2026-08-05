# Flexible Spec Path and Clear Agent Language Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cho LONG_RUNNING tự chọn nơi lưu spec theo cấu trúc project và làm ngôn ngữ trong planning/orchestration dễ hiểu hơn.

**Architecture:** Giữ nguyên bốn artifact `requirements.md`, `design.md`, `tasks.md`, `progress.md` và lifecycle hiện tại. Chỉ thay quy tắc chọn thư mục: nếu repository đã có `docs/` thì dùng `docs/specs/<feature>/`; nếu chưa có `docs/` thì dùng `.doct/specs/<feature>/`. Các stage machine-readable như `CHECKLIST_RECONCILE` vẫn giữ, nhưng prose mô tả chuyển sang từ ngữ trực tiếp.

**Tech Stack:** Markdown custom-agent definitions, Python `unittest` regression contracts.

## Global Constraints

- Không đổi FAST_FIX behavior.
- Không đổi bốn artifact WHAT/HOW/WORK/STATE.
- Không đổi stage/status enum đang được orchestrator dùng.
- Không hardcode `.doct/specs/<feature>/` làm path duy nhất.
- Tránh các cụm khó hiểu trong prose như `Hợp đồng không gian đặc tả`, `Hợp đồng checklist`, `canonical state`, `authoritative ledger` khi có thể diễn đạt trực tiếp.

---

### Task 1: Khóa behavior chọn spec path bằng regression test

**Files:**
- Modify: `tests/test_spec_workspace_contract.py`

**Interfaces:**
- Consumes: nội dung `agents/planning-agent.agent.md`, `agents/orchestrator.agent.md`, `README.md`.
- Produces: contract test yêu cầu cả `docs/specs/<feature>/` và `.doct/specs/<feature>/`, cùng quy tắc ưu tiên `docs/`.

- [ ] **Step 1: Viết test thất bại** yêu cầu planning-agent/orchestrator/README mô tả `docs/` tồn tại → `docs/specs/<feature>/`, nếu không → `.doct/specs/<feature>/`, và không còn heading `Hợp đồng không gian đặc tả`/`Hợp đồng checklist`.
- [ ] **Step 2: Chạy test để xác nhận RED** vì agent hiện tại chỉ hardcode `.doct/specs/<feature>/`.
- [ ] **Step 3: Giữ test tối thiểu**, chỉ kiểm behavior/path/language cần thay đổi.

### Task 2: Cập nhật planning-agent và orchestrator

**Files:**
- Modify: `agents/planning-agent.agent.md`
- Modify: `agents/orchestrator.agent.md`

**Interfaces:**
- Consumes: contract test từ Task 1.
- Produces: cùng một quy tắc chọn `Spec path` và prose đơn giản hơn.

- [ ] **Step 1: Sửa planning-agent** để kiểm tra cấu trúc docs trước khi chọn path; đổi heading và diễn đạt checklist sang tiếng Việt trực tiếp.
- [ ] **Step 2: Sửa orchestrator** để LONG_RUNNING dùng spec path do planning-agent chọn, không giả định `.doct/specs/` cố định.
- [ ] **Step 3: Giữ nguyên lifecycle/evidence semantics** của checklist, checkpoint và validation revision.
- [ ] **Step 4: Chạy regression test và xác nhận GREEN**.

### Task 3: Đồng bộ README và regression wording

**Files:**
- Modify: `README.md`
- Modify: `tests/test_spec_workspace_contract.py`

**Interfaces:**
- Consumes: behavior mới từ Task 2.
- Produces: tài liệu người dùng và test cùng mô tả một quy tắc.

- [ ] **Step 1: Cập nhật phần LONG_RUNNING/Spec workspace** trong README với hai vị trí lưu và ví dụ resume dùng `<spec-path>` thay vì `.doct/specs/...` cố định.
- [ ] **Step 2: Loại bỏ các assertion bắt buộc từ ngữ `authoritative` nếu không cần cho behavior**.
- [ ] **Step 3: Chạy test liên quan và full validation khả dụng**.

### Task 4: Review và hoàn tất branch

**Files:**
- Review all files changed on `fix/flexible-spec-path-and-language`.

**Interfaces:**
- Consumes: toàn bộ thay đổi ở Task 1-3.
- Produces: branch/PR có diff hẹp và evidence validation.

- [ ] **Step 1: So sánh diff với `main`** và kiểm không đổi behavior ngoài scope.
- [ ] **Step 2: Chạy validation fresh**.
- [ ] **Step 3: Tạo PR** nêu rõ path-selection rule, language cleanup và validation evidence.

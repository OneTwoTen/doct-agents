# Browser Capability Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cho phép `implementation-agent` tự reproduce, sửa và browser-verify web/UI task trong một worker loop, đồng thời giữ `browser-agent` cho independent validation và `cli-executor` cho final pipeline validation.

**Architecture:** Mở rộng capability của `implementation-agent` bằng `execute` và toàn bộ built-in Browser tools của GitHub Copilot. Cập nhật orchestrator để route browser-driven debugging trực tiếp vào writer khi browser evidence phục vụ chính thay đổi đó; chỉ dùng `browser-agent` khi cần validation độc lập/read-only. Validator được cập nhật có chủ đích để cho phép duy nhất `implementation-agent` và `test-agent` sở hữu cặp `edit+execute`, cùng regression tests bảo vệ ownership mới.

**Tech Stack:** GitHub Copilot custom agent Markdown/frontmatter, Python `unittest`, validator Python hiện có, README Markdown.

## Global Constraints

- `orchestrator` không nhận Browser tools.
- `browser-agent` vẫn read-only, không có `edit`.
- `implementation-agent` chỉ dùng `execute` cho dev-server/runtime loop hẹp; build/lint/typecheck/final integration vẫn thuộc `cli-executor`.
- `runPlaywrightCode` chỉ dùng khi primitive Browser tools không đủ.
- Browser actions phải bám `Scope` và `Expected behavior`; không exploratory testing vô hạn.
- Khi cần session hiện có nhưng tab chưa `Share with Agent`, trả `needs-info` thay vì workaround thủ công.
- Không thay đổi installer/runtime packaging ngoài agent definitions, validator tests và docs cần thiết cho capability mới.

---

### Task 1: Bảo vệ permission model mới bằng regression tests

**Files:**
- Modify: `tests/test_validate_agents.py`

**Interfaces:**
- Consumes: `validate_agents.validate(directory: Path) -> list[str]`, `validate_agents.parse_frontmatter(path: Path) -> dict[str, object]`.
- Produces: regression contract rằng `implementation-agent` được phép có `edit+execute`, sở hữu đầy đủ Browser tools; `browser-agent` vẫn không có `edit`; `orchestrator` vẫn không có Browser tools.

- [ ] **Step 1: Thêm test failing cho allowlist `implementation-agent`**

Thêm test cạnh `test_allows_test_agent_edit_execute_pair`:

```python
def test_allows_implementation_agent_edit_execute_pair(self) -> None:
    errors = self.validate_files(
        {
            "implementation-agent.agent.md": agent_text(
                "implementation-agent", tools=["read", "search", "edit", "execute"]
            )
        }
    )
    self.assertEqual([], errors)
```

- [ ] **Step 2: Thêm repository-level regression test cho browser capability ownership**

Thêm constant tool set trong test method hoặc module:

```python
browser_tools = {
    "openBrowserPage",
    "navigatePage",
    "readPage",
    "screenshotPage",
    "clickElement",
    "hoverElement",
    "dragElement",
    "typeInPage",
    "handleDialog",
    "runPlaywrightCode",
}
```

Và assertions:

```python
def test_repository_browser_capability_ownership(self) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    agents_directory = repository_root / "agents"

    implementation = validate_agents.parse_frontmatter(
        agents_directory / "implementation-agent.agent.md"
    )
    browser = validate_agents.parse_frontmatter(
        agents_directory / "browser-agent.agent.md"
    )
    orchestrator = validate_agents.parse_frontmatter(
        agents_directory / "orchestrator.agent.md"
    )

    browser_tools = {
        "openBrowserPage",
        "navigatePage",
        "readPage",
        "screenshotPage",
        "clickElement",
        "hoverElement",
        "dragElement",
        "typeInPage",
        "handleDialog",
        "runPlaywrightCode",
    }

    self.assertTrue(browser_tools.issubset(set(implementation["tools"])))
    self.assertIn("edit", implementation["tools"])
    self.assertIn("execute", implementation["tools"])

    self.assertTrue(browser_tools.issubset(set(browser["tools"])))
    self.assertNotIn("edit", browser["tools"])

    self.assertTrue(browser_tools.isdisjoint(set(orchestrator["tools"])))
```

- [ ] **Step 3: Chạy focused tests và xác nhận chúng fail trước implementation**

Run:

```bash
python -m unittest tests.test_validate_agents.ValidateAgentsTest.test_allows_implementation_agent_edit_execute_pair tests.test_validate_agents.ValidateAgentsTest.test_repository_browser_capability_ownership -v
```

Expected: FAIL vì `implementation-agent` chưa được allowlist `edit+execute` và chưa có Browser tools.

- [ ] **Step 4: Commit regression tests**

```bash
git add tests/test_validate_agents.py
git commit -m "test: define browser capability ownership"
```

---

### Task 2: Mở browser-driven implementation loop và cập nhật routing

**Files:**
- Modify: `scripts/validate_agents.py`
- Modify: `agents/implementation-agent.agent.md`
- Modify: `agents/browser-agent.agent.md`
- Modify: `agents/orchestrator.agent.md`

**Interfaces:**
- Consumes: acceptance criteria trong `docs/superpowers/specs/2026-08-04-browser-capability-loop-design.md`.
- Produces: `implementation-agent` có `read/search/edit/execute` + 10 Browser tools; `browser-agent` là independent validator; orchestrator route writer trực tiếp cho browser-driven fix.

- [ ] **Step 1: Mở validator allowlist tối thiểu**

Đổi:

```python
EDIT_EXECUTE_ALLOWLIST = {"test-agent"}
```

thành:

```python
EDIT_EXECUTE_ALLOWLIST = {"implementation-agent", "test-agent"}
```

Không thêm agent khác.

- [ ] **Step 2: Thêm Browser tools và `execute` vào `implementation-agent` frontmatter**

Tool list phải là:

```yaml
tools: ["read", "search", "edit", "execute", "openBrowserPage", "navigatePage", "readPage", "screenshotPage", "clickElement", "hoverElement", "dragElement", "typeInPage", "handleDialog", "runPlaywrightCode"]
```

- [ ] **Step 3: Thay command ownership tuyệt đối bằng runtime-loop ownership hẹp**

Trong `implementation-agent`, thay rule `Không chạy command` bằng contract:

```markdown
- Chỉ dùng `execute` để start/restart/inspect dev server hoặc runtime command hẹp cần trực tiếp cho reproduce/verify trong task hiện tại; ghi command/cwd/URL/port vào Validation.
- Không dùng `execute` cho build, lint, typecheck, full test suite hoặc final integration validation; các command đó vẫn thuộc `cli-executor`, ngoại trừ test mới thuộc `test-agent`.
```

- [ ] **Step 4: Thêm browser-driven loop vào `implementation-agent`**

Thêm section `## Browser-driven implementation` với rules:

```markdown
- Khi Scope liên quan web/UI hoặc runtime behavior cần browser evidence, ưu tiên một loop liền mạch: đọc source/call site -> reproduce bằng Browser tools -> edit -> `readPage`/`navigatePage` -> verify.
- Sau `openBrowserPage` hoặc `navigatePage`, dùng `readPage` để xác nhận URL/state trước interaction.
- Dùng click/type/hover/drag/dialog primitives trước; chỉ dùng `runPlaywrightCode` khi primitives không đủ cho assertion lặp, nhiều viewport hoặc selector có điều kiện.
- Chụp `screenshotPage` ở lỗi quan trọng hoặc evidence cuối khi hình ảnh có giá trị xác minh.
- Không dùng browser ngoài Scope, không thao tác production data/login profile cá nhân khi chưa được phép.
- Nếu cần session hiện có nhưng tab chưa `Share with Agent`, trả `needs-info`.
```

Cập nhật `Validation` output contract để bao gồm browser/runtime evidence thực sự đã chạy.

- [ ] **Step 5: Làm rõ `browser-agent` là independent validation**

Cập nhật description/body để nêu rõ worker này dùng cho `independent browser validation`, reproduction-only, regression/responsive flow và evidence độc lập. Giữ nguyên tool set, `agents: []`, `user-invocable: false`, không thêm `edit`.

- [ ] **Step 6: Cập nhật orchestrator routing**

Trong `FAST_FIX`/Validation ownership hoặc section riêng, thêm các rule tương đương:

```markdown
- Với web/UI fix cần browser evidence để reproduce hoặc kiểm tra thay đổi, handoff trực tiếp cho `implementation-agent` với URL/flow/expected browser behavior trong Scope; không chèn `browser-agent` như gateway bắt buộc.
- `browser-agent` chỉ được gọi khi task là `BROWSER_VALIDATION`, reproduction-only, regression/responsive check, hoặc cần independent verification tách khỏi writer.
- Browser runtime evidence do `implementation-agent` tạo được tái sử dụng như fresh validation evidence; chỉ gọi `browser-agent` lại khi acceptance criteria yêu cầu independent verification hoặc evidence hiện có chưa đủ.
```

Giữ `orchestrator.tools` nguyên trạng, không thêm Browser tools.

- [ ] **Step 7: Chạy focused regression tests**

Run:

```bash
python -m unittest tests.test_validate_agents.ValidateAgentsTest.test_allows_implementation_agent_edit_execute_pair tests.test_validate_agents.ValidateAgentsTest.test_repository_browser_capability_ownership -v
```

Expected: PASS.

- [ ] **Step 8: Chạy validator toàn bộ agent definitions**

Run:

```bash
python scripts/validate_agents.py agents
```

Expected: exit 0 và `Validated ... agent definitions successfully.`

- [ ] **Step 9: Commit capability/routing changes**

```bash
git add scripts/validate_agents.py agents/implementation-agent.agent.md agents/browser-agent.agent.md agents/orchestrator.agent.md
git commit -m "feat: enable browser-driven implementation loop"
```

---

### Task 3: Đồng bộ README và chạy validation tổng

**Files:**
- Modify: `README.md`
- Test: `tests/test_validate_agents.py`

**Interfaces:**
- Consumes: agent behavior sau Task 2.
- Produces: user-facing docs mô tả đúng hybrid model và fresh validation evidence cho toàn repository test surface liên quan.

- [ ] **Step 1: Cập nhật phần workflow trong README**

Ở phần `FAST_FIX`/browser usage, thêm mô tả ngắn:

```markdown
Với web/UI fix, `implementation-agent` có thể dùng trực tiếp built-in Browser tools và runtime command hẹp để reproduce -> sửa -> browser verify trong cùng worker loop. `browser-agent` được giữ cho kiểm tra browser độc lập/read-only như reproduction-only, regression, responsive hoặc independent verification; nó không còn là gateway bắt buộc cho mọi browser action. Build/lint/typecheck/final integration vẫn thuộc `cli-executor`.
```

Không mở rộng README sang OpenCode/MCP trong PR này.

- [ ] **Step 2: Chạy toàn bộ validator unit tests**

Run:

```bash
python -m unittest tests.test_validate_agents -v
```

Expected: PASS toàn bộ test.

- [ ] **Step 3: Chạy repository agent validator lần cuối**

Run:

```bash
python scripts/validate_agents.py agents
```

Expected: exit 0.

- [ ] **Step 4: Kiểm tra diff không làm tăng quyền ngoài thiết kế**

Run:

```bash
git diff main...HEAD -- agents scripts/validate_agents.py tests/test_validate_agents.py README.md
```

Expected:
- Browser tools chỉ được thêm cho `implementation-agent`; `orchestrator` không có Browser tools.
- `browser-agent` không có `edit`.
- `EDIT_EXECUTE_ALLOWLIST` chỉ thêm `implementation-agent` ngoài `test-agent` hiện có.
- README khớp hybrid ownership.

- [ ] **Step 5: Commit docs**

```bash
git add README.md
git commit -m "docs: explain hybrid browser workflow"
```

- [ ] **Step 6: Chuẩn bị PR**

PR base: `main`.

Title:

```text
feat: enable browser-driven implementation loop
```

Body phải nêu:
- `implementation-agent` có Browser tools + runtime `execute` hẹp.
- `browser-agent` vẫn read-only cho independent validation.
- orchestrator tránh browser-agent gateway trong normal web/UI fix.
- validator regression tests bảo vệ permission boundaries.
- validation commands và kết quả thực tế.

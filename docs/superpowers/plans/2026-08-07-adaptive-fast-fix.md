# Adaptive FAST_FIX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Làm FAST_FIX adaptive để task nhỏ mặc định đi direct path với ít worker/handoff hơn, nhưng vẫn tăng validation theo risk và escalate sang LONG_RUNNING khi discovery cho thấy scope không còn bounded.

**Architecture:** Giữ `FAST_FIX` và `LONG_RUNNING` là hai lifecycle cấp cao. Bổ sung `direct`/`guarded` execution strategy bên trong FAST_FIX, nới input contract của `implementation-agent` cho FAST_FIX, và khóa behavior bằng repository contract tests thay vì thêm logic runtime mới.

**Tech Stack:** Markdown custom agents, Python 3.9 `unittest`, repository validator, npm validation scripts.

## Global Constraints

- Không thêm workflow `SMALL/MEDIUM/LARGE` mới.
- Production code change vẫn bắt buộc qua `implementation-agent`.
- Planning-agent không được dùng trong FAST_FIX.
- Validation depth phụ thuộc risk, không phụ thuộc số dòng diff.
- Giữ validation ownership/fresh evidence rules hiện có.
- Giữ browser-driven implementation behavior hiện có.
- Không thêm dependency runtime mới.

---

### Task 1: Define adaptive FAST_FIX contract tests

**Files:**
- Modify: `tests/test_validate_agents.py`
- Read: `agents/orchestrator.agent.md`
- Read: `agents/implementation-agent.agent.md`

**Interfaces:**
- Consumes: repository prompt text and existing `validate_agents.parse_frontmatter` test helpers.
- Produces: regression contract for FAST_FIX direct/guarded routing, escalation, worker defaults and relaxed FAST_FIX validation-plan requirement.

- [ ] **Step 1: Add a failing repository contract test**

Add a test similar to:

```python
def test_repository_supports_adaptive_fast_fix(self) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    agents_directory = repository_root / "agents"
    orchestrator_text = (agents_directory / "orchestrator.agent.md").read_text(
        encoding="utf-8"
    )
    implementation_text = (
        agents_directory / "implementation-agent.agent.md"
    ).read_text(encoding="utf-8")

    self.assertIn("FAST_FIX direct", orchestrator_text)
    self.assertIn("FAST_FIX guarded", orchestrator_text)
    self.assertIn("mặc định không gọi `review-agent`", orchestrator_text)
    self.assertIn("chuyển sang `LONG_RUNNING`", orchestrator_text)
    self.assertIn("Validation plan chỉ bắt buộc", implementation_text)
    self.assertIn("LONG_RUNNING", implementation_text)
```

Also assert the direct path text does not route through planning-agent and that FAST_FIX worker budget is explicitly lower than the old generic four-worker default.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python -m unittest tests.test_validate_agents.ValidateAgentsTest.test_repository_supports_adaptive_fast_fix -v
```

Expected: FAIL because the current prompts do not contain the new direct/guarded and escalation contracts.

- [ ] **Step 3: Commit the failing contract**

```bash
git add tests/test_validate_agents.py
git commit -m "test: define adaptive fast fix contract"
```

---

### Task 2: Implement adaptive FAST_FIX routing and handoff

**Files:**
- Modify: `agents/orchestrator.agent.md`
- Modify: `agents/implementation-agent.agent.md`
- Test: `tests/test_validate_agents.py`

**Interfaces:**
- Consumes: FAST_FIX contract from Task 1 and existing worker ownership rules.
- Produces: explicit direct/guarded execution strategies, escalation criteria, optional risk-driven workers, smaller default worker budget, and FAST_FIX-specific implementation preconditions.

- [ ] **Step 1: Replace the current FAST_FIX state machine with adaptive execution text**

Use this semantic structure in `orchestrator.agent.md`:

```text
FAST_FIX direct: DISCOVER -> IMPLEMENT -> VALIDATE -> FINALIZE
FAST_FIX guarded: DISCOVER -> IMPLEMENT -> optional TEST/REVIEW/DOMAIN -> VALIDATE -> FINALIZE
```

State that direct is the default when behavior/scope are clear and no migration, compatibility, dependency-selection, security, concurrency or data-integrity risk is discovered.

- [ ] **Step 2: Add explicit escalation criteria**

Document that FAST_FIX must switch to `LONG_RUNNING` when discovery finds dependent phases, migration/rollback, compatibility contract, significant cross-module coordination, unresolved architecture decision, or validation that cannot fit a bounded loop.

- [ ] **Step 3: Make worker calls risk/evidence-driven**

Add explicit rules:

```text
review-agent: not default; only independent review when risk/evidence requires it
test-agent: only when test artifacts need to be added/changed
docs-agent: only when docs impact is required
cli-executor: only validation it owns and only when fresh equivalent evidence is absent
```

Keep `implementation-agent` mandatory for production code changes.

- [ ] **Step 4: Reduce FAST_FIX default worker budget**

Set direct to at most two workers total by default; guarded to at most three workers normally, with a fourth only for clear domain risk. Parallel workers default to one and are only used for genuinely independent scopes.

- [ ] **Step 5: Relax implementation-agent preconditions only for FAST_FIX**

Change the precondition contract so FAST_FIX requires `Objective`, `Scope`, `Expected behavior`; `Validation plan` is required only when validation is not obvious or a concrete acceptance/command constraint must be passed. Keep LONG_RUNNING validation plan and milestone/spec/file ownership requirements mandatory.

- [ ] **Step 6: Run the focused contract test and validator**

Run:

```bash
python -m unittest tests.test_validate_agents.ValidateAgentsTest.test_repository_supports_adaptive_fast_fix -v
python scripts/validate_agents.py agents
```

Expected: PASS.

- [ ] **Step 7: Commit implementation**

```bash
git add agents/orchestrator.agent.md agents/implementation-agent.agent.md
git commit -m "refactor: make fast fix adaptive"
```

---

### Task 3: Document and verify the workflow

**Files:**
- Modify: `README.md`
- Modify: `docs/token-metrics.md`
- Test: `tests/test_validate_agents.py`

**Interfaces:**
- Consumes: implemented FAST_FIX direct/guarded contract.
- Produces: user-facing workflow description and measurable runtime targets.

- [ ] **Step 1: Update README FAST_FIX section**

Replace the single fixed FAST_FIX chain with direct and guarded examples. Explain that task size selects FAST_FIX/LONG_RUNNING while risk selects validation depth, and that discovery can escalate to LONG_RUNNING.

- [ ] **Step 2: Add runtime benchmark targets**

In `docs/token-metrics.md`, add FAST_FIX direct targets:

```text
planning-agent calls = 0
review-agent default = 0
docs-agent default = 0
median worker count <= 2
duplicate validation signature = 0
change/validate loops = 1 normally
```

Keep the existing recommendation to measure at least five sessions and compare medians.

- [ ] **Step 3: Run repository tests**

Run:

```bash
python -m unittest tests.test_validate_agents -v
npm run check
```

Expected: all tests and repository validation pass.

- [ ] **Step 4: Review prompt-size budget and diff scope**

Confirm `orchestrator.agent.md` remains below its 12,000-character prompt body budget and worker prompts remain below their applicable budget. Confirm no unrelated agent contract changed.

- [ ] **Step 5: Commit documentation and verification state**

```bash
git add README.md docs/token-metrics.md docs/superpowers/specs/2026-08-07-adaptive-fast-fix-design.md docs/superpowers/plans/2026-08-07-adaptive-fast-fix.md
git commit -m "docs: describe adaptive fast fix workflow"
```

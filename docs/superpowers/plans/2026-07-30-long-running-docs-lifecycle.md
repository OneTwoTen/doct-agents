# Long-Running Workflow and Documentation Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm workflow dài hơi có roadmap/milestone/checkpoint, deliberation qua orchestrator và documentation impact lifecycle chỉ cập nhật tài liệu liên quan.

**Architecture:** Orchestrator tiếp tục là router duy nhất. `architecture-agent` tạo proposal/challenge, `planning-agent` tạo và duy trì plan bền vững, còn các worker implementation/review/docs hoạt động theo milestone contract. Validator và regression tests bảo vệ các invariant routing, least privilege và docs-impact gate.

**Tech Stack:** VS Code custom agent Markdown, Python 3.11 standard library, Node.js 18+, GitHub Actions.

## Global Constraints

- Không cho worker tự gọi worker ngang hàng; chỉ `orchestrator` được có subagent references.
- Không cập nhật tài liệu tràn lan; luôn assess impact và chỉ sửa tài liệu có evidence liên quan.
- `FAST_FIX` phải giữ hoạt động hiện có.
- `LONG_RUNNING` mặc định tự động cao, chỉ hỏi người dùng khi blocked theo policy.
- Tối đa 6 milestone mỗi plan; lớn hơn phải chia phase.
- Không thêm dependency runtime mới.
- Không cấp đồng thời `edit` và `execute` ngoài allowlist hiện có.
- Mọi thay đổi phải có regression test và validation hẹp nhất liên quan.

---

### Task 1: Add failing repository contract tests

**Files:**
- Modify: `tests/test_validate_agents.py`
- Modify: `scripts/validate_agents.py`

**Interfaces:**
- Consumes: `validate_agents.validate(directory) -> list[str]` và repository agent files.
- Produces: regression tests cho long-running routing, planning, docs lifecycle và router-only handoff policy.

- [ ] **Step 1: Add a failing test for router-only subagent ownership**

Thêm test tạo `orchestrator` hợp lệ và một worker có `agent` + `agents=["peer"]`, sau đó assert validator trả lỗi chứa:

```text
only orchestrator may reference subagents
```

- [ ] **Step 2: Add a failing repository contract test**

Test phải assert:

```python
architecture_path.exists()
planning_path.exists()
"architecture-agent" in orchestrator["agents"]
"planning-agent" in orchestrator["agents"]
"LONG_RUNNING" in orchestrator_text
"DOCS_IMPACT" in orchestrator_text
"impact-update" in docs_text
"Docs impact candidates" in implementation_text
"milestone" in review_text
"final" in review_text
```

- [ ] **Step 3: Run CI on the test-only commit**

Expected: Python test step fails because new agents/routing/policy do not exist yet.

- [ ] **Step 4: Commit**

```bash
git add tests/test_validate_agents.py scripts/validate_agents.py
git commit -m "test: define long-running orchestration contracts"
```

### Task 2: Enforce orchestrator-only handoff policy

**Files:**
- Modify: `scripts/validate_agents.py`
- Test: `tests/test_validate_agents.py`

**Interfaces:**
- Consumes: parsed `Agent` records.
- Produces: validation error when any non-orchestrator agent has non-empty `agents` or uses `agent` for peer handoff.

- [ ] **Step 1: Define the router allowlist**

Add:

```python
SUBAGENT_ROUTER_ALLOWLIST = {"orchestrator"}
```

- [ ] **Step 2: Implement minimal validation**

Inside the per-agent validation loop:

```python
if agent.name not in SUBAGENT_ROUTER_ALLOWLIST and (
    agent.agents or "agent" in agent.tools
):
    errors.append(
        f"{agent.path}: only orchestrator may reference subagents"
    )
```

Keep existing unknown-reference and tool/reference consistency checks.

- [ ] **Step 3: Run Python tests**

Run:

```bash
python -m unittest discover -s tests -v
```

Expected: router-policy test passes; repository contract test still fails because new agent files are absent.

- [ ] **Step 4: Commit**

```bash
git add scripts/validate_agents.py tests/test_validate_agents.py
git commit -m "feat: restrict subagent routing to orchestrator"
```

### Task 3: Add architecture and planning agents

**Files:**
- Create: `agents/architecture-agent.agent.md`
- Create: `agents/planning-agent.agent.md`

**Interfaces:**
- `architecture-agent` consumes requirements/proposal context and produces `Options`, `Assumptions`, `Risks`, `Recommendation`, `Validation`, `Next`.
- `planning-agent` consumes requirements, architecture decisions and challenge results; produces/updates `docs/superpowers/plans/YYYY-MM-DD-<feature>-implementation.md`.

- [ ] **Step 1: Create architecture-agent**

Frontmatter:

```yaml
---
name: architecture-agent
description: "Dùng cho yêu cầu dài hơi cần đề xuất hoặc phản biện kiến trúc, dependency, migration, rollback và trade-off trước khi lập kế hoạch triển khai."
argument-hint: "mode proposal hoặc challenge, requirements, constraints, proposal hiện có"
tools: ["read", "search"]
agents: []
user-invocable: false
---
```

Body phải định nghĩa `proposal` và `challenge`, giới hạn tối đa ba options, không edit, không handoff, ưu tiên evidence trong repo.

- [ ] **Step 2: Create planning-agent**

Frontmatter:

```yaml
---
name: planning-agent
description: "Dùng để tổng hợp requirements và quyết định thiết kế thành roadmap, milestone, checkpoint và implementation plan bền vững cho yêu cầu dài hơi."
argument-hint: "requirements, design decisions, challenges, scope, validation constraints"
tools: ["read", "search", "edit"]
agents: []
user-invocable: false
---
```

Body phải yêu cầu plan gồm Goal, Non-goals, Assumptions, Architecture decisions, Milestones, Dependencies, File ownership, Acceptance criteria, Validation commands, Docs impact candidates, Risks, Rollback strategy, Definition of done và Progress checkpoint.

- [ ] **Step 3: Run repository validator**

Run:

```bash
python scripts/validate_agents.py
```

Expected: agent definitions valid; repository contract test vẫn fail cho tới khi orchestrator tham chiếu agent mới.

- [ ] **Step 4: Commit**

```bash
git add agents/architecture-agent.agent.md agents/planning-agent.agent.md
git commit -m "feat: add architecture and planning agents"
```

### Task 4: Add LONG_RUNNING orchestration and deliberation

**Files:**
- Modify: `agents/orchestrator.agent.md`

**Interfaces:**
- Consumes: `req-extractor`, `architecture-agent`, `planning-agent`, implementation/review/docs workers.
- Produces: `LONG_RUNNING` state machine, autonomous blocker policy, deliberation protocol, milestone execution and checkpoint lifecycle.

- [ ] **Step 1: Add new agents to frontmatter**

Add `architecture-agent` and `planning-agent` to the orchestrator `agents` list.

- [ ] **Step 2: Add LONG_RUNNING routing criteria**

Document exact signals: 3+ modules/domains, multiple dependent phases, migration/rollout/backward compatibility, roadmap requirement, or more than one safe change-validation cycle.

- [ ] **Step 3: Add state machine**

Use exactly:

```text
DISCOVER -> REQUIREMENTS -> DELIBERATE -> DESIGN -> PLAN -> MILESTONE_LOOP -> FINAL_REVIEW -> FINALIZE
```

Inside `MILESTONE_LOOP` require:

```text
IMPLEMENT -> REVIEW -> VALIDATE -> DOCS_IMPACT -> CHECKPOINT
```

- [ ] **Step 4: Add deliberation protocol**

Specify three orchestrator-mediated rounds: independent analysis, challenge, synthesis. Limit to three analysis workers, one extra challenge round and no worker-to-worker handoff.

- [ ] **Step 5: Add autonomous blocker policy and budgets**

Include the exact six-milestone limit, fix-review limits, roadmap revisions and stop conditions from the design spec.

- [ ] **Step 6: Add docs impact gate**

Require an assessment after each code-changing milestone with:

```text
Status: required | not-required | uncertain
Changed behavior
Affected audience
Candidate docs
Evidence
Recommended updates
```

Only handoff to `docs-agent` when `required`, or read-first evaluation when `uncertain`.

- [ ] **Step 7: Run repository contract tests**

Run:

```bash
python -m unittest tests.test_validate_agents.ValidateAgentsTest.test_repository_supports_long_running_workflow -v
```

Expected: remaining failures identify worker contracts not yet updated.

- [ ] **Step 8: Commit**

```bash
git add agents/orchestrator.agent.md
git commit -m "feat: add long-running orchestration workflow"
```

### Task 5: Extend requirement, implementation and review contracts

**Files:**
- Modify: `agents/req-extractor.agent.md`
- Modify: `agents/implementation-agent.agent.md`
- Modify: `agents/review-agent.agent.md`

**Interfaces:**
- `req-extractor` produces long-running decomposition input.
- `implementation-agent` produces docs impact candidates.
- `review-agent` accepts `qa | quality | milestone | final` modes.

- [ ] **Step 1: Extend req-extractor output**

Add Goal, Non-goals, Requirements, Constraints, Assumptions, Open questions, Acceptance criteria, Dependency candidates, Milestone candidates and Long-running signal.

- [ ] **Step 2: Extend implementation result contract**

Add:

```text
Docs impact candidates: changed behavior, affected audience, candidate docs and evidence
```

Require `none` with reason when no candidate exists.

- [ ] **Step 3: Extend review modes**

Add:

```text
milestone: compare milestone diff with acceptance criteria, validation evidence and docs-impact result
final: review cross-milestone integration, unresolved risks and definition of done
```

Do not grant edit or agent tools.

- [ ] **Step 4: Commit**

```bash
git add agents/req-extractor.agent.md agents/implementation-agent.agent.md agents/review-agent.agent.md
git commit -m "feat: extend long-running worker contracts"
```

### Task 6: Add documentation impact modes

**Files:**
- Modify: `agents/docs-agent.agent.md`

**Interfaces:**
- Consumes: mode `author | impact-update`, validated behavior, affected audience, candidate docs and evidence.
- Produces: `Impact reviewed`, `Docs checked`, `Docs changed`, `Docs unchanged`, `Validation`, `Next`.

- [ ] **Step 1: Add mode section**

Define `author` and `impact-update`.

- [ ] **Step 2: Add impact-update workflow**

Require search/read of candidate docs, comparison against validated behavior, minimal section edits, no README rewrite by default and no new doc when an existing doc is appropriate.

- [ ] **Step 3: Add no-impact behavior**

When no documentation change is required, return checked files and evidence; do not edit files merely to produce output.

- [ ] **Step 4: Run repository contract test**

Run:

```bash
python -m unittest tests.test_validate_agents.ValidateAgentsTest.test_repository_supports_long_running_workflow -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add agents/docs-agent.agent.md
git commit -m "feat: add documentation impact lifecycle"
```

### Task 7: Update package documentation and version

**Files:**
- Modify: `README.md`
- Modify: `package.json`

**Interfaces:**
- Produces: user-facing guidance for FAST_FIX, LONG_RUNNING, checkpoint resume and docs impact; npm version `0.2.0`.

- [ ] **Step 1: Add workflow guidance to README**

Document:

- when FAST_FIX is used;
- when LONG_RUNNING is used;
- roadmap/milestone/checkpoint lifecycle;
- orchestrator-mediated agent deliberation;
- documentation impact behavior;
- example long-running prompt;
- how to resume from the plan file in a new chat.

- [ ] **Step 2: Bump package version**

Change:

```json
"version": "0.2.0"
```

This is a minor release because it adds new agent capabilities without removing existing commands.

- [ ] **Step 3: Commit**

```bash
git add README.md package.json
git commit -m "docs: document long-running agent workflows"
```

### Task 8: Full verification and PR

**Files:**
- Verify all changed files.

**Interfaces:**
- Produces: evidence that tests, validator and package contents pass.

- [ ] **Step 1: Run Node CLI tests**

```bash
npm test
```

Expected: all tests pass.

- [ ] **Step 2: Run Python tests**

```bash
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 3: Run agent validator**

```bash
python scripts/validate_agents.py
```

Expected: all agent definitions valid.

- [ ] **Step 4: Verify package contents**

```bash
npm pack --dry-run
```

Expected: package includes `architecture-agent.agent.md` and `planning-agent.agent.md`.

- [ ] **Step 5: Review diff against design definition of done**

Confirm no worker has peer subagent references, docs are only updated where behavior is user-facing, and FAST_FIX rules remain present.

- [ ] **Step 6: Open pull request**

PR body must include root cause/current gap, design summary, milestone lifecycle, docs impact behavior, validation evidence and release note for `0.2.0`.

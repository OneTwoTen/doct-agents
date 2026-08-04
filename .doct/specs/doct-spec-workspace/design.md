# Doct Spec Workspace Design

Status: approved

## Architecture

LONG_RUNNING dùng một canonical workspace do doct-agents sở hữu:

```text
.doct/
├── project.md
├── features/
│   ├── index.md
│   └── <feature>.md
└── specs/
    └── <feature>/
        ├── requirements.md
        ├── design.md
        ├── tasks.md
        └── progress.md
```

## Artifact ownership

- `requirements.md`: WHAT — goal, non-goals, requirements, constraints, acceptance criteria.
- `design.md`: HOW — architecture, decisions, interfaces, migration/rollback, risks, validation strategy.
- `tasks.md`: WORK — milestone/task graph, dependencies, file ownership, validation plan và definition of done.
- `progress.md`: STATE — completed/current work, validation evidence, blockers, docs impact, feature impact, next work.
- `.doct/features/index.md`: project capability catalog.
- `.doct/features/<feature>.md`: current-state truth của capability, được tổng hợp từ một hoặc nhiều completed specs.
- `.doct/project.md`: compact project view cho agent mới vào repo.

## LONG_RUNNING lifecycle

```text
DISCOVER
-> REQUIREMENTS
-> REQUIREMENTS_REVIEW
-> DELIBERATE
-> DESIGN
-> DESIGN_REVIEW
-> PLAN
-> SELECT_EXECUTOR
-> MILESTONE_LOOP
   -> PREPARE_MILESTONE
   -> IMPLEMENT
   -> REVIEW
   -> VALIDATE
   -> DOCS_IMPACT
   -> CHECKPOINT
-> FINAL_REVIEW
-> FINAL_VALIDATE
-> FEATURE_IMPACT
-> UPDATE_FEATURE_REGISTRY
-> FINALIZE
```

Human gate chỉ dùng khi ambiguity tạo nhiều behavior hợp lệ, destructive migration, security/compliance decision hoặc architecture conflict không thể tự adjudicate.

## Executor boundary

Orchestrator và canonical spec sở hữu lifecycle, acceptance criteria, review budget và checkpoint. Executor chỉ sở hữu worktree/task dispatch/model/local execution mechanics. Superpowers/OpenCode/native executor phải trả milestone result về cùng orchestrator contract.

## Feature impact

Mỗi code-changing milestone ghi feature-impact candidates vào `progress.md`. Final stage aggregate thành:

- Added capabilities
- Changed capabilities
- Removed capabilities
- Deferred/not implemented
- Related specs

Nếu capability thay đổi, update `.doct/features/index.md` và feature record tương ứng. Documentation impact và feature impact là hai gate độc lập.

## Status vocabularies

Spec: `draft | approved | implementing | completed | blocked | superseded`.
Feature: `planned | in-progress | experimental | stable | deprecated | removed`.

## Compatibility

FAST_FIX giữ nguyên workflow hiện tại. Các plan lịch sử trong `docs/superpowers/` không cần migrate; chỉ LONG_RUNNING mới tạo artifact theo contract mới.

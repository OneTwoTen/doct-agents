# Thiết kế Doct Spec Workspace

Status: implementing

## Kiến trúc

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

## Ownership của artifact

- `requirements.md`: WHAT — mục tiêu, ngoài phạm vi, yêu cầu, ràng buộc và Acceptance criteria.
- `design.md`: HOW — kiến trúc, quyết định, interface, migration/rollback, rủi ro và Validation strategy.
- `tasks.md`: WORK — milestone/task graph, dependency, file ownership, Validation plan, Definition of done và authoritative checklist.
- `progress.md`: STATE — vị trí hiện tại, validation evidence, blocker/deferred, docs impact, feature impact và next work; không sao chép checklist.
- `.doct/features/index.md`: catalog capability hiện tại của project.
- `.doct/features/<feature>.md`: current-state truth của capability, tổng hợp từ một hoặc nhiều spec đã được kiểm chứng.
- `.doct/project.md`: project/architecture overview tương đối tĩnh cho agent mới vào repo; không duplicate capability catalog.

## Lifecycle LONG_RUNNING

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
   -> CHECKLIST_RECONCILE
   -> CHECKPOINT
-> FINAL_REVIEW
-> FINAL_VALIDATE
-> FEATURE_IMPACT
-> UPDATE_FEATURE_REGISTRY
-> FINALIZE
```

Human gate chỉ dùng khi ambiguity tạo nhiều behavior hợp lệ, destructive migration, security/compliance decision hoặc architecture conflict không thể tự adjudicate.

## Ranh giới executor

Orchestrator và canonical spec sở hữu lifecycle, Acceptance criteria, checklist completion, review budget, validation và checkpoint. Executor chỉ sở hữu worktree, task dispatch, model/local execution mechanics. Superpowers, OpenCode và native executor phải trả kết quả về cùng orchestrator contract.

## Checklist và checkpoint

- `tasks.md` là authoritative execution ledger với stable task ID và Markdown checkbox.
- Chỉ `CHECKLIST_RECONCILE` mới cho phép đổi `[ ] -> [x]`, dựa trên implementation evidence + fresh required validation + review state.
- Blocked/deferred giữ `[ ]`; nếu evidence mất hiệu lực phải cho phép downgrade `[x] -> [ ]`.
- `progress.md` chỉ là journal/evidence cho current item, completed references, blocker/deferred và next work.
- `CHECKPOINT` chỉ được tạo sau checklist reconciliation.
- Trước `FINALIZE`, final reconciliation phải đối chiếu requirements/design/tasks/progress/feature registry với implementation và validation revision cuối.

## Feature impact

Mỗi code-changing milestone ghi `Feature impact candidates` vào `progress.md`. Final stage tổng hợp thành Added, Changed, Removed, Deferred capabilities và Related specs.

Nếu capability thay đổi, cập nhật `.doct/features/index.md` và feature record tương ứng. Documentation impact và feature impact là hai gate độc lập.

## Status vocabularies

Spec: `draft | approved | implementing | completed | blocked | superseded`.
Feature: `planned | in-progress | experimental | stable | deprecated | removed`.

## Tương thích

FAST_FIX giữ nguyên workflow. Browser-driven implementation loop mới trên `main` phải được giữ nguyên khi LONG_RUNNING thay đổi. Các plan lịch sử trong `docs/superpowers/` được giữ làm lịch sử; chỉ LONG_RUNNING mới tạo artifact theo contract mới.

# Long-Running Workflow and Documentation Lifecycle Design

## Goal

Mở rộng `doct-agents` để xử lý yêu cầu dài hơi theo roadmap và milestone rõ ràng, cho phép nhiều agent phân tích và phản biện thông qua orchestrator, đồng thời chỉ cập nhật tài liệu khi thay đổi code thực sự tác động đến tài liệu liên quan.

## Non-goals

- Không cho worker tự gọi trực tiếp worker ngang hàng.
- Không tự động sửa mọi tài liệu sau mỗi code change.
- Không biến task nhỏ thành quy trình nhiều phase.
- Không thêm dependency runtime mới.
- Không tạo cơ chế lưu trạng thái ngoài file Markdown trong repository.

## Core principles

1. Orchestrator là thành phần duy nhất sở hữu routing, state transition, execution budget và quyết định handoff.
2. Worker phân tích độc lập, trả kết quả có cấu trúc và không tự mở rộng scope.
3. Yêu cầu dài hơi luôn có roadmap, milestone, dependency, validation plan và definition of done.
4. Sau mỗi milestone có code change, orchestrator luôn thực hiện docs impact assessment.
5. Chỉ gọi `docs-agent` khi docs impact là `required`; khi `not-required`, phải ghi evidence ngắn gọn thay vì sửa tài liệu cho đủ thủ tục.
6. Chế độ mặc định là tự động cao: chỉ hỏi người dùng khi thật sự blocked, có thao tác phá hủy, thiếu credential, scope drift lớn hoặc có ambiguity ảnh hưởng trực tiếp đến behavior.

## Workflow routing

### FAST_FIX

Giữ workflow hiện có cho lỗi cục bộ, refactor nhỏ, thay đổi test hoặc thay đổi production trong một phạm vi hẹp.

### LONG_RUNNING

Chọn khi có một hoặc nhiều dấu hiệu:

- từ ba module hoặc domain trở lên;
- nhiều feature hoặc nhiều phase phụ thuộc nhau;
- cần design, migration, rollout hoặc backward compatibility;
- cần roadmap hoặc implementation plan bền vững;
- không thể hoàn thành an toàn trong một vòng `change -> validate`;
- yêu cầu có nhiều nhóm file độc lập hoặc nhiều chuyên môn cần phản biện.

State machine:

```text
DISCOVER
→ REQUIREMENTS
→ DELIBERATE
→ DESIGN
→ PLAN
→ MILESTONE_LOOP
    → IMPLEMENT
    → REVIEW
    → VALIDATE
    → DOCS_IMPACT
    → CHECKPOINT
→ FINAL_REVIEW
→ FINALIZE
```

## Agent roles

### req-extractor

Trích xuất goal, non-goals, requirements, constraints, assumptions, open questions, acceptance criteria, dependency candidates và milestone candidates. Không tạo implementation plan cuối cùng.

### architecture-agent

Có hai mode:

- `proposal`: đề xuất tối đa ba hướng thiết kế, trade-off, dependency, migration/rollback và recommendation.
- `challenge`: phản biện một proposal đã có, tìm assumption yếu, failure mode, coupling, validation gap và phương án đơn giản hơn.

Agent này read-only và không tự handoff.

### planning-agent

Tổng hợp requirements, design decisions và challenge results thành plan bền vững tại:

```text
docs/superpowers/plans/YYYY-MM-DD-<feature>-implementation.md
```

Plan phải có:

- Goal và non-goals;
- assumptions và architecture decisions;
- milestones theo dependency order;
- file ownership và phạm vi được phép sửa;
- acceptance criteria;
- validation commands;
- docs impact candidates;
- risk và rollback strategy;
- definition of done;
- progress checkpoint có thể dùng để tiếp tục trong chat mới.

### implementation-agent

Triển khai đúng một milestone hoặc một file set không xung đột. Kết quả phải bổ sung `Docs impact candidates` để orchestrator đánh giá sau validation.

### review-agent

Hỗ trợ thêm hai mode:

- `milestone`: review diff và acceptance criteria của milestone vừa hoàn thành.
- `final`: review cross-milestone, integration risk và definition of done.

Agent vẫn read-only và không sửa code.

### docs-agent

Có hai mode:

- `author`: task thuần tài liệu như hiện tại.
- `impact-update`: nhận behavior đã validate và docs impact map, tìm đúng tài liệu bị ảnh hưởng, sửa tối thiểu và liệt kê tài liệu đã kiểm tra nhưng không cần sửa.

## Deliberation protocol

Worker không nói chuyện trực tiếp với nhau. Orchestrator điều phối tối đa ba vòng:

1. `independent-analysis`: gọi tối đa ba agent độc lập, không truyền kết luận của agent khác để tránh bias.
2. `challenge`: truyền proposal đã tóm tắt cho một hoặc hai agent phản biện.
3. `synthesis`: giao requirements, proposals, challenges và decisions cho `planning-agent`.

Mỗi result dùng contract:

- `Status`
- `Summary`
- `Scope`
- `Findings` hoặc `Options`
- `Assumptions`
- `Risks`
- `Validation`
- `Next`

Tối đa một vòng challenge bổ sung. Khi conclusions mâu thuẫn, orchestrator ưu tiên evidence từ repository; chỉ hỏi người dùng khi không thể phân xử mà không thay đổi behavior mong muốn.

## Milestone contract

Mỗi milestone phải có:

```text
Objective
Dependencies
Scope
Allowed files
Forbidden files
Expected behavior
Acceptance criteria
Validation plan
Docs impact candidates
Definition of done
```

Không chạy song song các milestone cùng sửa một file, cùng database schema, cùng lockfile hoặc phụ thuộc output chưa hoàn thành của nhau.

## Checkpoint contract

Sau mỗi milestone, `planning-agent` hoặc orchestrator cập nhật plan với:

```text
Completed milestones
Current milestone
Blocked items
Validation evidence
Architecture decisions
Docs impact result
Remaining risks
Next milestone
```

Plan là nguồn trạng thái bền vững khi phải tiếp tục ở chat mới.

## Documentation impact lifecycle

Sau mỗi milestone có code change, orchestrator tạo kết quả:

```text
Status: required | not-required | uncertain
Changed behavior
Affected audience
Candidate docs
Evidence
Recommended updates
```

### `required`

Khi thay đổi một trong các nhóm:

- API request/response, error contract hoặc integration contract;
- config, environment variable, feature flag;
- build, test, deploy, migration, rollback hoặc operational procedure;
- user-visible behavior;
- architecture hoặc data flow quan trọng;
- onboarding hoặc local development;
- public command, public class/module name được tài liệu tham chiếu.

### `not-required`

Khi chỉ là:

- refactor nội bộ giữ nguyên contract;
- đổi tên biến local hoặc format/lint;
- test-only change;
- tối ưu nội bộ không đổi cách vận hành;
- bug fix không làm sai hoặc thay đổi behavior đã được mô tả trong docs.

### `uncertain`

Orchestrator phải đọc/search tài liệu gần scope hoặc gọi `docs-agent` ở chế độ đánh giá read-first. Không được mặc định rewrite README.

## Autonomous blocker policy

Orchestrator tiếp tục tự động trong từng milestone. Chỉ hỏi người dùng khi:

- thiếu thông tin dẫn đến nhiều behavior hợp lệ khác nhau;
- cần credential hoặc quyền ngoài workspace;
- thao tác phá hủy hoặc không thể rollback;
- scope thực tế lớn hơn đáng kể roadmap;
- validation bắt buộc không thể chạy;
- conflict code không thể giải quyết an toàn;
- đã chạm retry budget mà failure signature không đổi.

## Execution budget

Cho `LONG_RUNNING`:

- tối đa 6 milestone trong một plan; lớn hơn phải chia phase;
- tối đa 3 analysis worker song song;
- tối đa 1 implementation worker trên cùng file set;
- tối đa 2 vòng fix-review mỗi milestone;
- tối đa 1 vòng challenge bổ sung;
- tối đa 2 lần điều chỉnh roadmap.

## Validation and regression protection

Repository tests phải kiểm tra:

- có `architecture-agent` và `planning-agent`, cả hai không user-invocable;
- orchestrator route được `LONG_RUNNING` và tham chiếu hai agent mới;
- worker không được có subagent references; chỉ orchestrator được dùng `agent` để handoff;
- long-running workflow có plan, milestone, checkpoint và autonomous blocker policy;
- docs impact assessment tồn tại sau code-changing milestone;
- docs-agent có `author` và `impact-update`;
- implementation-agent trả docs impact candidates;
- review-agent hỗ trợ milestone/final review;
- package và README phản ánh behavior mới.

## Definition of done

- Agent definitions hợp lệ và validator chạy exit code 0.
- Python tests và Node CLI tests đều pass.
- Package dry-run chứa các agent mới.
- README mô tả FAST_FIX, LONG_RUNNING, docs impact và cách tiếp tục từ checkpoint.
- Version npm được tăng theo semantic versioning.

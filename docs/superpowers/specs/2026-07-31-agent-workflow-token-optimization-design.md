# Agent Workflow and Token Optimization Design

## Goal

Giảm chi phí token và xung đột điều phối trong `doct-agents` mà không làm yếu quy trình review, validation, checkpoint hoặc phân quyền hiện có.

## Evidence and constraints

- VS Code chạy subagent trong context cô lập và chỉ trả kết quả về parent; handoff cần truyền đúng phần liên quan thay vì toàn bộ lịch sử.
- Agent Skills được nạp theo nhu cầu, phù hợp với workflow dài và ít dùng hơn là nhồi toàn bộ hướng dẫn vào orchestrator.
- Mỗi tool làm tăng decision space và output của tool được thêm vào context; validation command phải có một owner rõ ràng để tránh chạy lặp.
- Repo hiện chỉ cho orchestrator gọi subagent và chỉ `test-agent` có đồng thời `edit + execute`; các guardrail này phải được giữ nguyên.
- Không thêm dependency runtime mới.
- Python validator vẫn phải chạy trên Python 3.9.

## Problems

### Ambiguous completion semantics

`Status: completed` hiện có thể nghĩa là worker đã hoàn thành phần việc nhưng phát hiện defect hoặc validation thất bại. Orchestrator có thể hiểu nhầm worker completion thành task success.

### Overlapping validation ownership

`review-agent`, `test-agent` và `cli-executor` đều có thể chạy test/lint. LONG_RUNNING có thể chạy cùng command ở worker, review và final validation, làm tăng token, thời gian và noise.

### Large repeated contracts

Orchestrator mô tả đầy đủ FAST_FIX, LONG_RUNNING, docs impact, checkpoint, anti-loop, permissions và result schema trong một body. Worker result contract mặc định cũng yêu cầu nhiều field ngay cả khi không có finding.

### Dependency update handoff gap

`dependency-agent` chỉ audit; ownership sửa manifest và regenerate lockfile chưa rõ, dễ tạo vòng handoff hoặc worker từ chối đúng scope.

### No enforceable prompt budget

Validator kiểm tra quyền và status vocabulary nhưng chưa chặn prompt tăng không kiểm soát hoặc contract mới bị xóa trong lần refactor sau.

## Chosen approach

Tối ưu trực tiếp agent definitions và mở rộng validator/tests, không tạo thêm agent.

### 1. Add `Outcome`

Mọi worker result có thêm trường:

```text
Outcome: passed | change-made | defect-found | validation-failed | no-change
```

`Status` tiếp tục biểu diễn execution state của worker. `Outcome` biểu diễn ý nghĩa nghiệp vụ của kết quả. Domain agent có thể dùng subset phù hợp nhưng vocabulary phải nằm trong allowlist.

### 2. Single-owner validation policy

- `test-agent`: chạy test hẹp mà nó vừa thêm hoặc sửa.
- `review-agent`: mặc định tái sử dụng validation evidence; chỉ chạy command khi thiếu evidence cần thiết và phải ghi `Validation owner: review-agent`.
- `cli-executor`: owner mặc định cho build, lint, typecheck, integration test và validation cuối.
- Domain agents chỉ sở hữu command chuyên môn: dependency audit, benchmark, browser runtime.
- Orchestrator không giao lại command có cùng normalized signature khi đã có fresh successful evidence cho cùng code revision.

### 3. Compact result contract

Mặc định worker trả compact result:

```text
Status
Outcome
Summary
Scope
Validation
Next
```

Chỉ thêm `Findings`, `Changes`, `Docs impact candidates` hoặc domain fields khi có dữ liệu. Summary tối đa 120 từ; handoff context tối đa 10 bullet và không copy nguyên worker result.

### 4. Explicit dependency update ownership

- `dependency-agent` audit và đề xuất version/compatibility, không sửa file.
- `implementation-agent` được sửa manifest khi manifest nằm trong `Allowed files`.
- `cli-executor` được chạy package-manager command để regenerate lockfile khi command, target package và expected lockfile đã được orchestrator cung cấp; không tự chọn version.

### 5. Prompt budget guardrails

Validator kiểm tra:

- Mọi worker khai báo `Outcome` với vocabulary hợp lệ.
- `review-agent` có reuse-evidence rule.
- Orchestrator có compact handoff/result policy và validation deduplication.
- Agent body có giới hạn ký tự theo tier để phát hiện prompt phình bất thường; orchestrator có budget cao hơn worker.

Budget là guardrail bảo trì, không phải token count tuyệt đối vì tokenizer phụ thuộc model.

## Files

- `agents/orchestrator.agent.md`: rút gọn routing, handoff, result và validation ownership.
- `agents/implementation-agent.agent.md`: manifest ownership và compact result.
- `agents/review-agent.agent.md`: reuse evidence, command escalation.
- `agents/test-agent.agent.md`: test ownership và outcome semantics.
- `agents/cli-executor.agent.md`: final validation và lockfile regeneration contract.
- `agents/dependency-agent.agent.md`: audit-only boundary.
- Các worker còn lại: thêm compact `Outcome` contract nếu thiếu.
- `scripts/validate_agents.py`: outcome vocabulary, repository contract và prompt-size guardrails.
- `tests/test_validate_agents.py`: regression tests.
- `README.md`: mô tả validation ownership và token policy.

## Testing

1. Test validator từ chối `Outcome` ngoài allowlist.
2. Test validator chấp nhận common outcome vocabulary.
3. Repository contract test xác nhận orchestrator có deduplication và compact handoff.
4. Repository contract test xác nhận review/test/CLI ownership không chồng mặc định.
5. Prompt budget test xác nhận agent body không vượt tier limit.
6. Chạy `npm run check` trên CI Ubuntu minimum/current và Windows current.

## Risks and mitigations

- **Rút gọn quá mức làm mất safety rule:** giữ các invariant trong validator và tests trước khi refactor.
- **Outcome làm output dài hơn:** bù lại bằng compact schema và field optional.
- **Review thiếu khả năng xác minh:** vẫn giữ `execute`, nhưng chỉ dùng khi evidence thiếu và không được lặp command signature.
- **Budget false positive:** dùng character budget đủ rộng, chỉ nhằm phát hiện tăng trưởng lớn.

## Success criteria

- CI đầy đủ pass trên ba runtime lane.
- Không thay đổi allowlist subagent routing hoặc edit/execute.
- Mỗi validation command có owner rõ và không chạy lặp khi có fresh evidence.
- Worker completion không còn bị nhầm với task outcome.
- Orchestrator và các worker chính giảm kích thước prompt so với baseline trước thay đổi.

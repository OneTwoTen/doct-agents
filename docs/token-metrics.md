# Đo token và hiệu quả workflow

Prompt-size budget trong validator chỉ là guardrail tĩnh. Để biết chính xác input token, output token, tool calls, duration và cache behavior của một phiên chạy, dùng Agent Debug Logs của VS Code.

## Bật Agent Debug Logs

Thêm setting:

```json
{
  "github.copilot.chat.agentDebugLog.fileLogging.enabled": true
}
```

Sau đó:

1. Mở Chat view.
2. Chọn menu `...` và `Show Agent Debug Logs`, hoặc chạy `Developer: Open Agent Debug Logs`.
3. Chọn session cần phân tích.
4. Mở `Summary` để xem tổng token usage, tool calls, error count và duration.
5. Mở `Agent Flow Chart` để xem orchestrator/subagent handoff.
6. Mở `Cache Explorer` để tìm prompt prefix thay đổi làm giảm cache hit.
7. Dùng `Chat Debug View` khi cần xem system prompt, user prompt, context và tool payload thực tế của từng model request.

Tài liệu chính thức:

- [Debug chat interactions](https://code.visualstudio.com/docs/agents/agent-troubleshooting/chat-debug-view)
- [Manage context for AI](https://code.visualstudio.com/docs/chat/copilot-chat-context)

## Bộ số liệu nên thu

Với mỗi session, ghi:

```text
workflow
agent hoặc subagent
model
input tokens
output tokens
cached tokens hoặc cache signal
inference calls
tool calls
duration
result status
result outcome
validation commands
failure signatures
```

Input/output token thực tế phụ thuộc model, context được attach, tool output và lịch sử session; không thể suy ra chính xác chỉ từ số ký tự trong `.agent.md`.

## Scenario benchmark

Dùng cùng repo revision và cùng model cho từng lần đo.

### FAST_FIX

Đo riêng `direct` và `guarded`; không gộp hai path vào cùng một median.

Prompt direct mẫu:

```text
Sửa một bug cục bộ có expected behavior rõ, dùng validation hẹp có sẵn và không thêm capability ngoài scope.
```

Prompt guarded mẫu:

```text
Sửa một bug business logic cục bộ, thêm regression test cần thiết và validate thay đổi.
```

Theo dõi:

- execution path `direct | guarded`;
- số subagent được gọi và worker nào thực sự cần thiết;
- command validation có bị chạy lặp không;
- input/output token của orchestrator, implementation, test/review và CLI;
- cache hit giữa các model request;
- tổng duration.

Mục tiêu ban đầu cho `FAST_FIX direct`:

```text
planning-agent calls = 0
review-agent default = 0
docs-agent default = 0
median worker count <= 2
duplicate validation signature = 0
change/validate loops = 1 normally
```

### CODE_REVIEW

Prompt mẫu:

```text
Review diff này theo correctness và test gap, không sửa code.
```

Theo dõi:

- review-agent có tái sử dụng evidence hay chạy command mới;
- số findings trước/sau deduplicate;
- output token trên mỗi finding.

### LONG_RUNNING

Dùng một task có 2–3 milestone và checkpoint rõ.

Theo dõi:

- số independent-analysis workers;
- số challenge rounds;
- token theo milestone;
- context được chuyển qua handoff;
- command signature bị chạy lại;
- token trước/sau khi mở chat mới từ checkpoint.

## Baseline và mục tiêu

Đo ít nhất 5 session cho mỗi workflow/path và dùng median thay vì một lần chạy đơn lẻ.

Các mục tiêu ban đầu:

- không có command validation trùng signature cho cùng code revision;
- FAST_FIX direct mặc định không gọi worker không liên quan;
- independent-analysis mặc định tối đa 2 worker;
- worker summary không vượt 120 từ;
- handoff context không vượt 10 bullet;
- không có prompt vượt budget của validator;
- giảm input/output token mà không làm giảm pass rate hoặc acceptance-criteria coverage.

## Phân tích session

Có thể attach snapshot Agent Debug Logs vào Chat và hỏi:

```text
/troubleshoot how many tokens did this session use and which agent/tool added the most context?
```

Khi cần phân tích ngoài VS Code, export session thành OpenTelemetry JSON và tổng hợp theo workflow, agent, input/output token, tool calls và duration. Không commit file log nếu nó chứa prompt, source code, đường dẫn cá nhân hoặc dữ liệu nhạy cảm.

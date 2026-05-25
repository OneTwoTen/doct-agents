# doct-agents

`doct-agents` là bộ VS Code Copilot custom agents dùng cho các workflow kỹ thuật của DOCT. Mỗi agent có một vai trò hẹp, tool được cấp theo nguyên tắc least privilege, và có thể được orchestrator điều phối khi tác vụ cần nhiều bước.

## Cấu trúc repo

```text
.
├── README.md
└── agents/
    ├── agent-authoring.agent.md
    ├── aggregator.agent.md
    ├── cli-executor.agent.md
    ├── dependency-agent.agent.md
    ├── docs-agent.agent.md
    ├── orchestrator.agent.md
    ├── performance-agent.agent.md
    ├── refactor-agent.agent.md
    ├── req-extractor.agent.md
    ├── research-agent.agent.md
    ├── review-agent.agent.md
    ├── security-agent.agent.md
    └── test-agent.agent.md
```

Repo này không bắt buộc dùng `.github/agents/`. Nếu đặt repo ở vị trí tùy biến, hãy cấu hình VS Code để đọc thư mục `agents/`.

## Cấu hình VS Code

Ví dụ khi dùng trực tiếp trong repo hiện tại hoặc khi nhúng repo này vào project khác:

```json
{
  "chat.agentFilesLocations": {
    "agents": true,
    "third_party/doct-agents/agents": true
  }
}
```

Nếu sau này thêm skills ở vị trí tùy biến, cấu hình tương tự với `chat.agentSkillsLocations`.

## Agent hiện có

| Agent | Khi nào dùng | Tools | User invocable | Model |
| --- | --- | --- | --- | --- |
| `orchestrator` | Chia nhỏ tác vụ kỹ thuật phức tạp, giao việc cho subagent và hợp nhất kết quả cuối. | `agent`, `read`, `search`, `todo`, `vscode/askQuestions` | Không khai báo | GPT-5.4 |
| `cli-executor` | Chạy terminal/CLI, thu stdout/stderr/exit code/log và phân loại kết quả thành lỗi, tiếp tục hoặc hoàn tất. | `execute`, `read`, `agent`, `vscode/askQuestions` | Có | GPT-5.4 |
| `aggregator-agent` | Tổng hợp findings từ nhiều subagent, khử trùng lặp và sắp xếp theo mức độ nghiêm trọng. | Không có | Không | GPT-5.4 mini |
| `agent-authoring` | Tạo hoặc cập nhật VS Code custom agents hay agent skills đúng cấu trúc workspace. | `read`, `search`, `edit`, `web`, `vscode/askQuestions` | Không | GPT-5 mini |
| `dependency-agent` | Kiểm tra package manager, lockfile, gói lỗi thời, vulnerability và hướng nâng cấp an toàn. | `read`, `search`, `execute`, `agent` | Không | Raptor mini |
| `docs-agent` | Tạo/cập nhật README, hướng dẫn cài đặt, onboarding notes hoặc tài liệu nội bộ ngắn. | `read`, `search`, `edit` | Không | GPT-5 mini |
| `performance-agent` | Phân tích benchmark, hiệu năng thực tế, điểm nghẽn hoặc so sánh với baseline. | `read`, `search`, `execute`, `agent` | Không | Raptor mini |
| `refactor-agent` | Refactor nhỏ, giữ nguyên hành vi, cải thiện readability hoặc giảm trùng lặp trong phạm vi hẹp. | `read`, `search`, `edit` | Không | Raptor mini |
| `req-extractor` | Chuyển brief/ticket/yêu cầu mơ hồ thành requirements, constraints, acceptance criteria và câu hỏi làm rõ. | `read`, `search`, `vscode/askQuestions` | Không | GPT-5 mini |
| `research-agent` | Thu thập thông tin bên ngoài repo từ nguồn đáng tin để hỗ trợ quyết định kỹ thuật/kiến trúc. | `web`, `read`, `search` | Không | GPT-5 mini |
| `review-agent` | Review code read-only theo mode `qa` hoặc `quality`, tập trung bug, test gap, maintainability, lint/type/error handling. | `read`, `search`, `execute`, `agent` | Không | Raptor mini |
| `security-agent` | Security review read-only để tìm secrets, cấu hình không an toàn hoặc flow/code path rủi ro. | `read`, `search` | Không | GPT-5 mini |
| `test-agent` | Thêm/cập nhật test tự động, tìm coverage gaps và chạy tập test hẹp nhất liên quan. | `read`, `search`, `edit`, `execute` | Không | Raptor mini |

## Nhóm vai trò

- Điều phối: `orchestrator`
- Chạy lệnh: `cli-executor`
- Tổng hợp: `aggregator-agent`
- Tạo/cập nhật customization: `agent-authoring`
- Phân tích yêu cầu: `req-extractor`
- Tài liệu và research: `docs-agent`, `research-agent`
- Chất lượng code: `review-agent`, `refactor-agent`, `test-agent`
- Rủi ro vận hành: `security-agent`, `dependency-agent`, `performance-agent`

## Cách sử dụng

### Dùng như Git submodule

```bash
git submodule add https://github.com/OneTwoTen/doct-agents.git third_party/doct-agents
git submodule update --init --recursive
```

Cập nhật submodule:

```bash
git submodule update --remote --merge
```

### Dùng như Git subtree

```bash
git subtree add --prefix=third_party/doct-agents https://github.com/OneTwoTen/doct-agents.git main --squash
```

## Frontmatter chuẩn

Mỗi file `.agent.md` nên có frontmatter theo các trường đang dùng trong repo:

```yaml
---
name: agent-name
description: "Mô tả rõ khi nào nên dùng agent."
argument-hint: "Tùy chọn, chỉ thêm khi agent cần gợi ý input."
tools: ["read", "search"]
agents: []
user-invocable: false
model: GPT-5 mini (copilot)
---
```

Ghi chú:

- `description` phải đủ cụ thể để VS Code discover đúng agent.
- `tools` chỉ cấp quyền tối thiểu cần thiết.
- Nếu agent gọi subagent, phải có `agent` trong `tools` và liệt kê subagent trong `agents`.
- Agent read-only không được có `edit`; agent không cần chạy lệnh không nên có `execute`.
- Agent có thể gặp việc ngoài quyền của mình nên có đường handoff tối thiểu qua `agent` thay vì hỏi người dùng cấp thêm quyền khi repo đã có subagent phù hợp.
- `argument-hint` chỉ dùng khi input của agent cần được định hướng rõ.
- `user-invocable` hiện chỉ bật cho `cli-executor`; phần lớn worker còn lại dùng qua orchestrator.

## Quy ước tool và quyền

- `read`: đọc file hoặc đoạn nội dung đã xác định.
- `search`: tìm file, symbol hoặc đoạn liên quan trước khi đọc rộng.
- `edit`: sửa file; chỉ cấp cho agent thực sự được phép thay đổi nội dung.
- `execute`: chạy CLI, test, audit, benchmark hoặc command kiểm chứng.
- `agent`: giao việc cho subagent.
- `web`: tra cứu nguồn ngoài repo khi thông tin có thể thay đổi hoặc cần nguồn chính thức.
- `todo`: theo dõi tác vụ nhiều bước trong orchestrator.
- `vscode/askQuestions`: hỏi lại khi thiếu dữ liệu để tiếp tục an toàn.

## Quy ước điều phối quyền

- Trước khi hỏi người dùng cấp thêm quyền cho agent hiện tại, kiểm tra xem repo đã có subagent có tool phù hợp chưa; nếu có, dùng `agent` để handoff.
- Chỉ hỏi lại khi thiếu dữ liệu nghiệp vụ, cần xác nhận thao tác phá hủy/khó hoàn tác, cần xác thực bên ngoài hoặc chưa có agent nào trong repo có quyền phù hợp.
- Agent chạy command nhưng không có `edit` không được tự sửa file bằng CLI; khi cần thay đổi nội dung, handoff sang `docs-agent`, `refactor-agent`, `test-agent` hoặc `agent-authoring` theo đúng phạm vi.

## Agent I/O contract

Khi orchestrator giao việc hoặc agent trả kết quả, ưu tiên contract ngắn này cho tác vụ đủ phức tạp. Với tác vụ nhỏ có thể rút gọn.

Input handoff:

- `Objective`: mục tiêu cần xử lý.
- `Scope`: file, module hoặc phạm vi liên quan.
- `Constraints`: quyền được dùng, điều không được làm, giới hạn thời gian hoặc token.
- `Context`: tín hiệu quan trọng đã biết; không gửi lại toàn bộ nội dung đã đọc nếu không cần.
- `Expected output`: dạng kết quả mong muốn.

Output handoff:

- `Status`: `done`, `needs-info`, `needs-fix` hoặc `blocked`.
- `Findings`: tối đa 5 mục chính nếu là review, research hoặc audit.
- `Actions`: việc đã làm hoặc đề xuất làm tiếp.
- `Validation`: lệnh đã chạy, kết quả chính hoặc lý do chưa chạy.
- `Next`: bước tiếp theo ngắn gọn.

## Quy ước thao tác

- Đọc file: dùng `search` trước để khoanh vùng file/symbol/đoạn liên quan, rồi mới `read` phần cần thiết.
- Sửa file có sẵn: dùng `edit` với diff/patch nhỏ, rõ và dễ review.
- Tạo file mới: sinh nội dung đầy đủ rồi ghi bằng `edit`; dùng script/template khi boilerplate lớn.
- Không dùng `execute`/shell để tạo hoặc sửa file nội dung, bao gồm redirect, heredoc, `Set-Content`, `Out-File`, `sed -i`, `perl -pi` hoặc script ghi file một lần; ngoại lệ chỉ dành cho công cụ sinh file/format/codemod có chủ đích, có thể kiểm chứng và nằm đúng phạm vi.
- Refactor hàng loạt: chỉ dùng script/codemod qua `execute` khi thay đổi cơ học, có thể kiểm chứng và tiết kiệm hơn chỉnh tay.
- Log dài: ưu tiên ghi ra file log rồi đọc đúng đoạn lỗi chính thay vì truyền toàn bộ stdout/stderr qua nhiều agent.
- Handoff giữa agents: chỉ truyền mục tiêu, phạm vi, constraint, tín hiệu chính và output mong muốn.
- Không tách thêm agent nếu workflow có thể xử lý bằng mode, constraint hoặc agent hiện có.

## Cập nhật repo này

1. Sửa hoặc thêm file `.agent.md` trong `agents/`.
2. Giữ `name` ổn định, `description` rõ ràng và `tools` tối thiểu.
3. Nếu thêm worker mới cho orchestrator, cập nhật `agents` trong `agents/orchestrator.agent.md`.
4. Cập nhật README khi thêm/xóa/đổi vai trò, tools, model hoặc `user-invocable`.
5. Kiểm tra frontmatter, tên tool và cấu trúc file trước khi commit.

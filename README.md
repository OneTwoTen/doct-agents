# doct-agents

`doct-agents` là một bộ custom agents cho VS Code Copilot, được tổ chức theo nhu cầu thực tế của hệ thống DOCT. Mỗi agent có một vai trò riêng và có thể phối hợp với nhau để xử lý các tác vụ như phân tích yêu cầu, review chất lượng, kiểm tra bảo mật, viết test, cập nhật tài liệu và tổng hợp kết quả.

## Cấu trúc repo hiện tại

Repo này **không bắt buộc** phải dùng `.github/agents/`, vì có thể chủ động cấu hình đường dẫn custom agent trong VS Code. Hiện tại bộ agent được đặt trong:

- `agents/`
- `agents/workers/`

Điều quan trọng là nội dung file `.agent.md` phải đúng chuẩn frontmatter và dùng đúng tên tool của VS Code.

## Những gì đã được chuẩn hóa

- Dùng đúng các trường frontmatter của custom agent như `name`, `description`, `argument-hint`, `tools`, `agents`, `user-invocable`.
- Dùng đúng tên built-in tool và tool set của VS Code như `read`, `search`, `edit`, `execute`, `agent`, `web`, `todos`, `vscode/askQuestions`.
- Viết lại mô tả agent bằng tiếng Việt có dấu để dễ bảo trì.
- Giữ `description` đủ rõ để agent dễ được discover đúng lúc.

## Danh sách agent hiện có

- `orchestrator`: điều phối tác vụ phức tạp và giao việc cho các worker agents.
- `aggregator-agent`: tổng hợp kết quả từ nhiều subagent.
- `dependency-agent`: kiểm tra dependency, audit, package lỗi thời.
- `docs-agent`: cập nhật README và tài liệu nội bộ.
- `performance-agent`: phân tích benchmark và điểm nghẽn.
- `qa-agent`: QA pass tổng quát, tìm bug và khoảng trống test.
- `quality-agent`: review maintainability, lint, type và error handling.
- `refactor-agent`: refactor nhỏ, không phá vỡ hành vi.
- `req-extractor`: trích xuất requirements từ feature brief.
- `research-agent`: tìm và tổng hợp thông tin từ nguồn bên ngoài.
- `security-agent`: security review theo chế độ read-only.
- `test-agent`: viết và cập nhật test.
- `agent-authoring`: agent chuyên tạo và cập nhật custom agents hoặc agent skills.

## Cách sử dụng

### 1. Git submodule

```bash
git submodule add https://github.com/OneTwoTen/doct-agents.git third_party/doct-agents
git submodule update --init --recursive
```

Cập nhật submodule:

```bash
git submodule update --remote --merge
```

### 2. Git subtree

```bash
git subtree add --prefix=third_party/doct-agents https://github.com/OneTwoTen/doct-agents.git main --squash
```

## Cấu hình trong VS Code

Vì repo này đặt agent ở thư mục tùy biến thay vì `.github/agents/`, cần trỏ thêm location trong VS Code. Ví dụ:

```json
{
   "chat.agentFilesLocations": {
      "agents": true,
      "third_party/doct-agents/agents": true
   }
}
```

Nếu sau này thêm skills ở vị trí tùy biến, có thể cấu hình tương tự với `chat.agentSkillsLocations`.

## Cách cập nhật repo này

1. Sửa hoặc thêm file `.agent.md` trong `agents/` hoặc `agents/workers/`.
2. Giữ `description` rõ ràng để VS Code dễ discover đúng agent.
3. Chỉ cấp các tool tối thiểu cần thiết cho từng agent.
4. Kiểm tra kỹ frontmatter, tên tool và cấu trúc file trước khi commit.

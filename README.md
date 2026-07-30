# doct-agents

`doct-agents` là bộ custom agents cho GitHub Copilot trong VS Code, tập trung vào workflow kỹ thuật: review, sửa code, test, chạy CLI, kiểm tra browser, security, dependency và performance.

## Bắt đầu nhanh

Yêu cầu:

- VS Code có GitHub Copilot Chat.
- Python 3.9 trở lên.
- Kết nối Internet trong lần cài hoặc cập nhật.

### Windows — cài cho toàn bộ project

Mở PowerShell:

```powershell
$installer = Join-Path $env:TEMP "doct-agents-install.py"
Invoke-WebRequest "https://raw.githubusercontent.com/OneTwoTen/doct-agents/main/install.py" -OutFile $installer
py -3 $installer install --scope user
```

Agent được cài vào:

```text
%USERPROFILE%\.copilot\agents
```

### macOS/Linux — cài cho toàn bộ project

```bash
curl -fsSL https://raw.githubusercontent.com/OneTwoTen/doct-agents/main/install.py \
  -o /tmp/doct-agents-install.py
python3 /tmp/doct-agents-install.py install --scope user
```

Agent được cài vào:

```text
~/.copilot/agents
```

### Cài riêng cho project hiện tại

Chạy tại thư mục gốc của project:

```bash
python install.py install --scope workspace
```

Hoặc chạy file installer đã tải ở phần trên với `--scope workspace`. Agent sẽ được đặt trong:

```text
.github/agents
```

Đây là vị trí workspace mặc định của VS Code, vì vậy không cần tự sửa `chat.agentFilesLocations`.

## Dùng trong VS Code

Sau khi cài:

1. Reload VS Code bằng lệnh `Developer: Reload Window`.
2. Mở GitHub Copilot Chat.
3. Gõ `/agents` hoặc mở danh sách agent ở cuối ô chat.
4. Chọn một trong hai agent chính:
   - `orchestrator`: task phức tạp cần chia nhỏ, review, sửa và validate.
   - `cli-executor`: chạy project, test, build, lint, migrate, seed hoặc script.

Các worker khác mặc định được gọi qua `orchestrator`, không cần chọn thủ công.

### Prompt mẫu

Review và sửa một PR:

```text
Review PR này theo hướng correctness và test gap. Chỉ sửa finding high/critical, sau đó chạy test hẹp nhất để validate.
```

Tối ưu hiệu năng:

```text
Phân tích điểm nghẽn của module order, đo baseline trước, đề xuất thay đổi nhỏ và validate bằng benchmark liên quan.
```

Chạy project:

```text
Chạy project ở thư mục backend, tìm đúng command từ cấu hình repo, báo URL hoặc lỗi quyết định.
```

Kiểm tra UI:

```text
Mở http://localhost:3000, kiểm tra luồng đăng nhập, chụp screenshot ở bước lỗi và báo expected/actual.
```

## Cập nhật

Dùng lại installer với lệnh `update`.

Windows:

```powershell
py -3 $env:TEMP\doct-agents-install.py update --scope user
```

macOS/Linux:

```bash
python3 /tmp/doct-agents-install.py update --scope user
```

Cập nhật cho workspace hiện tại:

```bash
python install.py update --scope workspace
```

Installer chỉ ghi đè các file do `doct-agents` quản lý. Nếu một agent đã được chỉnh sửa cục bộ, quá trình cập nhật sẽ dừng để tránh mất dữ liệu. Chỉ dùng `--force` khi thực sự muốn thay thế các chỉnh sửa đó:

```bash
python install.py update --scope user --force
```

## Kiểm tra trạng thái

```bash
python install.py status --scope user
```

Kết quả phân biệt:

- `Installed`: file còn nguyên như lần cài gần nhất.
- `Modified`: file đã được chỉnh sửa cục bộ.
- `Missing`: file do installer quản lý nhưng đã bị xóa.

Kiểm tra workspace hiện tại:

```bash
python install.py status --scope workspace
```

## Gỡ cài đặt

```bash
python install.py uninstall --scope user
```

Installer chỉ xóa file còn đúng checksum đã cài. File đã chỉnh sửa sẽ được giữ lại. Để xóa cả file đã chỉnh sửa:

```bash
python install.py uninstall --scope user --force
```

## Chọn scope nào?

| Nhu cầu | Scope | Vị trí |
| --- | --- | --- |
| Dùng agent cho mọi project | `user` | `~/.copilot/agents` |
| Team muốn version agent cùng source code | `workspace` | `.github/agents` |
| Phát triển chính repo này | Chạy trực tiếp repo | `agents/` qua `.vscode/settings.json` |

Khuyến nghị:

- Cá nhân: dùng `--scope user`.
- Project/team: commit `.github/agents` vào project hoặc dùng Git submodule nếu muốn cập nhật tập trung.

## Agent chính

| Agent | Vai trò |
| --- | --- |
| `orchestrator` | Route workflow, chia task, quản lý state/budget và tổng hợp kết quả. |
| `cli-executor` | Chạy terminal/CLI và trả command, cwd, exit code, log quyết định. |
| `review-agent` | Review read-only về correctness, test gap và maintainability. |
| `refactor-agent` | Refactor nhỏ, an toàn, không đổi public behavior. |
| `test-agent` | Viết/cập nhật test và chạy validation hẹp. |
| `browser-agent` | Kiểm tra UI/runtime bằng VS Code Browser tools. |
| `security-agent` | Security review read-only. |
| `dependency-agent` | Audit dependency, lockfile và vulnerability. |
| `performance-agent` | Benchmark và phân tích bottleneck dựa trên số liệu. |
| `research-agent` | Tra cứu thông tin kỹ thuật ngoài repo. |
| `docs-agent` | Cập nhật tài liệu. |
| `req-extractor` | Chuẩn hóa yêu cầu, constraint và acceptance criteria. |
| `aggregator-agent` | Khử trùng lặp findings từ nhiều worker. |
| `agent-authoring` | Tạo/cập nhật custom agent và skill. |

## Browser tools và MCP

`browser-agent` ưu tiên VS Code Browser tools tích hợp:

- `openBrowserPage`, `navigatePage`, `readPage`, `screenshotPage`.
- `clickElement`, `hoverElement`, `dragElement`, `typeInPage`, `handleDialog`.
- `runPlaywrightCode` chỉ dùng khi interaction tools không đủ.

Bật trong VS Code:

```json
{
  "workbench.browser.enableChatTools": true
}
```

Nếu cần trace hoặc DevTools chuyên sâu, repo có cấu hình Chrome DevTools MCP tùy chọn trong `.vscode/mcp.json`. Luồng UI thông thường không phụ thuộc MCP này.

## Dùng như Git submodule

Dành cho team muốn pin một revision của bộ agent trong project:

```bash
git submodule add https://github.com/OneTwoTen/doct-agents.git third_party/doct-agents
git submodule update --init --recursive
python third_party/doct-agents/install.py install --scope workspace \
  --source-dir third_party/doct-agents/agents
```

Cập nhật:

```bash
git submodule update --remote --merge
python third_party/doct-agents/install.py update --scope workspace \
  --source-dir third_party/doct-agents/agents
```

## Dùng trực tiếp thư mục tùy biến

Khi không muốn copy agent vào `.github/agents`, có thể cấu hình VS Code đọc thư mục khác:

```json
{
  "chat.agentFilesLocations": {
    "third_party/doct-agents/agents": true
  }
}
```

Cách này phù hợp với submodule nhưng phụ thuộc workspace settings. Với người dùng thông thường, installer vẫn là cách đơn giản hơn.

## Quy tắc orchestration

- Workflow đi qua các phase: `DISCOVER -> PLAN -> ANALYZE -> CHANGE -> VALIDATE -> FINALIZE`.
- Tối đa 4 worker cho một task, tối đa 3 worker song song.
- Tối đa 2 vòng `change -> validate` cho cùng một lỗi.
- Worker trả đề xuất handoff qua `Next`; orchestrator quyết định bước tiếp theo.
- Không kết luận `done` khi thay đổi chưa được validate hoặc còn finding high/critical chưa xử lý.

## Agent I/O contract

Input handoff:

- `Objective`
- `Scope`
- `Constraints`
- `Context`
- `Expected output`

Output:

- `Status`
- `Summary`
- `Scope`
- `Findings`
- `Changes`
- `Validation`
- `Next`

Finding signature chuẩn:

```text
category:file:symbol:normalized-root-cause
```

## Phát triển và kiểm tra repo

Chạy toàn bộ unit test:

```bash
python -m unittest discover -s tests -v
```

Validate toàn bộ agent:

```bash
python scripts/validate_agents.py
```

CI kiểm tra:

- frontmatter bắt buộc;
- agent name trùng;
- reference không tồn tại hoặc self-reference;
- quyền `agent`, `edit`, `execute` không hợp lệ;
- worker bật `user-invocable` sai;
- installer không ghi đè file ngoài quản lý;
- uninstall không xóa file đã chỉnh sửa.

## Cấu trúc repo

```text
.
├── agents/                    # Agent source
├── install.py                 # Installer/update/status/uninstall
├── scripts/validate_agents.py # Validator cấu hình agent
├── tests/                     # Unit tests
├── .github/workflows/         # CI
└── .vscode/                   # Cấu hình phát triển repo
```

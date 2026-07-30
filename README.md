# doct-agents

`doct-agents` là bộ custom agents cho GitHub Copilot trong VS Code, tập trung vào review, sửa code, test, chạy CLI, browser, security, dependency và performance.

## Cài nhanh

Yêu cầu:

- VS Code có GitHub Copilot Chat.
- Một trong các runtime: Node.js 18+, Bun hoặc Python 3.9+.

> Các lệnh `npx`, `bunx` và `pnpm dlx` bên dưới hoạt động sau khi package `doct-agents` được publish lần đầu lên npm.

### Cài bằng npx

Cài cho toàn bộ project trên máy:

```bash
npx doct-agents@latest install --scope user
```

Cài riêng cho project hiện tại:

```bash
npx doct-agents@latest install --scope workspace
```

### Cài bằng bunx

```bash
bunx doct-agents@latest install --scope user
```

Cài riêng cho workspace:

```bash
bunx doct-agents@latest install --scope workspace
```

`bunx` chạy package executable khai báo trong trường `bin` của `package.json`, tương tự `npx`.

### Cài bằng pnpm dlx

```bash
pnpm dlx doct-agents@latest install --scope user
```

### Cài bằng Python

Windows PowerShell:

```powershell
$installer = Join-Path $env:TEMP "doct-agents-install.py"
Invoke-WebRequest "https://raw.githubusercontent.com/OneTwoTen/doct-agents/main/install.py" -OutFile $installer
py -3 $installer install --scope user
```

macOS/Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/OneTwoTen/doct-agents/main/install.py \
  -o /tmp/doct-agents-install.py
python3 /tmp/doct-agents-install.py install --scope user
```

## Vị trí cài đặt

| Scope | Vị trí | Dùng khi |
| --- | --- | --- |
| `user` | `~/.copilot/agents` | Dùng agent cho mọi project trên máy |
| `workspace` | `.github/agents` | Team muốn version agent cùng source code |

Đây là các vị trí mặc định của VS Code nên không cần sửa `chat.agentFilesLocations`.

## Cập nhật

Mỗi lần chạy với `@latest`, `npx`, `bunx` hoặc `pnpm dlx` sẽ tải phiên bản package mới nhất trước khi chạy.

```bash
npx doct-agents@latest update --scope user
bunx doct-agents@latest update --scope user
pnpm dlx doct-agents@latest update --scope user
```

Cập nhật workspace hiện tại:

```bash
npx doct-agents@latest update --scope workspace
```

Installer lưu checksum trong `.doct-agents-manifest.json`. Nếu một agent đã được chỉnh sửa cục bộ, update sẽ dừng để tránh mất dữ liệu.

Chỉ dùng `--force` khi thật sự muốn thay thế chỉnh sửa cục bộ:

```bash
npx doct-agents@latest update --scope user --force
```

## Kiểm tra trạng thái

```bash
npx doct-agents@latest status --scope user
```

Kết quả phân biệt:

- `Installed`: file còn nguyên như lần cài gần nhất.
- `Modified`: file đã được chỉnh sửa cục bộ.
- `Missing`: file do installer quản lý nhưng đã bị xóa.

## Gỡ cài đặt

```bash
npx doct-agents@latest uninstall --scope user
```

Installer chỉ xóa file còn đúng checksum đã cài. File đã chỉnh sửa được giữ lại.

Xóa cả file đã chỉnh sửa:

```bash
npx doct-agents@latest uninstall --scope user --force
```

## Các tùy chọn CLI

```text
doct-agents [install|update|status|uninstall] [options]

--scope user|workspace   Chọn phạm vi cài đặt
--workspace <path>       Chỉ định workspace root
--target <path>          Ghi đè thư mục đích
--force                  Cho phép thay thế/xóa file đã chỉnh sửa
-h, --help               Hiển thị trợ giúp
```

Ví dụ cài vào thư mục tùy chỉnh:

```bash
npx doct-agents@latest install --target ./custom-agents
```

## Dùng trong VS Code

Sau khi cài:

1. Chạy `Developer: Reload Window`.
2. Mở GitHub Copilot Chat.
3. Gõ `/agents` hoặc mở danh sách agent ở cuối ô chat.
4. Chọn:
   - `orchestrator` cho task phức tạp cần chia nhỏ, review, sửa và validate.
   - `cli-executor` cho chạy project, test, build, lint, migrate, seed hoặc script.

Các worker khác mặc định được orchestrator gọi, không cần chọn thủ công.

### Prompt mẫu

Review và sửa code:

```text
Review module này theo hướng correctness và test gap. Chỉ sửa finding high/critical, sau đó chạy test hẹp nhất để validate.
```

Chạy project:

```text
Chạy project trong thư mục backend, tự tìm command phù hợp từ cấu hình repo và báo URL hoặc lỗi quyết định.
```

Kiểm tra UI:

```text
Mở http://localhost:3000, kiểm tra luồng đăng nhập, chụp screenshot ở bước lỗi và báo expected/actual.
```

## Agent chính

| Agent | Vai trò |
| --- | --- |
| `orchestrator` | Route workflow, chia task, quản lý state/budget và tổng hợp kết quả |
| `cli-executor` | Chạy terminal/CLI, thu exit code và log quyết định |
| `review-agent` | Review correctness, test gap và maintainability |
| `refactor-agent` | Refactor nhỏ, an toàn, không đổi public behavior |
| `test-agent` | Viết/cập nhật test và chạy validation hẹp |
| `browser-agent` | Kiểm tra UI/runtime bằng VS Code Browser tools |
| `security-agent` | Security review read-only |
| `dependency-agent` | Audit dependency, lockfile và vulnerability |
| `performance-agent` | Benchmark và phân tích bottleneck dựa trên số liệu |
| `research-agent` | Tra cứu thông tin kỹ thuật ngoài repo |
| `docs-agent` | Cập nhật tài liệu |
| `req-extractor` | Chuẩn hóa requirement và acceptance criteria |
| `aggregator-agent` | Khử trùng lặp findings từ nhiều worker |
| `agent-authoring` | Tạo/cập nhật custom agent và skill |

## Browser tools

Bật VS Code Browser chat tools:

```json
{
  "workbench.browser.enableChatTools": true
}
```

`browser-agent` ưu tiên `openBrowserPage`, `readPage`, interaction tools và `screenshotPage`. `runPlaywrightCode` chỉ dùng khi các tool cơ bản không đủ.

## Dùng như Git submodule

Dành cho team muốn pin một revision:

```bash
git submodule add https://github.com/OneTwoTen/doct-agents.git third_party/doct-agents
git submodule update --init --recursive
python third_party/doct-agents/install.py install --scope workspace \
  --source-dir third_party/doct-agents/agents
```

## Phát triển và kiểm tra

Node CLI:

```bash
npm test
npm pack --dry-run
```

Python installer và validator:

```bash
python -m unittest discover -s tests -v
python scripts/validate_agents.py
```

Chạy toàn bộ:

```bash
npm run check
```

## Publish lên npm

Package dùng tên `doct-agents` và executable cùng tên. Workflow `.github/workflows/publish-npm.yml` publish khi tạo GitHub Release hoặc chạy thủ công.

Repository cần secret:

```text
NPM_TOKEN
```

Quy trình release:

1. Xác nhận tên package `doct-agents` còn khả dụng hoặc đổi `name` trong `package.json`.
2. Tăng `version` trong `package.json`.
3. Merge thay đổi vào `main`.
4. Tạo GitHub Release tương ứng, ví dụ `v0.1.0`.
5. Workflow chạy test, `npm pack --dry-run`, sau đó `npm publish --provenance`.

Sau lần publish đầu tiên, các lệnh `npx doct-agents@latest` và `bunx doct-agents@latest` hoạt động trực tiếp.

## Cấu trúc repo

```text
.
├── agents/                    # Agent source và nội dung npm package
├── bin/doct-agents.js         # CLI cho npx, bunx và pnpm dlx
├── install.py                 # Installer Python fallback
├── package.json               # npm package metadata và bin mapping
├── scripts/validate_agents.py # Validator cấu hình agent
├── tests/                     # Node và Python unit tests
├── .github/workflows/         # Validate và publish npm
└── .vscode/                   # Cấu hình phát triển repo
```

# doct-agents

`doct-agents` là bộ custom agents dùng chung cho **GitHub Copilot trong VS Code** và **OpenCode**, hỗ trợ review, sửa code, test, chạy CLI, browser, security, dependency, performance và triển khai yêu cầu dài hơi theo roadmap.

Agent definitions trong `agents/*.agent.md` là source of truth duy nhất. Copilot dùng trực tiếp các file này; khi cài cho OpenCode, installer render chúng sang OpenCode Markdown agents và giữ nguyên workflow/routing contract.

## Cài nhanh

Yêu cầu:

- GitHub Copilot Chat nếu dùng platform `copilot`.
- OpenCode nếu dùng platform `opencode`.
- Một trong các runtime cài installer: Node.js 18+, Bun hoặc Python 3.9+.

### Cài bằng npx

Mặc định, `install` và `update` luôn cài Copilot và tự cài thêm OpenCode khi phát hiện `opencode`, `opencode2` hoặc thư mục config OpenCode chuẩn:

```bash
npx doct-agents@latest install --scope user
npx doct-agents@latest install --scope workspace
```

Chọn platform rõ ràng:

```bash
npx doct-agents@latest install --platform copilot --scope user
npx doct-agents@latest install --platform opencode --scope user
npx doct-agents@latest install --platform all --scope workspace
```

### Cài bằng bunx hoặc pnpm dlx

```bash
bunx doct-agents@latest install --platform opencode --scope user
pnpm dlx doct-agents@latest install --platform all --scope workspace
```

### Cài bằng Python

Windows PowerShell:

```powershell
$installer = Join-Path $env:TEMP "doct-agents-install.py"
Invoke-WebRequest "https://raw.githubusercontent.com/OneTwoTen/doct-agents/main/install.py" -OutFile $installer
py -3 $installer install --platform opencode --scope user
```

macOS/Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/OneTwoTen/doct-agents/main/install.py \
  -o /tmp/doct-agents-install.py
python3 /tmp/doct-agents-install.py install --platform opencode --scope user
```

Node CLI và Python installer có cùng semantics cho `copilot`, `opencode`, `all`, auto-detection, status và uninstall.

## Vị trí cài đặt

| Platform | Scope | Vị trí |
| --- | --- | --- |
| Copilot | `user` | `~/.copilot/agents` |
| Copilot | `workspace` | `.github/agents` |
| OpenCode | `user` | `~/.config/opencode/agents` |
| OpenCode | `workspace` | `.opencode/agents` |

Copilot giữ tên `*.agent.md`. OpenCode nhận file đã render dạng `<agent-name>.md`.

## OpenCode và Playwright MCP

Khi cài platform `opencode`, installer:

1. render toàn bộ source agents sang format OpenCode;
2. map quyền `read/search/edit/execute/agent/...` sang permission tương ứng của OpenCode;
3. giữ `orchestrator` là primary agent và chỉ cho orchestrator gọi các subagent được khai báo;
4. cấu hình browser automation bằng MCP `doct_playwright`;
5. chỉ cho `browser-agent` dùng namespace `doct_playwright_*`.

Browser MCP dùng package chính thức của Microsoft ở isolated mode:

```json
{
  "mcp": {
    "doct_playwright": {
      "type": "local",
      "command": ["npx", "-y", "@playwright/mcp@0.0.78", "--isolated"],
      "enabled": true
    }
  }
}
```

Installer **không overwrite toàn bộ OpenCode config**. Nó chỉ quản lý `mcp.doct_playwright` trong `opencode.json` hoặc `opencode.jsonc`, giữ lại provider, model, plugin, MCP khác và các phần config không liên quan. JSONC comments/trailing comma thông dụng được giữ khi patch entry này.

Nếu `doct_playwright` đã được người dùng sửa sau lần cài gần nhất, update/uninstall mặc định sẽ bảo vệ thay đổi đó. Chỉ dùng `--force` khi muốn thay thế hoặc xóa phần managed đã sửa.

OpenCode output dùng format tương thích với agent/config V1 hiện tại; không phụ thuộc format beta-only của OpenCode 2.

## Cập nhật

Mỗi lần chạy với `@latest`, `npx`, `bunx` hoặc `pnpm dlx` sẽ lấy package mới trước khi chạy:

```bash
npx doct-agents@latest update --scope user
npx doct-agents@latest update --platform opencode --scope user
npx doct-agents@latest update --platform all --scope workspace
```

Installer lưu checksum trong `.doct-agents-manifest.json`. Nếu một managed agent đã bị chỉnh sửa cục bộ, update dừng để tránh mất dữ liệu.

Khi phiên bản mới xóa hoặc đổi tên agent:

- file obsolete còn đúng checksum đã cài sẽ được xóa tự động;
- file obsolete đã chỉnh sửa cục bộ được giữ lại và tiếp tục xuất hiện là `Modified`;
- file unmanaged không bao giờ bị xóa.

`--force` không bỏ qua kiểm tra an toàn đường dẫn. Manifest/path không hợp lệ, target hoặc thư mục cha là symbolic link/junction, manifest là symbolic link hoặc managed agent là symbolic link đều làm installer dừng trước khi copy/xóa file.

Update stage toàn bộ file mới và manifest trước khi thay đổi target. Khi commit gặp lỗi, installer rollback các file đã thay thế; config OpenCode cũng được phục hồi nếu agent installation thất bại.

## Kiểm tra trạng thái

```bash
npx doct-agents@latest status --scope user
npx doct-agents@latest status --platform opencode --scope user
npx doct-agents@latest status --platform all --scope workspace
```

`status` phân biệt:

- `Installed`: managed file còn nguyên như lần cài gần nhất.
- `Modified`: file đã được chỉnh sửa cục bộ.
- `Missing`: file do installer quản lý nhưng đã bị xóa.
- OpenCode còn báo trạng thái Browser MCP config: `installed`, `modified` hoặc `missing`.

Để giữ backward compatibility, `status` **không có `--platform`** chỉ kiểm tra Copilot.

## Gỡ cài đặt

```bash
npx doct-agents@latest uninstall --scope user
npx doct-agents@latest uninstall --platform opencode --scope user
npx doct-agents@latest uninstall --platform all --scope workspace
```

Installer chỉ xóa managed file còn đúng checksum đã cài. File đã chỉnh sửa được giữ lại. Với OpenCode, installer chỉ xóa `mcp.doct_playwright` khi entry đó vẫn đúng giá trị managed; config khác không bị xóa.

Xóa cả managed content đã chỉnh sửa:

```bash
npx doct-agents@latest uninstall --platform opencode --scope user --force
```

Để tránh một lệnh legacy vô tình xóa thêm platform mới, `uninstall` **không có `--platform`** chỉ gỡ Copilot.

## Các tùy chọn CLI

```text
doct-agents [install|update|status|uninstall] [options]

--platform copilot|opencode|all
                         Chọn host platform rõ ràng
--scope user|workspace   Chọn phạm vi cài đặt
--workspace <path>       Chỉ định workspace root
--target <path>          Ghi đè target cho một platform
--force                  Cho phép thay thế/xóa managed content đã sửa
-h, --help               Hiển thị trợ giúp
```

`--target` không đi cùng `--platform all`, vì một đường dẫn không thể đại diện an toàn cho hai layout khác nhau. `--target` mà không có `--platform` giữ semantics cũ và được hiểu là Copilot.

## Dùng với GitHub Copilot

Sau khi cài:

1. Chạy `Developer: Reload Window`.
2. Mở chat mới trong GitHub Copilot Chat.
3. Gõ `/agents` hoặc mở danh sách agent.
4. Chọn `orchestrator` cho task kỹ thuật hoặc `cli-executor` cho task chạy command.

Các worker khác mặc định do orchestrator gọi.

## Dùng với OpenCode

Sau khi cài `--platform opencode`, mở/restart OpenCode trong project tương ứng. `orchestrator` được render là primary agent; các worker không user-invocable là subagent ẩn, còn `cli-executor` có thể dùng trực tiếp hoặc qua orchestrator.

Routing được render theo least privilege:

- `orchestrator`: chỉ được gọi các subagent có trong source allowlist;
- worker: `task` bị deny, nên không gọi ngang hàng;
- `implementation-agent`: có edit nhưng không có bash;
- `cli-executor`: có bash nhưng không có edit;
- `browser-agent`: có `doct_playwright_*`;
- agent khác: browser MCP bị deny.

## Workflow task ngắn: FAST_FIX

`FAST_FIX` dùng khi phạm vi cục bộ, expected behavior rõ và có thể hoàn thành an toàn trong một vòng sửa–review–validate.

```text
DISCOVER
→ PLAN
→ ANALYZE
→ CHANGE
→ VALIDATE
→ DOCS_IMPACT
→ FINALIZE
```

Với code production, orchestrator bắt buộc giao sửa file cho `implementation-agent`. Sau validation, orchestrator đánh giá tác động tài liệu; không tự động sửa README nếu thay đổi không ảnh hưởng tài liệu liên quan.

Ví dụ:

```text
Sửa lỗi campaign eligibility trong hai service này, thêm test hẹp nhất, chạy validation và chỉ cập nhật docs nếu public behavior hoặc vận hành bị thay đổi.
```

## Workflow dài hơi: LONG_RUNNING

`LONG_RUNNING` dùng khi task có nhiều module/domain, nhiều phase phụ thuộc, migration/rollback/rollout hoặc không thể hoàn thành an toàn trong một vòng change–validate.

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

### Roadmap và milestone

Trước implementation, `planning-agent` tạo plan tại:

```text
docs/superpowers/plans/YYYY-MM-DD-<feature>-implementation.md
```

Mỗi milestone phải có objective/dependency, allowed/forbidden files, expected behavior, acceptance criteria, validation plan, docs impact candidates và definition of done. Một plan tối đa 6 milestone; scope lớn hơn phải chia phase độc lập.

### Agent deliberation

Các worker không gọi trực tiếp nhau. Orchestrator làm trung gian để tránh vòng lặp và sửa chồng file:

1. `independent-analysis`: mặc định tối đa 2 agent; agent thứ ba chỉ khi có domain risk rõ như security, dependency hoặc performance.
2. `challenge`: tối đa 2 agent và chỉ khi proposal có mâu thuẫn, migration/rollback hoặc assumption rủi ro.
3. `synthesis`: `planning-agent` tổng hợp requirements, proposal, challenge và decisions thành roadmap.

`architecture-agent` có mode `proposal` và `challenge`.

### Kết quả worker và validation ownership

`Status` là trạng thái thực thi: `completed`, `needs-info`, `blocked`, `failed`. `Outcome` là ý nghĩa kết quả: `passed`, `change-made`, `defect-found`, `validation-failed`, `no-change`.

| Owner | Phạm vi validation |
| --- | --- |
| `test-agent` | Test hẹp mà chính agent vừa thêm hoặc sửa |
| `review-agent` | Tái sử dụng evidence; command hẹp chỉ khi finding quan trọng thiếu evidence |
| `cli-executor` | Build, lint, typecheck, integration test và validation cuối |
| `dependency-agent` | Audit, outdated và dependency tree |
| `performance-agent` | Benchmark và profiling |
| `browser-agent` | Browser runtime và user flow |

Orchestrator chuẩn hóa command signature và không chạy lại fresh successful evidence cho cùng code revision. Handoff context tối đa 10 bullet; summary mặc định tối đa 120 từ.

Validator kiểm tra routing, OpenCode tool renderability, Status/Outcome vocabulary và prompt-size budget: 12.000 ký tự cho orchestrator, 9.000 cho browser-agent và 7.000 cho worker còn lại.

### Chế độ tự động cao

Orchestrator chỉ hỏi người dùng khi thiếu dữ liệu tạo ra nhiều behavior hợp lệ, cần credential/quyền ngoài workspace, thao tác phá hủy, scope drift lớn, conflict không thể giải quyết, validation bắt buộc không chạy được hoặc retry budget đã hết mà failure signature không đổi.

### Checkpoint

Sau mỗi milestone, plan giữ completed/current milestone, validation evidence, decisions, docs impact, remaining risks và next milestone. Khi mở chat mới, tiếp tục từ milestone đầu tiên chưa hoàn thành thay vì làm lại phần đã checkpoint.

## Documentation impact lifecycle

Mỗi code-changing milestone đánh giá:

```text
Status: required | not-required | uncertain
Changed behavior
Affected audience
Candidate docs
Evidence
Recommended updates
```

`docs-agent` chỉ sửa khi impact là `required`, hoặc đọc/search thêm khi `uncertain`.

## Prompt mẫu

### Review và sửa code

```text
Review module này theo hướng correctness và test gap. Chỉ sửa finding high/critical, sau đó chạy test hẹp nhất để validate.
```

### Chạy project

```text
Chạy project trong thư mục backend, tự tìm command phù hợp từ cấu hình repo và báo URL hoặc lỗi quyết định.
```

### Kiểm tra UI

```text
Mở http://localhost:3000, kiểm tra luồng đăng nhập, chụp screenshot ở bước lỗi và báo expected/actual.
```

### Triển khai dài hơi

```text
Triển khai tính năng này theo LONG_RUNNING. Tự trích xuất requirements, cho architecture/security/performance phân tích độc lập nếu liên quan, phản biện proposal, tạo roadmap tối đa 6 milestone và thực hiện tự động. Sau mỗi milestone phải review, validate, đánh giá docs impact và cập nhật checkpoint.
```

## Agent chính

| Agent | Vai trò |
| --- | --- |
| `orchestrator` | Route FAST_FIX/LONG_RUNNING, quản lý state, budget, deliberation và checkpoint |
| `architecture-agent` | Đề xuất hoặc phản biện kiến trúc |
| `planning-agent` | Tạo roadmap, milestone, file ownership và checkpoint |
| `implementation-agent` | Sửa bug, triển khai production logic |
| `cli-executor` | Chạy terminal/CLI và thu evidence |
| `review-agent` | Review quality, milestone và final integration |
| `refactor-agent` | Refactor nhỏ, giữ public behavior |
| `test-agent` | Viết/cập nhật test và validation hẹp |
| `browser-agent` | Kiểm tra UI/runtime bằng browser automation của host |
| `security-agent` | Security review read-only |
| `dependency-agent` | Audit dependency, lockfile và vulnerability |
| `performance-agent` | Benchmark và bottleneck analysis |
| `research-agent` | Tra cứu thông tin kỹ thuật ngoài repo |
| `docs-agent` | Author docs hoặc impact-update |
| `req-extractor` | Chuẩn hóa requirements và dependency |
| `aggregator-agent` | Khử trùng lặp findings từ nhiều worker |
| `agent-authoring` | Tạo/cập nhật custom agent và skill |

## Browser tools

### GitHub Copilot

Bật VS Code Browser chat tools:

```json
{
  "workbench.browser.enableChatTools": true
}
```

### OpenCode

Không cần copy browser prompt riêng. Installer tự thêm `doct_playwright` MCP và render `browser-agent` để dùng namespace MCP đó trong isolated browser context.

## Dùng như Git submodule

```bash
git submodule add https://github.com/OneTwoTen/doct-agents.git third_party/doct-agents
git submodule update --init --recursive
python third_party/doct-agents/install.py install --scope workspace \
  --source-dir third_party/doct-agents/agents
```

Có thể thêm `--platform opencode` hoặc `--platform all` vào lệnh Python trên.

## Phát triển và kiểm tra

Chạy toàn bộ test Node, test Python, validator, package dry-run và smoke test từ tarball thực tế:

```bash
npm run check
```

Các lệnh hẹp hơn:

```bash
npm test
npm run test:python
npm run validate
npm run pack:check
npm run smoke:package
RELEASE_TAG=v0.3.0 npm run release:check
```

CI chạy ba lane: Node 18/Python 3.9 trên Ubuntu, runtime hiện tại trên Ubuntu và runtime hiện tại trên Windows. Packaged smoke test kiểm tra cả lifecycle Copilot legacy và OpenCode workspace + Playwright MCP.

## Publish lên npm

Package dùng tên `doct-agents` và executable cùng tên. Workflow `.github/workflows/publish-npm.yml` publish khi tạo GitHub Release hoặc chạy thủ công với input tag bắt buộc.

Quy trình release:

1. Tăng `version` trong `package.json`.
2. Merge thay đổi vào `main`.
3. Tạo GitHub Release cùng version, ví dụ `v0.3.0`; hoặc chạy workflow thủ công và nhập đúng tag đã tồn tại.
4. Workflow checkout chính tag đó và chạy `npm run check`.
5. Workflow xác nhận tag đúng bằng `v${package.json.version}` rồi mới chạy `npm publish`.

## Cấu trúc repo

```text
.
├── agents/                       # Source of truth của agent prompts
├── bin/cli.js                    # npm executable
├── bin/doct-agents.js            # Managed-file core, renderer và config patcher
├── bin/platform-runner.js        # Platform selection và OpenCode transaction orchestration
├── docs/superpowers/             # Design specs và implementation plans
├── install.py                    # Standalone Python installer parity
├── package.json                  # npm package metadata và bin mapping
├── scripts/check_release.py      # Kiểm tra release tag/package version
├── scripts/smoke_package.mjs     # Smoke tarball + Copilot/OpenCode lifecycle
├── scripts/validate_agents.py    # Agent contract/OpenCode compatibility validator
├── tests/                        # Node và Python tests
├── .github/workflows/            # Validate và publish npm
└── .vscode/                      # Cấu hình phát triển repo
```

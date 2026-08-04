# doct-agents

`doct-agents` là bộ custom agents cho GitHub Copilot trong VS Code, hỗ trợ review, sửa code, test, chạy CLI, browser, security, dependency, performance và triển khai yêu cầu dài hơi theo roadmap.

## Cài nhanh

Yêu cầu:

- VS Code có GitHub Copilot Chat.
- Một trong các runtime: Node.js 18+, Bun hoặc Python 3.9+.

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

Installer lưu checksum trong `.doct-agents-manifest.json`. Nếu một agent hiện tại đã được chỉnh sửa cục bộ, update sẽ dừng để tránh mất dữ liệu.

Khi phiên bản mới xóa hoặc đổi tên một agent:

- file obsolete còn đúng checksum đã cài sẽ được xóa tự động;
- file obsolete đã chỉnh sửa cục bộ được giữ lại và tiếp tục xuất hiện là `Modified` trong `status`;
- file unmanaged không bao giờ bị xóa.

Chỉ dùng `--force` khi thật sự muốn thay thế chỉnh sửa cục bộ của agent vẫn còn trong package:

```bash
npx doct-agents@latest update --scope user --force
```

`--force` không bỏ qua kiểm tra an toàn đường dẫn. Manifest có path không hợp lệ, target hoặc một thư mục cha là symbolic link/junction, manifest là symbolic link hoặc agent được quản lý là symbolic link đều làm installer dừng trước khi copy/xóa file.

Update stage toàn bộ agent mới và manifest trước khi thay đổi target. Khi commit gặp lỗi, installer rollback các file đã thay thế; nếu rollback cũng lỗi, thư mục backup được giữ lại và đường dẫn được báo trong error.

Sau khi update agent, chạy `Developer: Reload Window` và mở chat mới để VS Code nạp lại frontmatter, tool và subagent routing.

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
2. Mở một chat mới trong GitHub Copilot Chat.
3. Gõ `/agents` hoặc mở danh sách agent ở cuối ô chat.
4. Chọn:
   - `orchestrator` cho task cần phân tích, sửa, review, validate hoặc triển khai dài hơi.
   - `cli-executor` cho chạy project, test, build, lint, migrate, seed hoặc script.

Các worker khác mặc định được orchestrator gọi, không cần chọn thủ công.

## Workflow task ngắn: FAST_FIX

`FAST_FIX` dùng khi phạm vi cục bộ, expected behavior rõ và có thể hoàn thành an toàn trong một vòng sửa–review–validate.

Luồng điển hình:

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

`LONG_RUNNING` dùng khi task có nhiều module/domain, nhiều phase phụ thuộc nhau, migration/rollout, yêu cầu roadmap hoặc không thể hoàn thành an toàn trong một vòng change–validate.

Luồng:

```text
DISCOVER
→ REQUIREMENTS
→ REQUIREMENTS_REVIEW
→ DELIBERATE
→ DESIGN
→ DESIGN_REVIEW
→ PLAN
→ SELECT_EXECUTOR
→ MILESTONE_LOOP
    → PREPARE_MILESTONE
    → IMPLEMENT
    → REVIEW
    → VALIDATE
    → DOCS_IMPACT
    → CHECKPOINT
→ FINAL_REVIEW
→ FINAL_VALIDATE
→ FEATURE_IMPACT
→ UPDATE_FEATURE_REGISTRY
→ FINALIZE
```

### Spec workspace

LONG_RUNNING không lưu canonical state trong plan của một executor. `planning-agent` tạo workspace được commit cùng project:

```text
.doct/specs/<feature>/
├── requirements.md   # WHAT
├── design.md         # HOW
├── tasks.md          # WORK
└── progress.md       # STATE
```

`requirements.md` chứa goal, non-goals, requirements, constraints và acceptance criteria. `design.md` chứa architecture decisions, interfaces, migration/rollback, risks và validation strategy. `tasks.md` chứa roadmap/milestone, dependencies, allowed/forbidden files và definition of done. `progress.md` chỉ giữ runtime/checkpoint state để resume.

Một roadmap có tối đa 6 milestone. Scope lớn hơn phải chia thành phase độc lập.

### Feature catalog

Specs mô tả quá trình thay đổi, nhưng current-state capability được tổng hợp riêng:

```text
.doct/project.md
.doct/features/index.md
.doct/features/<feature>.md
```

`FEATURE_IMPACT` chạy sau final validation. Nếu capability thay đổi, `docs-agent` mode `feature-update` cập nhật feature index và feature record. Feature registry không thay thế README, API docs hoặc runbook.

### Agent deliberation

Các worker không gọi trực tiếp nhau. Orchestrator làm trung gian để tránh vòng lặp và sửa chồng file:

1. `independent-analysis`: mặc định tối đa 2 agent; chỉ gọi agent thứ ba khi có domain risk rõ như security, dependency hoặc performance.
2. `challenge`: tối đa 2 agent và chỉ chạy khi proposal có mâu thuẫn, migration/rollback hoặc assumption rủi ro.
3. `synthesis`: requirements/design/tasks được cập nhật theo đúng source-of-truth tương ứng.

`architecture-agent` hỗ trợ hai mode:

- `proposal`: đề xuất tối đa 3 options và trade-off.
- `challenge`: tìm coupling, failure mode, migration/rollback risk và validation gap.

### Executor boundary

Orchestrator chọn executor sau khi canonical spec ổn định. Superpowers, OpenCode hoặc native execution chỉ sở hữu mechanics như worktree, task dispatch và local runner; doct-agents vẫn sở hữu milestone contract, review budget, validation evidence và checkpoint.

### Kết quả worker và validation ownership

`Status` biểu diễn trạng thái thực thi của worker: `completed`, `needs-info`, `blocked` hoặc `failed`. `Outcome` biểu diễn ý nghĩa của kết quả: `passed`, `change-made`, `defect-found`, `validation-failed` hoặc `no-change`. Vì vậy `Status: completed` không tự động có nghĩa toàn bộ task đã thành công.

Mỗi command có một owner mặc định cho cùng code revision:

| Owner | Phạm vi validation |
| --- | --- |
| `test-agent` | Test hẹp mà chính agent vừa thêm hoặc sửa |
| `review-agent` | Tái sử dụng evidence; chỉ chạy command hẹp khi finding quan trọng còn thiếu evidence |
| `cli-executor` | Build, lint, typecheck, integration test và validation cuối |
| `dependency-agent` | Audit, outdated và dependency tree |
| `performance-agent` | Benchmark và profiling |
| `browser-agent` | Browser runtime và user flow |

Orchestrator chuẩn hóa command signature và không chạy lại command đã có fresh successful evidence cho cùng code revision. Handoff context giới hạn tối đa 10 bullet, ưu tiên file/symbol/evidence reference và không copy nguyên worker result hoặc toàn bộ lịch sử. Summary mặc định tối đa 120 từ; finding/change/domain fields chỉ xuất hiện khi có dữ liệu.

Validator kiểm tra Outcome vocabulary và prompt-size budget để ngăn agent prompt phình không kiểm soát. Budget hiện tại là 12.000 ký tự cho orchestrator, 9.000 cho browser-agent và 7.000 cho các worker còn lại.

### Chế độ tự động cao

Orchestrator tự tiếp tục giữa các milestone. Nó chỉ hỏi người dùng khi:

- thiếu thông tin tạo ra nhiều behavior hợp lệ khác nhau;
- cần credential hoặc quyền ngoài workspace;
- thao tác phá hủy hoặc không thể rollback;
- scope drift lớn so với roadmap;
- conflict code/spec không thể giải quyết an toàn;
- validation bắt buộc không thể chạy;
- retry budget đã hết nhưng failure signature không đổi.

### Checkpoint và tiếp tục ở chat mới

Sau mỗi milestone, `progress.md` được cập nhật với completed/current work, validation evidence, decision changes, docs impact, feature impact candidates, remaining risks và next work.

Khi cần mở chat mới, dùng prompt:

```text
Tiếp tục triển khai LONG_RUNNING tại .doct/specs/<feature>/. Đọc progress.md trước, không làm lại milestone/task đã completed và tiếp tục từ work đầu tiên chưa hoàn thành.
```

## Documentation impact lifecycle

Mọi code-changing milestone đều có assessment:

```text
Status: required | not-required | uncertain
Changed behavior
Affected audience
Candidate docs
Evidence
Recommended updates
```

`docs-agent` chỉ được gọi để sửa khi impact là `required`, hoặc đọc/search thêm khi `uncertain`.

Thường cần cập nhật docs khi thay đổi:

- API/error/integration contract;
- config, environment variable hoặc feature flag;
- build, test, deploy, migration, rollback hoặc vận hành;
- user-visible behavior;
- architecture/data flow quan trọng;
- onboarding, local development hoặc public command.

Không cần cập nhật docs cho refactor nội bộ giữ nguyên contract, local variable rename, test-only change, format/lint hoặc tối ưu nội bộ không đổi vận hành.

`docs-agent` có ba mode:

- `author`: task thuần tài liệu.
- `impact-update`: chỉ sửa section/file thực sự bị ảnh hưởng và liệt kê tài liệu đã kiểm tra nhưng không cần sửa.
- `feature-update`: cập nhật `.doct/features` từ validated feature impact synthesis.

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
Triển khai tính năng này theo LONG_RUNNING. Tự trích xuất requirements, review ambiguity, deliberation kiến trúc khi cần, tạo `.doct/specs/<feature>/`, chọn executor phù hợp và thực hiện tối đa 6 milestone. Sau mỗi milestone phải review, validate, đánh giá docs/feature impact và checkpoint. Chỉ hỏi tôi khi bị blocked theo autonomous blocker policy.
```

## Agent chính

| Agent | Vai trò |
| --- | --- |
| `orchestrator` | Route FAST_FIX/LONG_RUNNING, quản lý state, budget, deliberation và checkpoint |
| `architecture-agent` | Đề xuất hoặc phản biện kiến trúc cho yêu cầu dài hơi |
| `planning-agent` | Tạo/duy trì requirements, design, tasks và progress cho LONG_RUNNING |
| `implementation-agent` | Sửa bug, triển khai logic production và trả docs impact candidates |
| `cli-executor` | Chạy terminal/CLI, thu exit code và log quyết định |
| `review-agent` | Review qa/quality, milestone và final cross-milestone |
| `refactor-agent` | Refactor nhỏ, an toàn, không đổi public behavior |
| `test-agent` | Viết/cập nhật test và chạy validation hẹp |
| `browser-agent` | Kiểm tra UI/runtime bằng VS Code Browser tools |
| `security-agent` | Security review read-only |
| `dependency-agent` | Audit dependency, lockfile và vulnerability |
| `performance-agent` | Benchmark và phân tích bottleneck dựa trên số liệu |
| `research-agent` | Tra cứu thông tin kỹ thuật ngoài repo |
| `docs-agent` | Author docs, impact-update hoặc feature-update từ validated evidence |
| `req-extractor` | Chuẩn hóa requirements, dependency và milestone candidates |
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
RELEASE_TAG=v0.2.1 npm run release:check
```

Validator còn kiểm tra quyền subagent, `edit + execute`, Status/Outcome vocabulary và prompt-size budget. CI chạy ba lane: Node 18/Python 3.9 trên Ubuntu, runtime hiện tại trên Ubuntu và runtime hiện tại trên Windows.

## Publish lên npm

Package dùng tên `doct-agents` và executable cùng tên. Workflow `.github/workflows/publish-npm.yml` publish khi tạo GitHub Release hoặc chạy thủ công với input tag bắt buộc.

Quy trình release:

1. Tăng `version` trong `package.json`.
2. Merge thay đổi vào `main`.
3. Tạo GitHub Release cùng version, ví dụ `v0.2.1`; hoặc chạy workflow thủ công và nhập đúng tag đã tồn tại.
4. Workflow checkout chính tag đó và chạy `npm run check`.
5. Workflow xác nhận tag đúng bằng `v${package.json.version}` rồi mới chạy `npm publish`.

Nếu workflow vẫn dùng token cho publish, repository cần secret `NPM_TOKEN`. Sau khi Trusted Publishing được cấu hình, có thể dùng OIDC thay token dài hạn.

## Cấu trúc repo

```text
.
├── .doct/                        # Project/spec/feature knowledge cho LONG_RUNNING
├── agents/                       # Agent source và nội dung npm package
├── bin/cli.js                    # npm executable cho npx, bunx và pnpm dlx
├── bin/doct-agents.js            # CLI implementation và installer logic
├── docs/superpowers/             # Historical design specs và implementation plans
├── install.py                    # Installer Python fallback
├── package.json                  # npm package metadata và bin mapping
├── scripts/check_release.py      # Kiểm tra release tag và package version
├── scripts/smoke_package.mjs     # Smoke test tarball và executable đã đóng gói
├── scripts/validate_agents.py    # Validator cấu hình agent
├── tests/                        # Node và Python unit tests
├── .github/workflows/            # Validate và publish npm
└── .vscode/                      # Cấu hình phát triển repo
```
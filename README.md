# doct-agents

`doct-agents` là bộ custom agents cho GitHub Copilot trong VS Code, hỗ trợ review, sửa code, test, chạy CLI, browser, security, dependency, performance và triển khai yêu cầu dài hơi theo lộ trình.

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

`bunx` chạy executable khai báo trong trường `bin` của `package.json`, tương tự `npx`.

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

Installer lưu checksum trong `.doct-agents-manifest.json`. Nếu agent hiện tại đã được chỉnh sửa cục bộ, update sẽ dừng để tránh mất dữ liệu.

Khi phiên bản mới xóa hoặc đổi tên agent:

- file obsolete còn đúng checksum đã cài sẽ được xóa tự động;
- file obsolete đã chỉnh sửa cục bộ được giữ lại và tiếp tục xuất hiện là `Modified` trong `status`;
- file unmanaged không bao giờ bị xóa.

Chỉ dùng `--force` khi thật sự muốn thay thế chỉnh sửa cục bộ của agent vẫn còn trong package:

```bash
npx doct-agents@latest update --scope user --force
```

`--force` không bỏ qua kiểm tra an toàn đường dẫn. Manifest/path không hợp lệ, symbolic link hoặc junction ở target/parent đều làm installer dừng trước khi copy/xóa file.

Update stage toàn bộ agent mới và manifest trước khi thay đổi target. Khi commit gặp lỗi, installer rollback file đã thay thế; nếu rollback cũng lỗi, thư mục backup được giữ lại và đường dẫn được báo trong error.

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
2. Mở chat mới trong GitHub Copilot Chat.
3. Gõ `/agents` hoặc mở danh sách agent ở cuối ô chat.
4. Chọn `orchestrator` cho task cần phân tích/sửa/review/validate/triển khai dài hơi, hoặc `cli-executor` khi chỉ cần chạy project/test/build/lint/migrate/seed/script.

Các worker khác mặc định được orchestrator gọi, không cần chọn thủ công.

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

Với code production, orchestrator bắt buộc giao sửa file cho `implementation-agent`. Với web/UI, `implementation-agent` có thể dùng trực tiếp Browser tools trong cùng browser-driven loop `reproduce → inspect → edit → browser verify`; không cần handoff qua `browser-agent` chỉ để thao tác browser. `browser-agent` dành cho independent validation, reproduction-only, regression/responsive check hoặc khi cần evidence tách khỏi writer. Build, lint, typecheck và final integration validation vẫn thuộc `cli-executor`.

Sau validation, orchestrator đánh giá tác động tài liệu; không tự động sửa README nếu thay đổi không ảnh hưởng tài liệu liên quan.

Ví dụ backend:

```text
Sửa lỗi campaign eligibility trong hai service này, thêm test hẹp nhất, chạy validation và chỉ cập nhật docs nếu public behavior hoặc vận hành bị thay đổi.
```

Ví dụ web/UI:

```text
Sửa lỗi nút Save không hoạt động. Reproduce bằng integrated browser, sửa trong scope liên quan và browser-verify lại cùng flow trước khi trả kết quả.
```

## Workflow dài hơi: LONG_RUNNING

`LONG_RUNNING` dùng khi task có nhiều module/domain, nhiều phase phụ thuộc, migration/rollout, yêu cầu roadmap hoặc không thể hoàn thành an toàn trong một change–validate loop.

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
    → CHECKLIST_RECONCILE
    → CHECKPOINT
→ FINAL_REVIEW
→ FINAL_VALIDATE
→ FEATURE_IMPACT
→ UPDATE_FEATURE_REGISTRY
→ FINALIZE
```

### Spec workspace

LONG_RUNNING không lưu canonical state trong plan của executor. `planning-agent` tạo workspace được commit cùng project:

```text
.doct/specs/<feature>/
├── requirements.md   # WHAT
├── design.md         # HOW
├── tasks.md          # WORK
└── progress.md       # STATE
```

- `requirements.md`: mục tiêu, ngoài phạm vi, requirements, constraints và Acceptance criteria.
- `design.md`: Architecture decisions, interfaces, migration/rollback, risks và Validation strategy.
- `tasks.md`: roadmap/milestone, dependency, allowed/forbidden files và **authoritative execution checklist**.
- `progress.md`: current state, validation evidence, blockers/deferred và next work; không sao chép checklist.

Một roadmap có tối đa 6 milestone. Scope lớn hơn phải tách thành phase độc lập.

### Checklist và checkpoint

Mỗi executable task trong `tasks.md` có ID ổn định như `M2-T1` và dùng Markdown checkbox.

- `- [ ]`: chưa đủ evidence để kết luận hoàn tất.
- `- [x]`: chỉ được tick sau `CHECKLIST_RECONCILE` khi có implementation evidence, fresh required validation và không còn finding critical/high liên quan.
- Worker trả `Status: completed`, `Outcome: change-made`, nói "done" hoặc chỉ có file changed **không đủ** để tick.
- Item `blocked`/`deferred` giữ `[ ]` và ghi reason rõ trong `tasks.md` + `progress.md`.
- Nếu evidence mất hiệu lực, orchestrator phải downgrade `[x]` về `[ ]`.
- Milestone chỉ completed khi mọi required checklist item đã `[x]`.

`CHECKPOINT` chỉ được ghi sau `CHECKLIST_RECONCILE`. Khi resume, đọc `progress.md` để biết vị trí hiện tại rồi đối chiếu authoritative checkbox state trong `tasks.md`; repository evidence thắng memory/prose nếu có mâu thuẫn.

### Feature catalog

Specs mô tả quá trình thay đổi; capability hiện tại được tổng hợp riêng:

```text
.doct/project.md
.doct/features/index.md
.doct/features/<feature>.md
```

`.doct/project.md` chỉ mô tả architecture/knowledge model tương đối tĩnh. Danh sách capability nằm ở `.doct/features/index.md` để tránh duplicate và drift.

`FEATURE_IMPACT` chạy sau final validation. Nếu capability thay đổi, `docs-agent` mode `feature-update` cập nhật feature index và feature record. Feature registry không thay thế README, API docs hoặc runbook.

### Agent deliberation

Các worker không gọi trực tiếp nhau. Orchestrator làm trung gian để tránh vòng lặp và sửa chồng file:

1. `independent-analysis`: mặc định tối đa 2 agent; chỉ gọi agent thứ ba khi có domain risk rõ như security, dependency hoặc performance.
2. `challenge`: tối đa 2 agent và chỉ chạy khi proposal có mâu thuẫn, migration/rollback hoặc assumption rủi ro.
3. `synthesis`: requirements/design/tasks được cập nhật theo đúng source-of-truth tương ứng.

`architecture-agent` có mode `proposal` và `challenge`.

### Ranh giới executor

Orchestrator chọn executor sau khi canonical spec ổn định. Superpowers, OpenCode hoặc native execution chỉ sở hữu mechanics như worktree, task dispatch và local runner; doct-agents vẫn sở hữu milestone contract, checklist completion, review budget, validation evidence và checkpoint.

### Kết quả worker và validation ownership

`Status` biểu diễn trạng thái thực thi: `completed`, `needs-info`, `blocked`, `failed`. `Outcome` biểu diễn ý nghĩa kết quả: `passed`, `change-made`, `defect-found`, `validation-failed`, `no-change`. `Status: completed` không tự động nghĩa là task đã thành công.

| Owner | Phạm vi validation |
| --- | --- |
| `implementation-agent` | Browser runtime evidence hẹp trong web/UI change loop; không sở hữu final pipeline |
| `test-agent` | Test hẹp mà chính agent vừa thêm/sửa |
| `review-agent` | Tái sử dụng evidence; chỉ chạy command hẹp khi finding quan trọng thiếu evidence |
| `cli-executor` | Build, lint, typecheck, integration test và validation cuối |
| `dependency-agent` | Audit, outdated và dependency tree |
| `performance-agent` | Benchmark và profiling |
| `browser-agent` | Independent browser validation, reproduction-only và user-flow evidence tách khỏi writer |

Orchestrator chuẩn hóa command signature và reuse fresh successful evidence cho cùng validation revision. Metadata-only reconciliation trong `.doct/` không tự làm evidence stale.

Validator kiểm tra Outcome vocabulary, quyền `edit + execute` và prompt-size budget. `implementation-agent` dùng `execute` chỉ cho dev-server/runtime loop hẹp; final pipeline vẫn thuộc `cli-executor`.

### Chế độ tự động cao

Orchestrator tự tiếp tục giữa các milestone và chỉ hỏi user khi thiếu dữ liệu tạo nhiều behavior hợp lệ, cần credential/quyền ngoài workspace, thao tác phá hủy, scope drift lớn, architecture/spec conflict không thể giải quyết, validation bắt buộc không chạy được hoặc retry budget đã hết.

### Tiếp tục ở chat mới

```text
Tiếp tục triển khai LONG_RUNNING tại .doct/specs/<feature>/. Đọc progress.md trước, đối chiếu checklist trong tasks.md, không làm lại item đã [x] nếu evidence vẫn hợp lệ và tiếp tục từ item đầu tiên chưa hoàn thành.
```

## Documentation impact lifecycle

Mọi code-changing milestone đều có assessment với các key:

```text
Status: required | not-required | uncertain
Changed behavior
Affected audience
Candidate docs
Evidence
Recommended updates
```

`docs-agent` chỉ sửa khi impact là `required`, hoặc đọc/search thêm khi `uncertain`.

Thường cần cập nhật docs khi API/error/integration contract, config/flag, build/deploy/migration/rollback, user-visible behavior, architecture/data flow, onboarding hoặc public command thay đổi. Refactor nội bộ, test-only, format/lint hoặc tối ưu không đổi vận hành thường không cần docs.

`docs-agent` có ba mode:

- `author`: task thuần tài liệu.
- `impact-update`: cập nhật tài liệu bị ảnh hưởng.
- `feature-update`: cập nhật `.doct/features` từ validated `FEATURE_IMPACT` synthesis.

## Prompt mẫu

### Review và sửa code

```text
Review module này theo hướng correctness và test gap. Chỉ sửa finding high/critical, sau đó chạy test hẹp nhất để validate.
```

### Chạy project

```text
Chạy project trong thư mục backend, tự tìm command phù hợp từ cấu hình repo và báo URL hoặc lỗi quyết định.
```

### Sửa và kiểm tra UI trong cùng loop

```text
Sửa lỗi form checkout này. Dùng integrated browser để reproduce, inspect state cần thiết, sửa code trong scope và verify lại cùng user flow. Chỉ gọi browser-agent nếu cần independent validation sau khi sửa.
```

### Chỉ kiểm tra UI, không sửa code

```text
Mở http://localhost:3000, kiểm tra luồng đăng nhập, chụp screenshot ở bước lỗi và báo expected/actual. Đây là browser-only validation, không sửa code.
```

### Triển khai dài hơi

```text
Triển khai tính năng này theo LONG_RUNNING. Tạo .doct/specs/<feature>/, dùng checklist có evidence gate, chọn executor phù hợp và thực hiện tối đa 6 milestone. Sau mỗi milestone review, validate, đánh giá docs/feature impact, reconcile checklist rồi checkpoint. Chỉ hỏi tôi khi bị blocked theo autonomous blocker policy.
```

## Agent chính

| Agent | Vai trò |
| --- | --- |
| `orchestrator` | Route FAST_FIX/LONG_RUNNING, quản lý lifecycle, budget, checklist reconciliation và checkpoint; không sở hữu Browser tools |
| `architecture-agent` | Đề xuất hoặc phản biện kiến trúc |
| `planning-agent` | Tạo/duy trì requirements, design, tasks/checklist và progress |
| `implementation-agent` | Sửa production code; với web/UI có thể tự reproduce và browser-verify |
| `cli-executor` | Chạy terminal/CLI và sở hữu final build/lint/typecheck/integration validation |
| `review-agent` | Review quality, milestone và final cross-milestone |
| `refactor-agent` | Refactor nhỏ, an toàn, không đổi public behavior |
| `test-agent` | Viết/cập nhật test và chạy validation hẹp |
| `browser-agent` | Independent UI/runtime validation read-only; không phải browser gateway bắt buộc |
| `security-agent` | Security review read-only |
| `dependency-agent` | Audit dependency, lockfile và vulnerability |
| `performance-agent` | Benchmark và phân tích bottleneck |
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

Browser capability dùng mô hình hybrid:

- `implementation-agent` dùng trực tiếp `openBrowserPage`, `navigatePage`, `readPage`, `clickElement`, `hoverElement`, `dragElement`, `typeInPage`, `handleDialog`, `screenshotPage`, `runPlaywrightCode` khi web/UI change cần reproduce hoặc verify runtime.
- `browser-agent` có cùng Browser tool set nhưng giữ read-only để làm independent validation, reproduction-only, regression/responsive flow và evidence tách khỏi writer.
- `orchestrator` không có Browser tools.
- `runPlaywrightCode` chỉ dùng khi primitive Browser tools không đủ.
- `implementation-agent` chỉ dùng `execute` cho dev-server/runtime command hẹp; build/lint/typecheck/final integration vẫn giao `cli-executor`.

Nếu cần session/login đang có trong tab hiện tại, share tab với agent trước. Agent không nên tự tạo workaround đăng nhập bằng profile cá nhân hoặc thay đổi production data khi chưa được phép.

## Dùng như Git submodule

```bash
git submodule add https://github.com/OneTwoTen/doct-agents.git third_party/doct-agents
git submodule update --init --recursive
python third_party/doct-agents/install.py install --scope workspace \
  --source-dir third_party/doct-agents/agents
```

## Phát triển và kiểm tra

Chạy toàn bộ test Node/Python, validator, package dry-run và smoke test:

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

CI chạy ba lane: Node 18/Python 3.9 trên Ubuntu, runtime hiện tại trên Ubuntu và runtime hiện tại trên Windows.

## Publish lên npm

Package dùng tên `doct-agents` và executable cùng tên. Workflow `.github/workflows/publish-npm.yml` publish khi tạo GitHub Release hoặc chạy thủ công với input tag bắt buộc.

Quy trình release:

1. Tăng `version` trong `package.json`.
2. Merge thay đổi vào `main`.
3. Tạo GitHub Release cùng version, ví dụ `v0.2.1`, hoặc chạy workflow thủ công với tag đã tồn tại.
4. Workflow checkout tag và chạy `npm run check`.
5. Workflow xác nhận tag bằng `v${package.json.version}` rồi mới `npm publish`.

Nếu workflow vẫn dùng token, repository cần secret `NPM_TOKEN`. Sau khi Trusted Publishing được cấu hình có thể dùng OIDC.

## Cấu trúc repo

```text
.
├── .doct/                        # Project/spec/feature knowledge cho LONG_RUNNING
├── agents/                       # Agent source và nội dung npm package
├── bin/cli.js                    # npm executable
├── bin/doct-agents.js            # CLI implementation và installer logic
├── docs/superpowers/             # Historical specs/plans/checkpoints
├── install.py                    # Installer Python fallback
├── package.json                  # npm package metadata
├── scripts/                      # Validator/release/smoke scripts
├── tests/                        # Node và Python unit tests
├── .github/workflows/            # Validate và publish npm
└── .vscode/                      # Cấu hình phát triển repo
```

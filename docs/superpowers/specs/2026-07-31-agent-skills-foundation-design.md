# Agent Skills Foundation Design

## Goal

Bổ sung Agent Skills thành customization hạng nhất trong `doct-agents`: được đóng gói, cài đặt, cập nhật, kiểm tra, gỡ bỏ và định tuyến theo workflow/ngôn ngữ/framework mà không làm phình prompt agent hoặc phá vỡ lifecycle installer hiện tại.

## Research basis

Thiết kế dựa trên tài liệu chính thức hiện hành của VS Code, GitHub Copilot và Agent Skills open standard:

- VS Code discover project skills tại `.github/skills`, `.claude/skills`, `.agents/skills`; personal skills tại `~/.copilot/skills`, `~/.claude/skills`, `~/.agents/skills`.
- Khi bắt đầu, runtime chỉ đọc `name` và `description`. Toàn bộ `SKILL.md` chỉ được nạp khi task phù hợp hoặc người dùng gọi slash command; resource chỉ được đọc khi skill tham chiếu đến.
- Tên skill phải là lowercase kebab-case, tối đa 64 ký tự và trùng với thư mục cha trực tiếp. Vì vậy taxonomy không được biểu diễn bằng nested namespace trong tên runtime.
- VS Code custom-agent frontmatter hiện không có trường `skills`. Skill không được preload cố định theo agent; composition dựa trên discovery/activation hoặc slash command.
- Skill có thể chứa `scripts`, `references`, `assets` và resource khác. Installer phải quản lý cây file, không chỉ một file Markdown.

Primary references:

- https://code.visualstudio.com/docs/agent-customization/agent-skills
- https://code.visualstudio.com/docs/agent-customization/custom-agents
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- https://agentskills.io/

## Current-state findings

Repo hiện chỉ sản phẩm hóa custom agents:

- `package.json` chỉ publish `agents`, `bin`, README và LICENSE.
- Node/Python installer chỉ tìm `*.agent.md` trong một source directory phẳng.
- Default target chỉ có `~/.copilot/agents` hoặc `.github/agents`.
- Manifest schema 1 chỉ chấp nhận basename kết thúc bằng `.agent.md`; nested path bị từ chối.
- Transaction staging/rollback chỉ hoạt động trên một target root.
- `scripts/validate_agents.py` chỉ kiểm tra agent frontmatter, tool boundary, result vocabulary và prompt budget.
- `agent-authoring` phân biệt đúng agent và skill nhưng chưa có lifecycle thực tế cho skill.

Chỉ thêm `skills` vào npm package sẽ không đủ: installer, manifest, transaction, validator, smoke test, Python parity và tài liệu đều phải thay đổi.

## Options considered

### Option A — Install skills bằng công cụ ngoài repo

Giữ installer agent hiện tại và hướng dẫn người dùng dùng `gh skill` hoặc copy thủ công.

Ưu điểm:

- Ít code thay đổi.
- Không cần nâng manifest.

Nhược điểm:

- `doct-agents install/update/status/uninstall` không còn là lifecycle thống nhất.
- Không có checksum protection, rollback và parity Node/Python cho skill.
- Version agent và skill dễ lệch nhau.

Không chọn.

### Option B — Một central manifest cho toàn bộ customization

Đặt một manifest ở `~/.copilot` hoặc `.github`, quản lý đồng thời agents và skills.

Ưu điểm:

- Một nguồn trạng thái duy nhất.
- Dễ biểu diễn package version.

Nhược điểm:

- Thay đổi vị trí manifest hiện có.
- Migration và rollback phức tạp hơn cần thiết.
- Custom target ở các filesystem khác nhau trở nên khó xử lý.

Không chọn cho foundation release.

### Option C — Hai target/manifests, một package-level transaction

Giữ agent và skill tại đúng default location của VS Code. Mỗi target có manifest riêng, nhưng command chuẩn bị và commit cả hai component trong một transaction có rollback phối hợp.

Ưu điểm:

- Đúng runtime convention.
- Backward compatible với agent target hiện có.
- Component độc lập nhưng version package vẫn được cập nhật đồng bộ.
- Có thể cài chỉ agents hoặc chỉ skills.

Nhược điểm:

- Cần generic hóa installer ở cả Node và Python.
- Phải quản lý nested path và rollback nhiều root.

**Chosen approach: Option C.**

## Source layout

Skill runtime directories phải phẳng; taxonomy được lưu riêng trong catalog.

```text
agents/
  orchestrator.agent.md
  review-agent.agent.md
  ...

skills/
  catalog.json
  repository-discovery/
    SKILL.md
  code-review/
    SKILL.md
  verification-before-completion/
    SKILL.md
  java/
    SKILL.md
    references/
      concurrency.md
  spring-boot/
    SKILL.md
    references/
      transactions.md
```

`catalog.json` là metadata của package và validator, không phải runtime instruction. Installer chỉ cài các thư mục con có `SKILL.md`; không cài `catalog.json` vào target.

## Skill taxonomy

Foundation hỗ trợ bốn type:

- `workflow`: quy trình task-specific như discovery, review, implementation, verification.
- `language`: semantics và rủi ro của một ngôn ngữ như Java hoặc TypeScript.
- `framework`: behavior riêng của framework như Spring Boot hoặc React.
- `risk`: workflow ngang theo risk surface như migration, security hoặc performance.

Catalog schema 1:

```json
{
  "schema": 1,
  "skills": [
    {
      "name": "code-review",
      "type": "workflow",
      "activation": "auto-and-user",
      "compositionGroup": "primary-workflow"
    },
    {
      "name": "java",
      "type": "language",
      "activation": "auto",
      "compositionGroup": "language"
    },
    {
      "name": "spring-boot",
      "type": "framework",
      "activation": "auto",
      "compositionGroup": "framework"
    }
  ]
}
```

Allowed `activation` values:

- `auto`: `user-invocable: false`, model có thể tự load.
- `manual`: `disable-model-invocation: true`, xuất hiện dưới dạng slash command.
- `auto-and-user`: mặc định cho cả auto-load và slash command.

Catalog không cố điều khiển runtime. Nó dùng để:

- validate frontmatter và policy;
- sinh bảng tài liệu;
- phát hiện duplicate/collision;
- giữ taxonomy ổn định khi số skill tăng.

## Runtime routing and composition

Routing thực tế dựa trên `name` và `description` trong `SKILL.md`. Description phải mô tả cả capability và activation boundary.

Ví dụ:

```yaml
---
name: spring-boot
description: >
  Analyze or change Spring Boot applications, including dependency injection,
  configuration, transactions, Spring Data, MVC, or WebFlux. Use when task files
  or dependencies show Spring usage. Do not use for plain Java without Spring.
user-invocable: false
---
```

Composition policy:

1. Chọn tối đa một primary workflow skill.
2. Thêm tối đa một language skill khi file/build evidence phù hợp.
3. Thêm tối đa một framework skill khi dependency/import/config evidence phù hợp.
4. Thêm risk skill chỉ khi task surface thực sự có risk tương ứng.
5. Không load skill chỉ vì repository có công nghệ đó nhưng task không chạm tới.
6. Foundation target là tối đa 3–4 active skills cho một FAST_FIX thông thường.

VS Code không cung cấp per-agent preload field. Agent definitions chỉ thêm một policy ngắn yêu cầu tận dụng skill phù hợp và tránh load theo repository-wide presence. Không copy nội dung skill vào agent.

`context: fork` chưa được dùng trong foundation vì đây là tính năng experimental và cần setting riêng. Có thể đánh giá sau cho skill review/research dài.

## Initial skill set

Foundation release tạo năm skill có mục đích rõ và đủ để chứng minh composition:

### `repository-discovery` — workflow, auto

Đọc cấu trúc, build files, test layout, conventions và constraints trước thay đổi. Không thực hiện implementation.

### `code-review` — workflow, auto-and-user

Chuẩn hóa expected behavior, diff/surrounding-code analysis, severity, evidence và test-gap review.

### `verification-before-completion` — workflow, auto

Yêu cầu fresh evidence trước khi tuyên bố task hoàn thành; tái sử dụng command evidence theo code revision.

### `java` — language, auto

Java semantics: nullability, exceptions, generics, equality, concurrency, resource lifecycle. Không chứa Spring-specific rules.

### `spring-boot` — framework, auto

Spring Boot semantics: bean/proxy behavior, transaction boundaries, MVC/WebFlux, configuration và Spring Data/JPA risks.

Không tạo `java-review`, `java-debugging`, `spring-review` hoặc ma trận language × workflow. Workflow là xương sống; language/framework là lớp bổ sung.

## SKILL.md authoring contract

Required:

- `name`: `^[a-z0-9]+(?:-[a-z0-9]+)*$`, 1–64 chars, trùng directory.
- `description`: 1–1024 chars, nói rõ capability và use condition.

Supported optional fields trong foundation:

- `argument-hint`.
- `user-invocable`.
- `disable-model-invocation`.
- `context`, chỉ chấp nhận `inline` hoặc `fork`; initial shipped skills dùng inline.
- Open-standard fields `license`, `compatibility`, `metadata`, `allowed-tools` được parser chấp nhận nhưng không bắt buộc.

Body policy:

- Tối đa 500 dòng.
- Tối đa 8.000 ký tự cho `SKILL.md` body.
- Chi tiết dài chuyển sang `references/`.
- Link relative không được thoát khỏi skill directory.
- Script/resource phải được tham chiếu trực tiếp hoặc có lý do rõ trong validator allowlist.
- Không lặp lại agent persona, tool restriction hoặc result contract nếu đã thuộc agent.

## Package and install targets

`package.json.files` thêm `skills`.

Default targets:

| Scope | Agents | Skills |
| --- | --- | --- |
| user | `~/.copilot/agents` | `~/.copilot/skills` |
| workspace | `.github/agents` | `.github/skills` |

CLI giữ backward compatibility:

```text
doct-agents [install|update|status|uninstall] [options]

--scope user|workspace
--workspace <path>
--component all|agents|skills   default: all
--agents-target <path>
--skills-target <path>
--target <path>                 legacy alias của --agents-target
--force
```

`--target` không đổi nghĩa để tránh phá script cũ. Dùng đồng thời `--target` và `--agents-target` là lỗi rõ ràng.

## Manifest schema 2

Mỗi target root có manifest riêng:

```json
{
  "schema": 2,
  "package": "doct-agents",
  "repository": "OneTwoTen/doct-agents",
  "component": "skills",
  "files": {
    "code-review/SKILL.md": "<sha256>",
    "java/references/concurrency.md": "<sha256>"
  }
}
```

Rules:

- Relative paths dùng `/` trong manifest trên mọi OS.
- Không absolute path, `..`, empty segment, NUL, drive prefix hoặc path escape.
- Reject case-insensitive collision để an toàn trên Windows.
- Mỗi path component hiện hữu phải không phải symlink/junction.
- Destination cuối phải là regular file hoặc chưa tồn tại.
- Manifest file không được là symlink/junction.

Backward compatibility:

- Agent target tiếp tục đọc schema 1 hiện tại.
- Schema 1 được normalize thành component `agents` trong memory.
- Lần update thành công tiếp theo ghi schema 2.
- Schema 1 không hợp lệ trong skill target.

## Generic installer architecture

Node và Python giữ parity bằng cùng khái niệm:

```text
ComponentSpec
- name
- sourceRoot
- targetRoot
- discoverFiles()
- validateRelativePath()
```

Discovery:

- agents: regular files `agents/*.agent.md`.
- skills: mỗi direct child directory phải có regular `SKILL.md`; recursively collect regular files bên trong; reject symlink/junction ở mọi level.
- `skills/catalog.json` được validator đọc nhưng không nằm trong installed file set.

Install/update flow:

1. Resolve selected component specs.
2. Validate source trees, targets và manifests.
3. Tính conflict/obsolete/preserved cho tất cả component trước mutation.
4. Nếu có conflict và không `--force`, dừng toàn bộ.
5. Stage toàn bộ component cạnh target tương ứng.
6. Commit file changes và manifests bằng shared rollback journal.
7. Nếu bất kỳ commit nào lỗi, rollback mọi component đã thay đổi.
8. Chỉ xóa backup khi toàn bộ package transaction thành công.

Nested directories được tạo lazily trước replace và xóa nếu rỗng sau rollback/uninstall. Installer không xóa directory có unmanaged file.

Status output nhóm theo component và hiển thị relative path. `installed` count phân biệt số agent/skill directories với số managed files khi cần.

## Validator architecture

Đổi entry point thành `scripts/validate_customizations.py` nhưng giữ `scripts/validate_agents.py` wrapper trong một release để không phá external command.

Validators:

### Agent validator

Giữ nguyên các guardrail hiện tại:

- required frontmatter;
- subagent routing allowlist;
- tool boundary;
- status/outcome vocabulary;
- prompt-size budget.

### Skill validator

Kiểm tra:

- catalog schema và allowed enum;
- catalog entry ↔ skill directory one-to-one;
- `SKILL.md` tồn tại và là regular file;
- name/description constraints;
- directory/name match;
- activation fields khớp catalog;
- body line/character budget;
- broken hoặc escaping relative links;
- no symlink/junction;
- case-insensitive path/name collision;
- duplicate description hoặc description quá chung;
- initial skill composition groups hợp lệ.

### Cross-customization validator

Kiểm tra:

- agent không nhúng bản copy dài của shipped skill workflow;
- orchestrator có skill composition policy ngắn;
- package files chứa `skills`;
- Node/Python default target và component vocabulary đồng nhất.

Không thêm runtime dependency; Python validator tiếp tục hỗ trợ Python 3.9. Frontmatter parser được mở rộng có kiểm soát cho scalar, folded description và optional mappings cần thiết, thay vì thêm PyYAML.

## Testing strategy

### Node installer tests

- default agents/skills targets cho user và workspace;
- install all components và ghi hai schema-2 manifests;
- install agents-only/skills-only;
- legacy `--target` behavior;
- nested resource modified/missing status;
- preserve modified obsolete skill file;
- remove unchanged obsolete skill/resource và empty directory;
- reject nested traversal, symlink/junction và case collision;
- prepare-all-before-mutate;
- failure ở skill commit rollback agent commit;
- uninstall không xóa unmanaged file trong skill directory.

### Python installer tests

Mirror toàn bộ security/lifecycle contract quan trọng của Node, bao gồm archive extraction có nested skill files.

### Validator tests

- valid pilot skills;
- missing/mismatched name;
- invalid description/activation;
- catalog missing/orphan entry;
- broken/escaping links;
- body budget;
- duplicate/case-colliding name;
- agent validator regression.

### Package/release tests

- `npm pack --dry-run` chứa mọi `SKILL.md` và resource.
- packaged CLI smoke install/status/uninstall cả agents và skills.
- release check giữ package version/tag invariant.
- CI chạy Node minimum/current, Python 3.9 và Windows lane hiện có.

## Documentation changes

README bổ sung:

- agent vs skill vs instructions decision rule;
- progressive loading chính xác;
- default skill locations;
- taxonomy/composition;
- `/skills` diagnostics và reload guidance;
- CLI component/target options;
- local modification protection cho nested resources.

`agent-authoring.agent.md` được rút gọn để trỏ tới authoring contract, không nhét toàn bộ skill specification vào agent prompt.

## Rollout

Foundation là minor release `0.3.0` vì thêm shipped behavior và CLI options nhưng giữ command cũ.

- `install/update` mặc định cài cả agents và skills.
- Người dùng có thể dùng `--component agents` để giữ behavior agent-only.
- Sau update cần `Developer: Reload Window` và chat mới để VS Code discover skill metadata.
- Initial skills dùng description hẹp; language/framework skills ẩn khỏi slash menu để giảm noise.
- Không dùng `context: fork` hoặc bundled executable scripts trong release đầu.

## Non-goals

- Không xây skill marketplace hoặc dependency resolver.
- Không dùng nested runtime skill namespaces.
- Không tự động đo semantic similarity bằng LLM trong CI.
- Không tạo mọi language/framework skill trong một PR.
- Không thay thế agent permissions, subagent isolation hoặc hooks bằng skills.
- Không đảm bảo runtime sẽ luôn chọn đúng skill; foundation tối ưu metadata, validator và composition policy nhưng routing cuối vẫn do Copilot quyết định.

## Risks and mitigations

- **Auto-loaded skill làm thay đổi behavior ngoài ý muốn:** description hẹp, background skill không user-invocable, component opt-out và pilot set nhỏ.
- **Nested path mở rộng attack surface:** canonical POSIX relative path, component-by-component link checks, case-collision rejection và tests Windows/POSIX.
- **Hai target gây partial update:** prepare toàn bộ trước mutation và shared rollback journal.
- **Validator YAML parser quá phức tạp:** chỉ hỗ trợ subset frontmatter cần thiết; không thêm dependency runtime.
- **Workflow bị lặp giữa agent và skill:** cross-customization checks và agent prompt budget.
- **Skill catalog lệch runtime description:** validator enforce catalog/frontmatter activation agreement.

## Success criteria

- `npm run check` pass trên các CI lane hiện có.
- `doct-agents install/update/status/uninstall` quản lý agents và nested skill resources an toàn ở cả Node/Python.
- Existing schema-1 agent installation update thành công mà không mất local modification.
- npm package chứa năm pilot skills và resource cần thiết.
- VS Code discover đúng skill name/description tại default targets.
- Skill body không được đọc đồng loạt; agent prompts không tăng đáng kể vì domain workflow được tách khỏi agent.
- Một Java Spring review có thể compose `code-review + java + spring-boot` mà không cần agent hoặc skill nhân chéo.

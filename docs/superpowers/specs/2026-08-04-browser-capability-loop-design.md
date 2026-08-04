# Browser Capability Loop Design

## Mục tiêu

Cho phép `implementation-agent` sử dụng trực tiếp Browser tools của GitHub Copilot khi sửa và xác minh ứng dụng web, thay vì bắt buộc đi qua `browser-agent` cho mọi thao tác browser. Giữ `browser-agent` như một worker kiểm tra độc lập/read-only cho các flow validation chuyên biệt.

## Hiện trạng

- `orchestrator` sở hữu routing và delegate sang worker chuyên biệt.
- `implementation-agent` chỉ có `read`, `search`, `edit`, không thể tự reproduce hoặc verify bằng integrated browser.
- `browser-agent` có đầy đủ Browser tools nhưng không được sửa file.
- Với bug/UI task, flow dễ trở thành `implementation-agent -> orchestrator -> browser-agent -> orchestrator -> implementation-agent`, tạo nhiều handoff và làm mất tight feedback loop mà Copilot Agent mặc định có.

## Thiết kế được chọn

Áp dụng mô hình hybrid capability ownership:

1. `implementation-agent` nhận trực tiếp Browser tools và `execute` để có thể chạy tight loop `reproduce -> inspect -> edit -> browser verify` trong cùng worker khi scope là web/UI.
2. `browser-agent` vẫn giữ read-only, không có `edit`, dùng cho independent validation, reproduction-only, regression flow, responsive checks và evidence độc lập.
3. `orchestrator` không nhận Browser tools. Nó tiếp tục sở hữu routing/budget nhưng không trở thành browser executor.
4. Browser validation không còn được mô hình hóa chỉ như một phase cuối. Với web/UI task, `implementation-agent` có thể dùng Browser tools trong DISCOVER/ANALYZE/VALIDATE trong cùng change loop.
5. Final build/lint/typecheck/integration validation vẫn thuộc `cli-executor`; browser runtime evidence không thay thế pipeline validation bắt buộc.

## Tool ownership

### implementation-agent

Giữ các tool hiện tại và thêm:

- `execute`
- `openBrowserPage`
- `navigatePage`
- `readPage`
- `screenshotPage`
- `clickElement`
- `hoverElement`
- `dragElement`
- `typeInPage`
- `handleDialog`
- `runPlaywrightCode`

`implementation-agent` chỉ dùng Browser tools khi task/scope liên quan trực tiếp UI, web flow hoặc runtime behavior cần reproduce/verify. Không biến mọi task backend thành browser task.

### browser-agent

Giữ nguyên Browser tool set và read-only policy. Vai trò được làm rõ là independent browser validation, không phải gateway bắt buộc để truy cập browser.

### orchestrator

Không thêm Browser tools. Routing được cập nhật để:

- ưu tiên `implementation-agent` tự dùng browser khi browser evidence cần cho việc sửa;
- gọi `browser-agent` khi cần independent verification, reproduction-only hoặc validation tách biệt khỏi writer;
- tránh handoff qua `browser-agent` chỉ để thao tác browser trong cùng một fix loop.

## Luồng mong muốn

### Web/UI fix

`orchestrator -> implementation-agent`

Trong `implementation-agent`:

`read source -> reproduce bằng browser -> edit -> read/navigate browser -> verify -> trả evidence`

Nếu cần validation độc lập sau đó:

`orchestrator -> browser-agent`

### Browser-only validation

`orchestrator -> browser-agent`

Không sửa code; chỉ reproduce, inspect, interact, screenshot và trả findings/evidence.

## Guardrails

- `implementation-agent` không được dùng browser để đăng nhập profile cá nhân, gửi form production, mua hàng hoặc thay đổi production data khi chưa được phép.
- `runPlaywrightCode` chỉ dùng khi primitive Browser tools không đủ.
- Browser action phải bám `Scope`/`Expected behavior`; không mở rộng exploratory testing vô hạn.
- `execute` trong `implementation-agent` chỉ dùng để phục vụ dev server/runtime loop hẹp của task; build/lint/typecheck/final integration vẫn handoff cho `cli-executor`.
- Khi tab cần session hiện có nhưng chưa `Share with Agent`, agent trả `needs-info` thay vì tự tạo workaround thủ công.

## Thay đổi tài liệu/prompt

- Cập nhật `agents/implementation-agent.agent.md` tool list và quy tắc browser-driven loop.
- Cập nhật `agents/browser-agent.agent.md` mô tả để nhấn mạnh independent validation và loại bỏ hàm ý browser gateway.
- Cập nhật `agents/orchestrator.agent.md` routing/validation ownership để ưu tiên direct browser capability trong implementation worker và chỉ delegate browser-agent khi cần độc lập.
- Cập nhật README ở phần workflow để phản ánh mô hình hybrid.
- Nếu validator/test đang hard-code tool list hoặc role assumptions, bổ sung test regression tương ứng.

## Acceptance criteria

- Một web/UI production fix có thể được orchestrator giao một lần cho `implementation-agent`, và worker đó có thể tự reproduce + sửa + browser verify trong cùng scope.
- `browser-agent` vẫn không có `edit` và vẫn có đầy đủ Browser tools.
- `orchestrator` vẫn không có Browser tools.
- Prompt không yêu cầu vòng handoff `implementation -> browser -> implementation` cho browser-driven debugging thông thường.
- Existing agent validation/tests pass và có regression coverage cho ownership mới nếu test suite hỗ trợ kiểm tra frontmatter/tool policy.
- README mô tả đúng workflow mới.

## Không thuộc phạm vi

- Không thêm MCP browser adapter cho OpenCode trong thay đổi này.
- Không thay đổi installer/runtime packaging ngoài những gì cần để ship agent definitions đã cập nhật.
- Không gộp `browser-agent` vào `implementation-agent` hoặc xóa agent chuyên biệt.

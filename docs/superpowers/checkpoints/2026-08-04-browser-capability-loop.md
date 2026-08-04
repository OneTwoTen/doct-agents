# Browser Capability Loop Checkpoint

Status: completed

## Completed

- `implementation-agent` có built-in Browser tools và `execute` cho dev-server/runtime loop hẹp.
- `implementation-agent` được phép chạy `reproduce -> inspect -> edit -> browser verify` cho web/UI task trong cùng worker.
- `browser-agent` giữ read-only và được định nghĩa rõ là independent validation/reproduction worker, không phải browser gateway bắt buộc.
- `orchestrator` ưu tiên direct browser capability trong implementation worker và chỉ gọi `browser-agent` khi cần independent evidence.
- Validator allowlist đã mở có chủ đích cho `implementation-agent` với `edit + execute`.
- Regression test bảo vệ Browser tool ownership, execute allowlist và orchestrator tool boundary.
- README đã mô tả hybrid browser model, web/UI FAST_FIX loop, validation ownership, agent roles, prompt mẫu và Browser tools.
- Design spec và implementation plan đã được lưu cùng branch.

## Validation evidence

- GitHub Actions `Validate agents` đã pass đầy đủ trên final branch revision.
- Matrix pass: `ubuntu-current`, `windows-current`, `ubuntu-minimum`.
- Mỗi lane pass bước `Run complete repository check`.

## Architecture decisions

- Browser là capability của implementation worker khi phục vụ change loop, không phải một stage/gateway bắt buộc.
- `browser-agent` tồn tại cho independent validation, regression/responsive flow và reproduction-only.
- `orchestrator` không nhận Browser tools.
- `execute` trong `implementation-agent` không thay quyền final validation của `cli-executor`.

## Docs impact

Status: required

- README đã được cập nhật để phản ánh behavior và ownership mới.
- Design spec và implementation plan mô tả rationale, guardrail và acceptance criteria.

## Remaining risks

- Chưa bổ sung OpenCode/MCP browser adapter; phần này nằm ngoài scope của thay đổi hiện tại.
- Browser tool availability vẫn phụ thuộc VS Code/Copilot runtime và `workbench.browser.enableChatTools`.

## Next

- Review và merge PR #10 khi phù hợp.

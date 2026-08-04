# Browser capability loop

Với web/UI fix, `implementation-agent` có thể dùng trực tiếp built-in Browser tools và runtime command hẹp để chạy vòng reproduce -> sửa -> browser verify trong cùng worker. `browser-agent` được giữ cho independent browser validation/read-only. Build, lint, typecheck và final integration validation vẫn thuộc `cli-executor`.

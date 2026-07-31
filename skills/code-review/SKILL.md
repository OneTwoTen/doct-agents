---
name: code-review
description: >
  Dùng khi đánh giá pull request, commit, patch hoặc implementation đã có để tìm defect, regression và test gap dựa trên evidence. Không dùng làm workflow chính cho feature chưa triển khai hoặc lỗi chưa xác định được root cause.
user-invocable: true
---

# Code Review

## Entry gate

Xác định expected behavior, phạm vi diff và code revision trước khi kết luận. Khi expected behavior có nhiều cách hiểu hợp lệ, ghi assumption hoặc yêu cầu bổ sung thay vì tự chọn silently.

## Quy trình

1. Đọc diff trước, sau đó đọc surrounding code, call site, model và test liên quan.
2. Theo dõi dữ liệu qua happy path, boundary và failure path; chú ý state, transaction, retry, concurrency và cleanup khi có evidence liên quan.
3. So sánh implementation với contract thực tế: API, schema, config, error behavior và compatibility.
4. Kiểm tra test có bảo vệ behavior thay đổi hay chỉ mirror implementation detail.
5. Chỉ tạo finding khi có failure scenario cụ thể, location và impact có thể hành động.
6. Gộp finding cùng root cause; không nâng style preference thành bug.
7. Tái sử dụng validation evidence còn fresh cho cùng revision; chỉ đề xuất command hẹp khi finding quan trọng chưa được xác minh.

## Severity

- `critical`: mất dữ liệu, security boundary hoặc hệ thống không thể vận hành an toàn.
- `high`: behavior chính sai hoặc regression có khả năng xảy ra trong production.
- `medium`: edge case thực tế, reliability hoặc maintainability có failure mode rõ.
- `low`: tác động hẹp và không chặn merge; dùng tiết chế.

## Hoàn tất

Nêu rõ phạm vi đã review, evidence đã dùng và phần chưa kiểm chứng. Không tuyên bố toàn bộ hệ thống an toàn từ một diff hẹp.

---
name: implementation-workflow
description: >
  Dùng khi expected behavior và phạm vi thay đổi đã đủ rõ để sửa bug hoặc triển khai code production bằng patch nhỏ có validation plan. Không dùng thay cho root-cause analysis khi lỗi còn chưa tái hiện hoặc nguyên nhân chưa có evidence.
user-invocable: true
---

# Implementation Workflow

## Entry gate

Chỉ bắt đầu khi có Objective, Scope, Expected behavior và Validation plan. Với bug, root cause phải được hỗ trợ bởi evidence đủ để phân biệt với symptom.

## Quy trình

1. Đọc implementation hiện tại, call site, data contract và test gần phạm vi.
2. Xác định change surface nhỏ nhất có thể sửa behavior mà không mở rộng capability.
3. Chọn test hoặc validation hẹp nhất có khả năng fail nếu behavior sai.
4. Thực hiện thay đổi theo convention hiện có; giữ compatibility trừ khi requirement nói rõ phá vỡ.
5. Kiểm tra error path, cleanup, transaction/state boundary và behavior khi dependency thất bại.
6. Ghi rõ file/symbol thay đổi, lý do và risk còn lại.
7. Chuyển command validation cho đúng owner; không kết luận pass từ static inspection nếu acceptance criteria cần runtime evidence.
8. Đánh giá docs impact dựa trên public behavior, config, operation và integration contract.

## Chống scope drift

- Không refactor lân cận nếu không cần để sửa behavior.
- Không tự chọn dependency version hoặc migration strategy ngoài scope.
- Khi phát hiện requirement mới làm thay đổi design, dừng phase implementation và trả về orchestrator để cập nhật plan.

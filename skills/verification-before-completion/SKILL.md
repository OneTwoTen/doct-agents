---
name: verification-before-completion
description: >
  Dùng trước khi tuyên bố task, milestone, fix hoặc release đã hoàn thành để đối chiếu từng claim với evidence còn mới trên đúng code revision. Không dùng để thay thế implementation, review hoặc command validation chưa được thực hiện.
user-invocable: false
---

# Verification Before Completion

## Quy trình

1. Liệt kê các claim sắp đưa ra: behavior đúng, test pass, build pass, docs cập nhật hoặc migration an toàn.
2. Gắn mỗi claim với evidence cụ thể gồm command hoặc inspection source, cwd, exit code và code revision.
3. Loại bỏ evidence cũ nếu code/config/environment liên quan đã thay đổi sau lần chạy.
4. Tái sử dụng successful evidence có cùng normalized command signature và revision; không chạy lặp chỉ để tạo log mới.
5. Kiểm tra acceptance criteria, finding critical/high, docs impact và milestone checklist còn mở.
6. Khi command bắt buộc không chạy được, báo `unverified` hoặc `blocked`; không đổi thành success bằng suy luận.
7. Kết luận chỉ trong phạm vi evidence hỗ trợ và liệt kê remaining risks.

## Evidence tối thiểu

- Claim.
- Owner.
- Command hoặc inspection source.
- Exit code/result.
- Revision/freshness.
- Unresolved hoặc limitation.

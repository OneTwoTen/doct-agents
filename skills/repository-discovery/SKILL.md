---
name: repository-discovery
description: >
  Dùng khi cần hiểu cấu trúc repository, convention, build system, test layout và ràng buộc trước khi review, sửa code hoặc lập kế hoạch. Không dùng khi scope và command liên quan đã được xác định bằng evidence còn mới.
user-invocable: false
---

# Repository Discovery

## Mục tiêu

Tạo repository map đủ dùng cho task hiện tại, không đọc toàn bộ source và không biến discovery thành một vòng nghiên cứu mở.

## Quy trình

1. Xác định workspace root và module trực tiếp liên quan tới task.
2. Đọc instruction gần scope nhất như `AGENTS.md`, README module, config build và convention test.
3. Phát hiện ngôn ngữ/framework bằng file, dependency, import và config thực tế; không suy ra chỉ từ tên repository.
4. Xác định command build, test, lint hoặc typecheck từ script/config có trong repo.
5. Tìm code path, test gần nhất, call site và integration boundary cần cho phase tiếp theo.
6. Dừng khi đã đủ evidence để chọn workflow, owner và validation plan.

## Kết quả cần cung cấp cho phase sau

- Root/module và file trọng tâm.
- Instruction/convention áp dụng.
- Ngôn ngữ/framework có evidence.
- Command validation khả dụng và nguồn xác định command.
- Unknown hoặc blocker còn lại.

## Giới hạn

- Không sửa file.
- Không chạy full build chỉ để khám phá.
- Không load language/framework skill chỉ vì công nghệ tồn tại ở module khác không thuộc task.

# Java Concurrency Reference

Chỉ áp dụng khi có shared mutable state, async execution, parallel stream, lock, future, scheduler hoặc callback chạy khác thread.

- Xác định owner của state và thread nào được phép mutate.
- Kiểm tra atomicity của read-modify-write; `volatile` chỉ cung cấp visibility, không làm chuỗi thao tác thành atomic.
- Không giữ monitor/lock qua network, disk hoặc callback không kiểm soát.
- Bảo toàn interruption: restore interrupt flag hoặc propagate theo contract.
- Kiểm tra executor lifecycle, queue growth, rejection policy và cancellation.
- Với `CompletableFuture`, xác định executor, exception path và behavior khi một stage bị cancel.
- Test concurrency phải chứng minh invariant; tránh chỉ dựa vào sleep hoặc timing may rủi.

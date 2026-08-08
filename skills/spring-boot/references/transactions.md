# Spring Transaction Reference

- Xác định transaction bắt đầu ở public proxy boundary nào; self-invocation không kích hoạt interceptor mặc định.
- Kiểm tra checked exception, caught exception và rollback rule thực tế.
- Không giả định remote API, message broker hoặc file operation được rollback cùng database.
- Với external side effect, xác định thứ tự call, idempotency, compensation hoặc outbox strategy.
- Kiểm tra propagation (`REQUIRED`, `REQUIRES_NEW`, `NESTED`) và connection/pool impact.
- Không truy cập lazy relation ngoài persistence context nếu contract không bảo đảm session mở.
- Với retry, bảo đảm retry boundary không tái phát side effect không idempotent.

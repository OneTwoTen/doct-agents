---
name: java
description: >
  Dùng khi task trực tiếp đọc hoặc thay đổi Java source, JVM test hay build configuration và cần kiểm tra semantics của Java. Không dùng chỉ vì repository có Java ở module khác hoặc khi risk hoàn toàn thuộc framework mà không cần Java-level reasoning.
user-invocable: false
---

# Java

Dùng skill này như lớp bổ sung cho workflow chính, không thay thế workflow review, implementation hoặc debugging.

## Checklist theo evidence

- Nullability, boxing/unboxing và giá trị mặc định.
- Equality/hash contract, identity và collection key behavior.
- Exception type, wrapping, checked/unchecked boundary và interruption.
- Generic variance, raw type, type erasure và unsafe cast.
- Resource lifecycle với stream, file, connection và executor.
- Mutable shared state, publication và thread safety.
- Numeric overflow, precision, date/time zone và charset.
- API compatibility của signature, overload và serialization model.

Khi task có concurrency, đọc [hướng dẫn concurrency](references/concurrency.md).

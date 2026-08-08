---
name: spring-boot
description: >
  Dùng khi task trực tiếp liên quan Spring Boot, dependency injection, configuration, transaction, Spring Data, MVC hoặc WebFlux có evidence từ dependency/import/config. Không dùng cho plain Java không có Spring hoặc module không bị task chạm tới.
user-invocable: false
---

# Spring Boot

Dùng skill này cùng workflow chính và Java skill khi reasoning phụ thuộc Java semantics.

## Checklist theo evidence

- Bean lifecycle, scope, conditional creation và configuration binding.
- Proxy boundary, self-invocation và annotation chỉ có hiệu lực qua proxy.
- Transaction propagation, rollback rule, external side effect và lazy loading.
- Spring Data query semantics, pagination, fetch strategy và N+1.
- MVC/WebFlux consistency; không block event-loop bằng API blocking.
- Validation/error mapping, content type và serialization contract.
- Async/scheduled execution, context propagation và shutdown behavior.
- Test slice có phản ánh runtime wiring cần bảo vệ hay không.

Khi task có transaction hoặc side effect, đọc [hướng dẫn transaction](references/transactions.md).

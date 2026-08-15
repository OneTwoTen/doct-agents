# Adaptive FAST_FIX Design

**Status:** approved for implementation

## Goal

Giảm model calls, token và latency cho task nhỏ mà không làm yếu validation cho thay đổi có rủi ro. Giữ hai lifecycle cấp cao hiện có là `FAST_FIX` và `LONG_RUNNING`; không thêm workflow `SMALL/MEDIUM/LARGE` mới.

## Current problem

`FAST_FIX` hiện dùng state machine `DISCOVER -> PLAN -> ANALYZE -> CHANGE -> VALIDATE -> DOCS_IMPACT -> FINALIZE`. Planning-agent đã được loại khỏi FAST_FIX, nhưng contract vẫn khiến task rất nhỏ có thể mang metadata/handoff và worker budget lớn hơn cần thiết. `implementation-agent` cũng đang yêu cầu `Validation plan` cho mọi code change dù validation đôi khi hiển nhiên.

## Design

### 1. FAST_FIX có hai execution path

`direct` là mặc định cho thay đổi bounded, expected behavior rõ và không có signal rủi ro đặc biệt.

```text
DISCOVER -> IMPLEMENT -> VALIDATE -> FINALIZE
```

`guarded` dùng khi vẫn bounded nhưng cần thêm test, independent review hoặc domain validation.

```text
DISCOVER -> IMPLEMENT -> optional TEST/REVIEW/DOMAIN -> VALIDATE -> FINALIZE
```

Các path này là execution strategy bên trong FAST_FIX, không phải workflow mới.

### 2. Routing dựa trên boundedness và risk

FAST_FIX chỉ được dùng khi scope có thể hoàn thành an toàn trong một bounded change-validate loop. `direct` ưu tiên khi:

- expected behavior rõ;
- scope cục bộ và xác định được;
- không có migration/rollback;
- không đổi dependency theo cách cần lựa chọn version;
- không có compatibility/public-contract concern đáng kể;
- không có security, concurrency hoặc data-integrity risk;
- validation hẹp có thể xác định từ repo/task.

`guarded` được chọn khi task vẫn bounded nhưng evidence cho thấy cần regression test mới, independent review hoặc domain validation.

### 3. Escalation

FAST_FIX phải chuyển sang `LONG_RUNNING` khi discovery cho thấy có một trong các dấu hiệu:

- nhiều phase phụ thuộc;
- migration/rollback;
- compatibility contract;
- cross-module coordination đáng kể;
- architecture decision chưa rõ;
- không thể validate trong bounded loop.

Không cố giữ task trong FAST_FIX chỉ vì prompt ban đầu trông nhỏ.

### 4. Worker policy

- Production code change vẫn bắt buộc qua `implementation-agent`.
- `review-agent` không phải default trong FAST_FIX; chỉ gọi khi risk/evidence cần independent read.
- `test-agent` chỉ gọi khi cần thêm/sửa test artifact; không gọi chỉ để chạy test đã tồn tại.
- `cli-executor` chỉ chạy validation thuộc ownership của nó và không lặp fresh evidence cùng signature/revision.
- `docs-agent` chỉ gọi khi docs impact thực sự `required`; docs impact là predicate nhẹ, không phải worker mặc định.
- FAST_FIX direct mặc định một writer và tối đa hai worker tổng cộng; guarded mặc định tối đa ba worker, worker thứ tư chỉ khi có domain risk rõ.
- Không chạy nhiều worker song song mặc định cho FAST_FIX; chỉ parallelize khi scope thực sự độc lập.

### 5. Handoff contract

`implementation-agent` trong FAST_FIX cần `Objective`, `Scope`, `Expected behavior`. `Validation plan` chỉ bắt buộc khi validation không hiển nhiên hoặc orchestrator cần truyền acceptance/command constraint cụ thể.

LONG_RUNNING giữ contract chặt hiện tại gồm milestone/spec path/allowed files/forbidden files/definition of done/validation plan.

### 6. Validation depth theo risk

Task size chọn workflow; risk chọn độ sâu validation.

- mechanical/local change: static hoặc local check hẹp;
- local behavior: targeted test/typecheck phù hợp;
- contract behavior: targeted test + relevant integration evidence;
- security/data/concurrency risk: independent/domain validation phù hợp.

Một thay đổi một dòng nhưng risk cao không được dùng validation nhẹ chỉ vì diff nhỏ.

## Guardrails

Repository tests phải khẳng định:

- FAST_FIX có `direct` và `guarded` semantics;
- direct path không mặc định planning/review/docs worker;
- FAST_FIX có explicit escalation sang LONG_RUNNING;
- implementation FAST_FIX không bắt buộc Validation plan khi validation hiển nhiên;
- LONG_RUNNING vẫn bắt buộc Validation plan và milestone metadata;
- validation ownership/fresh evidence rules hiện có không bị phá.

## Documentation

README mô tả FAST_FIX adaptive ở mức người dùng: task nhỏ bounded ưu tiên direct path; test/review/docs/domain validation chỉ được thêm theo risk/evidence; discovery có thể escalate sang LONG_RUNNING.

## Success criteria

- Planning-agent calls trong FAST_FIX: `0`.
- Review/docs worker không phải default của FAST_FIX direct.
- Median worker count mục tiêu cho FAST_FIX direct: `<= 2`.
- Duplicate validation signature trên cùng validation revision: `0`.
- Existing LONG_RUNNING lifecycle và browser-driven implementation behavior vẫn giữ nguyên.

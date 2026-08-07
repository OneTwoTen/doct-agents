# FAST_FIX

Status: stable

## Capability

FAST_FIX điều phối task kỹ thuật bounded bằng execution path adaptive: mặc định dùng `direct` để giảm handoff/model call cho thay đổi rõ và ít rủi ro; chuyển sang `guarded` khi evidence cho thấy cần test mới, independent review hoặc domain validation; escalate sang `LONG_RUNNING` khi discovery cho thấy scope không còn bounded.

## Đã triển khai

- `direct`: `DISCOVER -> IMPLEMENT -> VALIDATE -> FINALIZE`.
- `guarded`: `DISCOVER -> IMPLEMENT -> optional TEST/REVIEW/DOMAIN -> VALIDATE -> FINALIZE`.
- FAST_FIX không gọi `planning-agent`, không tạo spec/roadmap.
- Production code change vẫn bắt buộc qua `implementation-agent`.
- FAST_FIX chỉ yêu cầu `Objective`, `Scope`, `Expected behavior`; `Validation plan` chỉ bắt buộc khi validation không hiển nhiên hoặc cần truyền acceptance/command constraint cụ thể.
- `review-agent` không phải bước mặc định; chỉ dùng khi risk/evidence cần independent review.
- `test-agent` chỉ được gọi khi cần thêm/sửa test artifact; test đã tồn tại do validation owner phù hợp chạy.
- `docs-agent` chỉ được gọi khi docs impact là `required`; uncertainty của FAST_FIX được orchestrator read/search trước.
- Browser-driven implementation giữ nguyên: web/UI có thể reproduce -> inspect -> edit -> browser verify trong `implementation-agent`; `browser-agent` dành cho validation/reproduction độc lập.
- Refactor giữ behavior vẫn route `refactor-agent`; test-only vẫn route `test-agent`.
- `cli-executor` sở hữu build/lint/typecheck/final integration và không chạy lại fresh evidence cùng signature/revision.
- FAST_FIX direct tối đa 2 worker; guarded tối đa 3 worker, worker thứ tư chỉ khi có domain risk rõ; mặc định 1 worker tại một thời điểm.
- Escalate sang `LONG_RUNNING` khi có dependent phases, migration/rollback, compatibility contract, cross-module coordination đáng kể, unresolved architecture decision hoặc validation không thể hoàn thành trong bounded loop.
- Validation depth phụ thuộc risk thay vì số dòng diff.

## Chưa triển khai

- Runtime classifier/telemetry machine-readable cho `direct` và `guarded`.
- Benchmark thực tế đủ mẫu để chứng minh mức giảm token/latency; mục tiêu hiện tại cần đo tối thiểu 5 Agent Debug sessions cho mỗi path và so sánh median.

## Ràng buộc quan trọng

- Không thêm workflow cấp cao `SMALL/MEDIUM/LARGE`; `direct`/`guarded` chỉ là execution strategy bên trong FAST_FIX.
- Task một dòng nhưng có security/concurrency/data-integrity risk vẫn phải dùng validation phù hợp.
- Fresh validation evidence cùng signature/revision phải được reuse.
- Nếu discovery chứng minh task không còn bounded, phải chuyển LONG_RUNNING thay vì cố giữ FAST_FIX.

## Validation

Behavior revision `b7a7ed3f07778d1ec992e0146278bf95aefb7c13` đã pass GitHub Actions run `31141889762` trên Ubuntu current, Ubuntu minimum và Windows current. Mỗi lane hoàn thành full `npm run check`, gồm Node tests, 62 Python tests, agent validator/prompt-size budget, package dry-run và packaged CLI smoke test.

## Related specs

- `docs/superpowers/specs/2026-08-07-adaptive-fast-fix-design.md`.
- `docs/superpowers/plans/2026-08-07-adaptive-fast-fix.md`.
- `docs/token-metrics.md` — target đo runtime token/worker count cho direct/guarded.

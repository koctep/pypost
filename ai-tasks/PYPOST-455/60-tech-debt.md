# PYPOST-455: Technical Debt Analysis

## Shortcuts Taken

- **Local-only micro-benchmark:** Timing numbers in `20-architecture.md` are from developer
  hardware, not CI. Sufficient for order-of-magnitude decision on a desktop client.
- **Deferral without duration metrics:** Relied on existing attempt counters rather than adding
  a histogram in this evaluation task.

## Code Quality Issues

None introduced. No production code changes.

## Missing Tests

- No automated performance regression test (intentionally avoided — flaky on shared CI runners).
- Guard tests in `test_template_service_caching_eval.py` cover idempotency only.

## Performance Concerns

- **Compile-per-call remains:** `Environment.from_string` runs on every non-empty render.
  Acceptable per benchmark (~130–180 µs typical; ~0.7 ms per simulated HTTP request).
- **Large multi-placeholder templates:** ~1.4 ms/render in stress benchmark; rare in practice.
  Revisit if users adopt very large inline templates.

## Follow-up Tasks

- **Compiled template LRU (optional):** If Prometheus shows sustained high
  `template_expression_render_attempts` or hover lag is reported, implement Strategy A from
  `20-architecture.md` (`lru_cache` on compile, `maxsize=256`). No Jira ticket created —
  criteria documented above; create ticket when signal appears.
- **Render duration histogram (optional):** Add only if volume counters are insufficient to
  diagnose lag.

## Evaluation verdict

**SAFE TO CLOSE** — caching deferred with documented revisit criteria. No blockers.

# PYPOST-422: Technical Review (STEP 6)

## Delivered scope

- **Prometheus counter rename:** `email_notification_failures_total` replaced by
  `request_retry_exhaustions_total` with help text describing outbound HTTP retry exhaustion
  (`pypost/core/metrics.py`).
- **API surface:** `track_request_retry_exhaustion(endpoint)` replaces the previous
  email-specific tracker name; private field `_request_retry_exhaustions_total` aligns with NFR-4.
- **Call site:** `RequestService._emit_exhaustion_alert` invokes
  `track_request_retry_exhaustion(request.url)` (`pypost/core/request_service.py`).
- **Labels:** `endpoint` only; semantics unchanged (FR-3).
- **Architecture choice:** Option **A** (hard rename, no dual export), per `20-architecture.md`
  and STEP 3 notes in `00-roadmap.md`.
- **Automated tests:** `tests/test_metrics_manager.py` asserts scraped text format for
  `request_retry_exhaustions_total{endpoint=...}`; `tests/test_retry.py` asserts the tracker on
  exception and status exhaustion paths (AC-2, NFR-3).
- **Code quality / observability artifacts:** `40-code-cleanup.md`, `50-observability.md` document
  scoped lint status, pytest results, and emission-point verification.

## Technical debt findings

- **Consumer migration (medium — ops/process):** Hard rename drops the old series; Grafana and
  Prometheus rules need manual updates. No deprecated alias (option A trade-off).
- **`doc/dev/` coverage (low — STEP 7):** `doc/dev/testing.md` does not yet list
  `request_retry_exhaustions_total` or migration from the legacy name. FR-2 / AC-3 tracked for
  STEP 7.
- **Historical task docs (low — informational):** Some `ai-tasks/*` artifacts may still mention
  legacy names for audit history; they are not product `doc/dev/` or runtime code.
- **Repository-wide flake8 (low — pre-existing):** Full `make lint` on `pypost/` still fails
  outside PYPOST-422 paths (see `40-code-cleanup.md`).

**Explicit none:** No extra shortcuts, duplicate metric increments, or architecture deviations
were found in the PYPOST-422 implementation paths.

## Risk assessment

| Risk | Likelihood | Impact | Mitigation |
| ---- | ---------- | ------ | ---------- |
| Dashboards/alerts still query the old metric | High if not notified | Medium | Release notes, CHANGELOG, internal comms; STEP 7 dev docs |
| Legacy names return in code | Low | Medium | Tests pin series and method; `rg` per `50-observability.md` |
| Mix-up with `request_errors_total` | Low | Low | Names, help text, `50-observability.md` |

Overall: **acceptable for merge** on code and tests; main residual risk is **migration
communication**, not implementation quality.

## Test adequacy

- **Strengths:** Registry scrape assertion validates the **exported contract** (name, label key,
  sample value). Retry tests cover **both** exhaustion paths (exception and retryable status) and
  assert **not called** when exhaustion does not occur.
- **Gaps (non-blocking):** No HTTP `/metrics` integration test; matches existing
  `MetricsManager` unit-test style. Full `make lint` is not green for unrelated modules
  (documented).

## Follow-up recommendations

1. **STEP 7:** Update `doc/dev/` (and release notes / CHANGELOG as applicable) with the new series
   name, former name, and operator actions per FR-2, AC-3, and NFR-2.
2. **Operations:** Notify dashboard and alert owners to replace queries using
   `email_notification_failures_total` with `request_retry_exhaustions_total`.
3. **Optional later:** If product needs a softer rollout, consider a time-boxed dual-export (option
   B) in a separate task; not required for PYPOST-422 closure.

## Review conclusion

- **Blockers for release (code/test):** **None** identified in this review.
- **STEP 6 artifact:** This document satisfies the STEP 6 technical debt and review checkpoint for
  PYPOST-422; user approval remains the gate before STEP 7 per `00-rules.mdc`.

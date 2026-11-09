# PYPOST-1392: Technical Debt Analysis

## Shortcuts Taken

1. **Explicit `preserve_reveal_state` flag** — Callers must opt in (indent path does).
   Content fingerprinting of `(body, hidden_fields)` was deferred; accidental preserve on
   a new payload remains prevented by default `False`.
2. **Stale map entries kept until full clear** — Paths absent from the new span set stay
   in `_reveal_state` until `clear()`. Harmless for same-response reformat; only cleared
   on new response / `clear_body`.
3. **Sequential restore of revealed spans** — `_apply_persisted_reveals` expands each
   revealed path with the same linear later-span shift as `handle_click`. Acceptable for
   typical secret counts; high-N toggle cost already tracked under PYPOST-1547.

## Code Quality Issues

1. **Private map access remaining internal** — `_reveal_state` is controller-private;
   observability logs counts without exposing a public accessor. Acceptable for this
   scope. *Accepted by design / low risk — no ticket.*
2. **Repro helpers use path substring match** — `_span_by_path` matches `path_substr in
   s.path`. Sufficient for flat `token` / `password` fixtures; brittle if fixtures gain
   nested duplicate suffixes. *Accepted for current fixtures — no ticket.*

## Missing Tests

1. **Timeout markers** — Module `pytestmark = pytest.mark.timeout(60)` on
   `tests/test_pypost_1392_failing_repro.py`. **Zero blockers.**
2. **FR-5 `clear_body` reset** — Covered indirectly by `clear()` wiping the map, but no
   dedicated GUI assertion that `clear_body` then redisplay starts masked.
3. **FR-7 re-mask persistence** — Reveal-then-re-mask before `set_indent_size` is not an
   explicit automated case (only single reveal + sibling still-masked).
4. **Medium-doc async preserve** — Indent reformat through `ResponseMaskWorker` relies on
   `set_masked_spans` restore; no dedicated medium-payload preserve test.

## Performance Concerns

1. **O(R × N) restore on reformat** — Restoring `R` revealed spans each walks later
   spans. Typical `R` is small; same class of cost as multi-toggle (see PYPOST-1547).
2. **Unpruned `_reveal_state` growth** — Only relevant if preserve were misused across
   many distinct payloads without `clear()`; current API defaults prevent that.

## Follow-up Tasks

### Pre-existing / flaky suite failures

None newly triaged in Steps 5–8 for this task (targeted suites green). Broader suite
failures, if any at commit time, should reuse existing NON-BLOCKER tickets rather than
re-filing.

### New follow-ups from this implementation

| ID | Priority | Description | Notes / Jira |
| --- | --- | --- | --- |
| TD-1 | Low | Add automated coverage for `clear_body` reset (FR-5) and reveal-then-re-mask persistence across indent reformat (FR-7) | Complements existing indent + new-response tests. Jira: [PYPOST-1549](https://pypost.atlassian.net/browse/PYPOST-1549) |
| TD-2 | Low | Add medium-document (`ResponseMaskWorker`) indent-reformat preserve regression so async span application restores `_reveal_state` under generation checks | Sync path covered by PYPOST-1392 repro. Jira: [PYPOST-1550](https://pypost.atlassian.net/browse/PYPOST-1550) |
| TD-3 | Low | Optionally prune `_reveal_state` keys not present in the current span set after `set_masked_spans` to bound memory under long preserve sessions | Nice-to-have; not required for DoD. Jira: [PYPOST-1551](https://pypost.atlassian.net/browse/PYPOST-1551) |

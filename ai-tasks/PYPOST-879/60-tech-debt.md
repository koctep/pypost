# PYPOST-879: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Optional shared `worker_timeout_detail` extraction remains unnecessary:
inventory still shows a **single** worker-only consumer module. Closing as
explicit YAGNI deferral with evidence (PYPOST-828 TD-2 acceptance path).
**Do not create Jira tickets in this step** — no new follow-ups required.

## Shortcuts Taken

- **Did not extract shared helper.** Matches ticket guidance and architecture:
  extract only when a second worker-only consumer appears.
- **Counted two call sites as one consumer.** Both waits live in
  `tests/test_collection_storage_worker.py`; that is reuse within one module,
  not cross-module duplication.
- **No red/green harness change.** Step 3 N/A; decision documented instead of
  inventing a failing test for a non-change.
- **Full `make check` not run.** Docs/decision-only; full gate remains
  [PYPOST-880](https://pypost.atlassian.net/browse/PYPOST-880).

## Code Quality Issues

- None blocking. Local `_worker_timeout_detail` is a five-line closure over
  `format_storage_async_timeout_detail(worker_running=…)`. Acceptable
  colocation until reuse appears.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Shared `worker_timeout_detail` API | Not applicable — API not introduced |
| Local worker timeout detail still used | Covered by existing collection worker waits |
| Inventory of second consumer | Documented absent (manual inventory) |

Timeout markers: unchanged on existing modules. **No timeout-marker blockers.**

## Performance Concerns

None. No code path changes.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| — | — | None | Reopen/extract only if a second worker-only consumer appears | — |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Full `make check` when sibling noise is clear | [PYPOST-880](https://pypost.atlassian.net/browse/PYPOST-880) |
| Wire `worker_operation` into env gateway detail | [PYPOST-878](https://pypost.atlassian.net/browse/PYPOST-878) (done / sibling) |

## Inventory evidence (close criteria)

```text
_worker_timeout_detail definition: tests/test_collection_storage_worker.py only
_worker_timeout_detail call sites: 2 (same file)
Other worker-only timeout_detail helpers: none
Gateway waits: use gateway_timeout_detail (already shared)
```

## User documentation

N/A — harness/docs-only; no `doc/user/` updates. Developer docs are Step 8.

## Blocker Review

**SAFE TO CLOSE**

- DoD met via YAGNI deferral path: inventory recorded; extract-vs-defer
  decision explicit; no forced refactor; product unchanged.
- No missing pytest timeout markers.
- No BLOCKER or unticketed follow-ups for Phase D.
- Unticketed follow-ups needing Jira: **none**.

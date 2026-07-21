# PYPOST-889: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Agent e2e exactly-once lock for the PYPOST-887 double response-body case is
in place: `REQUEST_BODY_EDIT` identity, catalog canned result + streaming
stub, and `tests/test_agent_e2e_double_response_body.py` under
`make test-agent-e2e`. Items below are non-blocking hygiene. **Do not create
Jira tickets in this step** — orchestrator Phase D fills the Jira column.

## Shortcuts Taken

- **FR5 red proof is local / manual.** Architecture requires the lock to fail
  when discard is missing. Proven by temporarily no-op'ing
  `_discard_chunk_buffer` in `_on_request_finished`, then restoring — not
  committed. Default HEAD stays green. No CI job re-runs that protocol
  (see TD-1).
- **Snapshot observation walks `RESPONSE_PANEL` text.** Status/body still
  lack dedicated widget ids (same fallback as golden). Architecture accepted
  this; already tracked under PYPOST-853 / PYPOST-838 TD-1.
- **Test-local panel walk helpers.** Copied golden-style `_walk_values` /
  `_subtree_by_name` / excerpt helpers into the lock module rather than
  extracting a shared helper in this story (architecture: “share later if
  debt”). Already tracked as [PYPOST-869](https://pypost.atlassian.net/browse/PYPOST-869).
- **Streaming stub needs explicit catalog `name=`.**
  `canned_send_with_one_chunk(...)` returns a callable, so
  `stub_agent_e2e_http` identity checks against canned constants do not
  auto-resolve `double_body_lock_ok`. Lock passes
  `name="double_body_lock_ok"` (see TD-2).
- **FR7 `doc/dev/` discoverability deferred to Step 8.** Same story; not
  Debt. Roadmap already records this.
- **No method/body matrix.** Out of scope; epic
  [PYPOST-888](https://pypost.atlassian.net/browse/PYPOST-888) siblings own
  broader presentation coverage.

## Code Quality Issues

- **Duplicated response-panel snapshot walkers** across golden, env HTTP,
  and this lock — drift risk; remediate via existing PYPOST-869.
- **`stub_agent_e2e_http` catalog auto-name vs streaming factories** —
  authors must remember `name=` when using `canned_send_with_one_chunk`
  (TD-2). Lock itself is correct.
- **Hardcoded settle budgets** (`_SEND_SETTLE_TIMEOUT_S = 15.0`,
  `_CHUNK_FLUSH_SETTLE_MS = 100`) mirror golden / flush interval; intentional,
  not magic debt.

## Missing Tests

| Scenario | Status |
| --- | --- |
| PUT + reported body → body token exactly once | Covered (lock) |
| Catalog + `canned_send_with_one_chunk` unit | Covered (`test_agent_e2e_http.py`) |
| `REQUEST_BODY_EDIT` identity spot-check | Covered |
| Explicit `pytest.mark.timeout` on new tests | Present (60s + `agent_e2e`) |
| Automated FR5 red (discard no-op via monkeypatch) | Missing — TD-1 |
| Broad method/body matrix | Out of scope (PYPOST-888) |
| Dedicated response status/body widget waits | Deferred (PYPOST-853) |

**No timeout-marker blockers.**

## Performance Concerns

None. One additional agent e2e scenario; same settle/poll profile as golden.
`QTest.qWait(100)` after settle is bounded and only ensures a late flush
would be visible if discard were missing.

## User documentation (`doc/user/`)

N/A. Requirements exclude user-facing docs; this is an agent e2e lock +
harness identity. Developer discoverability is Step 8 (`doc/dev/`).

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Automate FR5 red-path proof | Optional second test (or marked variant) that monkeypatches `_discard_chunk_buffer` to no-op under the streaming stub and asserts `count >= 2`; keeps product code untouched | Jira: [PYPOST-892](https://pypost.atlassian.net/browse/PYPOST-892) |
| TD-2 | Lowest | Improve stub catalog naming for streaming helpers | When `stub_agent_e2e_http` receives `canned_send_with_one_chunk(known_canned)`, derive catalog name (or document `name=` as required in `agent_e2e_http.md`) | Jira: [PYPOST-893](https://pypost.atlassian.net/browse/PYPOST-893) |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Share response-panel snapshot walk helpers | [PYPOST-869](https://pypost.atlassian.net/browse/PYPOST-869) |
| Optional `pypost_response_status` / `pypost_response_body` ids | [PYPOST-853](https://pypost.atlassian.net/browse/PYPOST-853) |
| Product double-body discard fix | [PYPOST-887](https://pypost.atlassian.net/browse/PYPOST-887) |
| Broader Send/response presentation matrix | Epic [PYPOST-888](https://pypost.atlassian.net/browse/PYPOST-888) |

### Planned this ticket (not separate Debt)

- Step 8: brief `doc/dev/` note + links from agent e2e / golden / HTTP docs
  (FR7).

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions relative to AC | None — lock + identity + catalog meet DoD |
| Missing pytest timeout markers | **None** |
| Deviations from architecture | None — FR7 docs intentionally Step 8 |
| Hardcoded values | Settle/flush budgets intentional |
| Merge / release blockers | **None** |

**SAFE TO CLOSE** — regression lock is green under `agent_e2e`; residual
items are optional FR5 automation and stub naming polish. Shared panel
helpers and response widget ids remain owned by existing tickets.

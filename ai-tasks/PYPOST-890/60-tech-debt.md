# PYPOST-890: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Agent e2e method × body presentation matrix is in place: smoke + slow
params, once-only body/status asserts, `REQUEST_DETAIL_TABS` identity,
and `ai-tasks/PYPOST-890/findings.md` for PYPOST-891. Product fixes are
out of scope. Items below are non-blocking hygiene. **Do not create Jira
tickets in this step** — orchestrator Phase D fills the Jira column when
needed.

## Shortcuts Taken

- **FR5-style red proof is local / manual.** Temp no-op of
  `_discard_chunk_buffer` in `_on_request_finished` proved
  `POST-json_ok` fails with `count=2`, then restored — not committed.
  Default HEAD stays green. No CI job re-runs that protocol (TD-1).
- **Snapshot observation walks `RESPONSE_PANEL` text.** Status/body still
  lack dedicated widget ids (same fallback as golden / 889). Already
  tracked under PYPOST-853 / PYPOST-838 TD-1.
- **Test-local panel walk helpers.** Matrix copies golden-style
  `_walk_values` / `_subtree_by_name` / excerpt helpers rather than
  extracting a shared helper (architecture: share later). Already tracked
  as [PYPOST-869](https://pypost.atlassian.net/browse/PYPOST-869).
- **Streaming stub needs explicit catalog `name=`.** Matrix passes
  `name=presentation_matrix_{method}_{shape}` (same class of issue as
  [PYPOST-893](https://pypost.atlassian.net/browse/PYPOST-893)).
- **FR7 `doc/dev/` discoverability deferred to Step 8.** Same story; not
  Debt. Roadmap already records this.
- **`REQUEST_DETAIL_TABS` not in `KEY_WIDGET_IDS`.** Identity is set and
  used by the matrix; optional spot-check / KEY list expansion left as
  TD-2 rather than expanding the PYPOST-834 key set in this story.
- **Empty `findings.md` table on HEAD.** 25/25 green with discard present;
  no xfail rows. Real product defects → xfail + findings row (owned by
  matrix maintainers / PYPOST-891).

## Code Quality Issues

- **Duplicated response-panel snapshot walkers** across golden, env HTTP,
  889 lock, and this matrix — drift risk; remediate via existing
  PYPOST-869.
- **`stub_agent_e2e_http` catalog auto-name vs streaming factories** —
  authors must remember `name=` when using `canned_send_with_one_chunk`
  (existing PYPOST-893).
- **Hardcoded settle budgets** (`_SEND_SETTLE_TIMEOUT_S = 15.0`,
  `_CHUNK_FLUSH_SETTLE_MS = 100`) mirror golden / flush interval;
  intentional, not magic debt.

## Missing Tests

| Scenario | Status |
| --- | --- |
| 5×5 method × body once-only body/status | Covered (matrix) |
| Smoke slice in default `agent_e2e and not slow` | Covered (5 cells) |
| Non-200 status probe (`POST×json_ok` → 201) | Covered |
| Body tab select for GET/PATCH/DELETE + body | Covered via
  `REQUEST_DETAIL_TABS` |
| Explicit `pytest.mark.timeout` on new tests | Present (60s +
  `agent_e2e`) |
| Automated discard no-op red protocol | Missing — TD-1 |
| `REQUEST_DETAIL_TABS` identity spot-check | Missing — TD-2 |
| Product presentation fixes for failing cells | Out of scope
  (PYPOST-891) |

**No timeout-marker blockers.**

## Performance Concerns

None beyond suite budget already designed into smoke vs `slow`. Full
cartesian (25 cells) is `slow`-gated; default `make test-agent-e2e` keeps
the five smoke cells. `QTest.qWait(100)` after settle is bounded.

## User documentation (`doc/user/`)

N/A. Requirements exclude user-facing docs; this is an agent e2e matrix +
harness identity. Developer discoverability is Step 8 (`doc/dev/`).

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Automate discard no-op red-path proof | Optional marked variant that monkeypatches `_discard_chunk_buffer` to no-op under the streaming stub and asserts `count >= 2` on one smoke cell; keeps product code untouched. Prefer extending [PYPOST-892](https://pypost.atlassian.net/browse/PYPOST-892) rather than a new ticket | Jira: [PYPOST-892](https://pypost.atlassian.net/browse/PYPOST-892) |
| TD-2 | Lowest | Spot-check / KEY list for `REQUEST_DETAIL_TABS` | Optionally add to `KEY_WIDGET_IDS` + `test_ui_identity_spotcheck` / `doc/dev/ui_identity.md` when expanding the key set | Jira: [PYPOST-894](https://pypost.atlassian.net/browse/PYPOST-894) |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Share response-panel snapshot walk helpers | [PYPOST-869](https://pypost.atlassian.net/browse/PYPOST-869) |
| Optional `pypost_response_status` / `pypost_response_body` ids | [PYPOST-853](https://pypost.atlassian.net/browse/PYPOST-853) |
| Stub catalog naming for streaming helpers | [PYPOST-893](https://pypost.atlassian.net/browse/PYPOST-893) |
| Automate FR5 discard no-op red (889 family) | [PYPOST-892](https://pypost.atlassian.net/browse/PYPOST-892) |
| Product double-body discard fix | [PYPOST-887](https://pypost.atlassian.net/browse/PYPOST-887) |
| Triage findings / file Bugs from matrix | [PYPOST-891](https://pypost.atlassian.net/browse/PYPOST-891) |
| Epic for presentation coverage | [PYPOST-888](https://pypost.atlassian.net/browse/PYPOST-888) |

### Planned this ticket (not separate Debt)

- Step 8: brief `doc/dev/agent_e2e_presentation_matrix.md` + links from
  agent e2e / HTTP umbrella docs (FR7).

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions relative to AC | None — matrix + identity + findings meet DoD (docs Step 8) |
| Missing pytest timeout markers | **None** |
| Deviations from architecture | FR7 docs intentionally Step 8; Body-tab id hardened in Step 4 |
| Hardcoded values | Settle/flush budgets intentional |
| Merge / release blockers | **None** |
| Unticketed Debt creating Jira now | **Skipped per task instruction** |

**SAFE TO CLOSE** — presentation matrix is green under smoke; full matrix
is `slow`-gated; residual items are optional red automation and identity
spot-check. Shared panel helpers and response widget ids remain owned by
existing tickets. Do **not** create Jira tickets in this step.

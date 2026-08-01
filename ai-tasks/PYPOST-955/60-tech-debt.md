# PYPOST-955: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Mapping GET Send forced-timeout companion exists alongside the PYPOST-901
happy-path module. Inventory gate in `tests/test_agent_e2e_http.py` and companion
`test_mapping_get_send_settle_timeout_includes_step_and_excerpt` assert
`step=wait_response_after_mapping_get_send` and `response_excerpt` on forced
settle. Explicit timeout markers present. No production changes. Closes PYPOST-901
TD-1.

## Shortcuts Taken

- **Inventory red gate, not a red GUI assertion.** Step 3 proves companion
  existence via callable check (871 / 901 precedent). Rewrap already lives in
  `_wait_response`; a correct companion passes on first write.
- **Companion inlines rewrap** instead of calling `_wait_response`. Matches
  golden (PYPOST-950) and dialog (PYPOST-934) timeout companions; helper
  hardcodes 15 s `SEND_SETTLE_TIMEOUT_S`.
- **GET path only.** One forced timeout locks
  `wait_response_after_mapping_get_send` plus excerpt — satisfies Jira
  acceptance. POST step name remains in parent `_wait_response` only.
- **Impossible snapshot predicate** (`lambda _: False`) with 50 ms budget —
  mapping settle uses snapshot wait, not text-wait; avoids flakiness when 200
  arrives quickly.
- **Step 8 dev-doc row completed.** Two-test table + GET companion documented in
  `doc/dev/agent_e2e_http.md` (Step 8).

## Code Quality Issues

- **Duplicated rewrap shape** between `_wait_response` and the companion inline
  block. Acceptable for companion isolation; shared extraction tracked as
  PYPOST-956 if a third GUI Send module copies the pattern.
- **Module-local `FORCED_SETTLE_TIMEOUT_S = 0.05`.** Same constant name and
  value as golden/dialog companions; not yet centralized — low priority.
- **No assertion on excerpt content.** Companion checks presence and type of
  `response_excerpt`, not panel text — sufficient for regression lock on the
  diagnostic carrier.

Architecture vs implementation:

| Architecture | Implementation | Assessment |
| --- | --- | --- |
| Inventory gate in `test_agent_e2e_http.py` | `test_mapping_multi_url_settle_timeout_companion_exists` | Match |
| GET-only companion with inline rewrap | `test_mapping_get_send_settle_timeout_includes_step_and_excerpt` | Match |
| Impossible snapshot + 0.05 s budget | `lambda _: False`, `FORCED_SETTLE_TIMEOUT_S` | Match |
| Assert `step` + `response_excerpt` | Diagnostics assertions on forced timeout | Match |
| No happy-path / production changes | PYPOST-901 scenario unchanged | Match |

## Missing Tests

| Scenario | Status |
| --- | --- |
| Forced mapping GET Send settle timeout | Covered (agent e2e) |
| `step` + `response_excerpt` on forced timeout | Covered |
| Inventory: companion callable exists | Covered (unit gate) |
| Explicit timeout markers | **Present** — module `timeout(60)` + `agent_e2e` |
| Forced POST Send settle timeout companion | **Not covered** — optional follow-up |
| Caplog `agent_e2e_http_stub_installed name=url_router` | Not duplicated — PYPOST-957 |
| Shared rewrap helper extraction | Out of scope — PYPOST-956 |
| Full mapping failure matrix | Out of scope — requirements NFR minimalism |

**No timeout-marker blockers** (`.cursor/lsr/do-testing.md`).

## Performance Concerns

None. Forced timeout uses 50 ms snapshot poll inside a 60 s module budget;
typical companion run is sub-second offscreen. No new production metrics or log
volume.

## Deviations from Architecture

None material. GET-only coverage and inline rewrap were explicit architecture
decisions (20-architecture.md).

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Shared Send settle + timeout rewrap helper | [PYPOST-956](https://pypost.atlassian.net/browse/PYPOST-956) |
| Caplog for `name=url_router` in mapping GUI | [PYPOST-957](https://pypost.atlassian.net/browse/PYPOST-957) |
| Parent mapping multi-URL happy path | [PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901) |
| Golden Send timeout companion precedent | [PYPOST-950](https://pypost.atlassian.net/browse/PYPOST-950) |

### NON-BLOCKER

| ID | Priority | Item | Notes | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Low | Optional POST-path timeout companion | Force near-zero settle after POST Send; assert `step=wait_response_after_mapping_post_send` plus `response_excerpt`. GET companion closes PYPOST-901 TD-1; POST adds parity when both step names need independent CI locks. | [PYPOST-982](https://pypost.atlassian.net/browse/PYPOST-982) |
| TD-2 | Low | Centralize `FORCED_SETTLE_TIMEOUT_S` | Same 0.05 s constant appears in golden, dialog, and mapping companions; extract to shared test helper if a fourth companion copies it. | [PYPOST-983](https://pypost.atlassian.net/browse/PYPOST-983) |

### Accepted / out of scope (do not ticket)

- Full multi-URL / multi-method failure matrix — requirements NFR minimalism.
- Production Send settle or wait API changes — test-only scope.
- Asserting excerpt panel text content — diagnostic carrier lock is sufficient.
- Per-route DEBUG logging on stub install — PYPOST-901 observability decision.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | Inventory gate + inline rewrap intentional (precedent) |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None for companion code |
| Hardcoded values | `FORCED_SETTLE_TIMEOUT_S`, catalog URLs — same as siblings |
| Merge / release blocker debt | **None** for acceptance |

**SAFE TO CLOSE** — mapping GET Send settle timeout diagnostics are proven in CI.
Remaining items are optional POST companion, shared-helper hygiene, and caplog
proof — not acceptance gaps.

## Worklog

```
tokens_used: 38000
role: execution
step: 7
step_name: tech debt review
```

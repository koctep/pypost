# PYPOST-871: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Seed POST GUI Send scenario lands on the shared HTTP layer: method/URL/
body fill → `agent_e2e_http_stub(CANNED_SEED_POST_OK)` → status/body
assert with shared response-panel helpers. Inventory unit gate + GUI
scenario green. No product runtime change. Items below are non-blocking
follow-ups (Phase D: list only; this run does not create Jira issues).

## Shortcuts Taken

- Blank `agent_e2e_session` with explicit URL/method/body fill rather
  than opening the seeded Seed POST collection item (same scope
  boundary as env GET’s resolved-URL fill).
- Plain `return_value` stub (not `canned_send_with_one_chunk`) — matches
  env GET / golden status+body asserts; streaming once-only is owned by
  matrix / double-body locks.
- Local `_SEND_SETTLE_TIMEOUT_S = 15.0` and `_response_ready` (mirror
  env GET); shared settle constant already ticketed elsewhere.

## Code Quality Issues

- None material. Scenario closely mirrors
  `tests/test_agent_e2e_http_env.py` with POST body path added.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Catalog has `seed_post_ok` | Covered (unit, pre-existing) |
| Inventory: scenario module exists | Covered (unit) |
| GUI Send POST + body + shared stub | Covered (agent e2e) |
| Collection-tree open of Seed POST | Out of scope (deferred) |
| Caplog `name=seed_post_ok` | Optional sibling PYPOST-870 |

No timeout-marker blockers.

## Performance Concerns

None relative to DoD. Settle budget matches env GET.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent HTTP stub layer | [PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859) |
| Shared response-panel helpers | [PYPOST-869](https://pypost.atlassian.net/browse/PYPOST-869) |
| Shared Send settle timeout constant | [PYPOST-895](https://pypost.atlassian.net/browse/PYPOST-895) |
| Env Send timeout excerpt alignment | [PYPOST-896](https://pypost.atlassian.net/browse/PYPOST-896) |
| Caplog for stub install event | [PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870) |
| This scenario (self) | [PYPOST-871](https://pypost.atlassian.net/browse/PYPOST-871) |

### NON-BLOCKER — need NEW Jira Debt tickets (Phase D)

#### Seed POST Send timeout diagnostics use shared excerpt

- **Priority:** Low
- **Description:** Seed POST Send wait-timeout path mirrors env GET
  (step diagnostics only) and does not attach
  `response_panel_excerpt`, unlike golden / matrix / double-body.
- **Remediation:** Align timeout re-raise with
  `response_panel_excerpt(last)` + diagnostics key (same as PYPOST-896
  for env).
- **Jira:** [PYPOST-897](https://pypost.atlassian.net/browse/PYPOST-897)

#### Optional collection-tree open for Seed POST item

- **Priority:** Lowest
- **Description:** Scenario fills resolved URL/body rather than
  navigating to the seeded Seed POST request in the collection tree.
- **Remediation:** Add a separate marked scenario that selects the seed
  POST item via tree identities, then Sends under the shared stub.
- **Jira:** [PYPOST-898](https://pypost.atlassian.net/browse/PYPOST-898)

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None — new scenario module as planned |
| Hardcoded values | Settle 15s local (optional shared constant) |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR6 satisfied by seed POST GUI Send on the
shared stub with body fill and panel asserts. Remaining gaps are
optional hygiene / navigation, not blockers.

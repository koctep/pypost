# PYPOST-859: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Deterministic HTTP layer meets DoD: shared catalog +
`stub_agent_e2e_http` / `agent_e2e_http_stub`, golden and env Send on the
shared path, docs for adding canned responses, CI-deterministic under
offscreen Qt with real UI → RequestWorker path. Items below are
non-blocking follow-ups or work already owned by sibling stories.

## Shortcuts Taken

- **No URL→response router in v1.** Named catalog + optional callable
  `side_effect` covers golden/env and multi-call sequences; a full
  router can wait until multi-URL scenarios proliferate.
- **Env Send fills resolved seed URL** rather than driving collection
  tree open of the seed GET item. Proves shared HTTP + seeded session
  composition without owning collection-tree navigation complexity.
- **Catalog name inference via identity (`is`)** for the three shipped
  constants; custom results use `name=` (default `custom`).
- **Unit tests unmarked `agent_e2e`.** Fast non-GUI proofs stay on
  `make test`; agent pack stays GUI-focused.

## Code Quality Issues

- **Response-panel helpers duplicated** across golden and env Send
  modules (`_walk_values`, `_subtree_by_name`, ready predicates). Could
  share a tiny test helper; not required for AC.
- **Hardcoded Send settle 15s** mirrors golden; could be a shared
  constant later.
- **Architecture vs implementation:** no meaningful deviation —
  fixture module + plugin fixture + patch-at-RequestService-site.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Catalog builder / names | Covered (unit) |
| Stub install + restore | Covered (unit) |
| Callable side_effect | Covered (unit) |
| Golden uses shared stub | Covered |
| Env seeded Send uses shared stub | Covered |
| Caplog for `agent_e2e_http_stub_installed` | Not covered (optional) |
| Seed POST Send scenario | Catalog entry only; no GUI Send yet |
| URL router / multi-URL map | Not implemented (deferred) |

No timeout-marker blockers.

## Performance Concerns

None relative to DoD. Stub is a patch context; Send settle cost matches
pre-migration golden.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Failure artifacts | [PYPOST-860](https://pypost.atlassian.net/browse/PYPOST-860) |
| Make / CI entry for full env pack | [PYPOST-861](https://pypost.atlassian.net/browse/PYPOST-861) |
| Session / marker packaging | Delivered by PYPOST-858 |
| Seed inventory | Delivered by PYPOST-857 |

### NON-BLOCKER — need NEW Jira Debt tickets

#### Optional URL→canned response router helper

- **Priority:** Low
- **Description:** Authors with multi-URL Send flows may want a small
  map keyed by resolved URL (or method+URL) instead of a custom
  callable. Not required while golden/env use single canned results.
- **Remediation:** Add optional `responses: Mapping[str, HTTPRequestResult]`
  overload to `stub_agent_e2e_http` with documented match rules.
- **Jira:** [PYPOST-868](https://pypost.atlassian.net/browse/PYPOST-868)

#### Share response-panel snapshot helpers for agent Send tests

- **Priority:** Low
- **Description:** Golden and env HTTP Send tests duplicate walk /
  subtree / excerpt helpers. Drift risk as more Send scenarios land.
- **Remediation:** Extract to `tests/helpers/agent_e2e_response_panel.py`
  (or similar) and reuse.
- **Jira:** [PYPOST-869](https://pypost.atlassian.net/browse/PYPOST-869)

#### Optional caplog proof for HTTP stub install event

- **Priority:** Low
- **Description:** No automated assert that
  `agent_e2e_http_stub_installed` is emitted. Useful for logging-catalog
  regressions; not required for AC.
- **Remediation:** One small test with
  `caplog.at_level(INFO, logger="pypost.fixtures.agent_e2e_http")`.
- **Jira:** [PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870)

#### Seed POST GUI Send scenario on shared HTTP layer

- **Priority:** Low
- **Description:** `CANNED_SEED_POST_OK` is in the catalog but no agent
  e2e Send exercises POST body path via the shared stub.
- **Remediation:** Add a marked scenario mirroring env GET Send for POST
  (blank or seeded), asserting body/status.
- **Jira:** [PYPOST-871](https://pypost.atlassian.net/browse/PYPOST-871)

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None — catalog + CM + plugin fixture |
| Hardcoded values | Settle 15s / golden constants intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR8 satisfied by shared catalog/stub, golden +
env migration, docs, and offscreen CI determinism. Remaining gaps are
optional hygiene or sibling stories, not blockers.

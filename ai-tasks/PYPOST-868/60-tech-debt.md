# PYPOST-868: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

**Decision: ENABLE** — optional URL→canned Mapping overload shipped on
`stub_agent_e2e_http` with documented exact-URL match rules and fail-loud
miss. Unit proofs green; docs updated. No product UX change.

## Shortcuts Taken

- **Exact URL match only (v1).** No glob/prefix or method+URL compound
  keys. Sufficient for agent scenarios that fill resolved URLs; callable
  remains the escape hatch for streaming/ordered sequences.
- **Request extraction prefers `str` `.url`.** Avoids MagicMock `self`
  auto-attrs in unit calls; real RequestService path still passes
  `RequestData` with string URL.
- **No GUI multi-URL scenario.** Acceptance covered by unit router
  proofs; golden/env/seed still single-canned.

## Code Quality Issues

- Catalog identity naming still uses `is` checks; Mapping uses
  `name=url_router` default — consistent enough for logs.
- `_request_data_from_send_args` is private; public
  `url_router_side_effect` is reusable if authors need a custom CM.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Mapping multi-URL hit + restore | Covered |
| Mapping miss → AssertionError + known keys | Covered |
| Single result / callable unchanged | Covered (existing) |
| GUI multi-URL Send via Mapping | Not covered (optional) |
| method+URL compound keys | Not implemented (deferred) |

No timeout-marker blockers (module `timeout(10)`).

## Performance Concerns

None — dict lookup per Send in tests only.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Share response-panel helpers | [PYPOST-869](https://pypost.atlassian.net/browse/PYPOST-869) |
| Caplog proof for HTTP stub install | [PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870) |
| Seed POST GUI Send | [PYPOST-871](https://pypost.atlassian.net/browse/PYPOST-871) |

### NON-BLOCKER

#### Optional GUI multi-URL Send using Mapping router

- **Priority:** Low
- **Description:** No agent e2e GUI scenario yet drives two different
  URLs under one `stub_agent_e2e_http({...})` map. Unit coverage is
  enough for AC; a marked GUI smoke would raise confidence.
- **Remediation:** Add a small `agent_e2e` scenario (blank or seeded)
  that Sends twice to distinct resolved URLs with a Mapping stub and
  asserts panel outcomes.
- **Jira:** [PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901)

#### Optional method+URL compound map keys

- **Priority:** Lowest
- **Description:** Parent debt mentioned method+URL keys; v1 uses exact
  URL only. Revisit if two methods share one URL in a scenario.
- **Remediation:** Extend match rules (e.g. `"GET https://…"` keys) and
  document precedence vs bare URL keys.
- **Jira:** [PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902)

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None — ENABLE as planned |
| Hardcoded values | Catalog URLs intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR6 and DoD satisfied via ENABLE helper, unit
proofs, and docs. Remaining items are optional GUI / compound-key polish
(PYPOST-901 / PYPOST-902).

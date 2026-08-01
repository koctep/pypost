# PYPOST-901: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: marked `agent_e2e` scenario installs a two-URL Mapping stub,
Sends GET then POST under one scope, waits for panel settle, and asserts status
and canned body for each Send. Inventory gate + scenario green under
`make test-agent-e2e`. Explicit timeout markers present. No product runtime
change.

## Shortcuts Taken

- **Inventory red gate, not a red GUI test.** Step 3 proves module existence
  via `test_mapping_multi_url_gui_send_scenario_module_exists` (871 precedent).
  Mapping router, catalog, harness, and panel helpers were already green —
  a correct GUI scenario would pass on first write.
- **Blank session + explicit fill.** Architecture decision; mirrors seed POST
  boundary without collection-tree navigation.
- **Seed GET / seed POST catalog pair only.** Natural map keys already used in
  unit proofs and `doc/dev/agent_e2e_http.md`; not a full multi-URL matrix.
- **Plain canned results (no streaming).** Same as env GET / seed POST GUI
  paths; `canned_send_with_one_chunk` remains for matrix / double-body locks.
- **Happy-path only.** Timeout rewrap includes per-Send `step` and
  `response_excerpt` in `_wait_response`, but no companion test forces a
  near-zero settle budget to assert diagnostics (golden PYPOST-853 TD-3
  pattern).
- **Developer-doc discoverability deferred to Step 8.** Harness table row and
  URL-router GUI module link are planned in `20-architecture.md`; until Step 8,
  `tests/test_agent_e2e_harness_table_doc.py` reports the new module as
  `only_in_marks` (expected mid-workflow, not a scenario AC gap).

## Code Quality Issues

- **`_wait_response` helper is local.** Cleaner than inline try/except in env
  GET / seed POST, but duplicated pattern across Send scenarios — promote to
  shared helper only if a third module needs the same shape (TD-2).
- **Separate `_get_response_ready` / `_post_response_ready`.** Clear for two
  distinct bodies; could fold into a factory if more URLs are added later.
- **Hardcoded `_STATUS_LABEL = "Status: 200"`.** Same coupling as sibling Send
  scenarios; acceptable while catalog entries stay 200 OK.
- **`assert stub_agent_e2e_http is agent_e2e_http_stub`.** Intentional fixture
  identity check (mirrors seed POST); not production logic.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Two Sends under one Mapping stub + panel asserts | Covered (agent e2e) |
| Inventory: scenario module exists | Covered (unit gate) |
| Explicit timeout markers | **Present** — module `timeout(60)` + `agent_e2e` |
| Timeout companion asserts `step` + `response_excerpt` | Implemented in rewrap; **no** dedicated assert (TD-1) |
| Mapping router miss via GUI | Not covered — unit-only (`test_stub_agent_e2e_http_url_router_miss_raises`) |
| Caplog `agent_e2e_http_stub_installed name=url_router` | Optional — golden caplog proof exists (PYPOST-870); not duplicated here (TD-3) |
| Harness table / dev-doc discoverability (FR8) | **Step 8** — table guard currently red until doc row lands |
| method+URL compound map keys | Out of scope — [PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902) |

No timeout-marker blockers (`.cursor/lsr/do-testing.md`).

## Performance Concerns

None. Two bounded `SEND_SETTLE_TIMEOUT_S` waits inside a 60 s module timeout;
typical run ~25 ms offscreen. No new production metrics or log volume.

## Deviations from Architecture

None material for the scenario module. Step 8 doc touches (`doc/dev/agent_e2e.md`
harness table, `doc/dev/agent_e2e_http.md` GUI link) remain as planned — not
a code deviation.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent Mapping router | [PYPOST-868](https://pypost.atlassian.net/browse/PYPOST-868) |
| Shared response-panel helpers | [PYPOST-869](https://pypost.atlassian.net/browse/PYPOST-869) |
| Caplog for HTTP stub install | [PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870) |
| Shared Send settle timeout | [PYPOST-895](https://pypost.atlassian.net/browse/PYPOST-895) |
| method+URL compound map keys | [PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902) |
| This scenario (self) | [PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901) |

### Step 8 (same workflow — not optional polish)

| Item | Notes |
| --- | --- |
| Harness table row in `doc/dev/agent_e2e.md` | Add `tests/test_agent_e2e_http_mapping_multi_url.py` — clears harness guard |
| URL-router GUI link in `doc/dev/agent_e2e_http.md` | Point multi-URL section at new module + run command |

### NON-BLOCKER

| ID | Priority | Item | Notes | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Medium | Agent e2e timeout companion for mapping settle diagnostics | Mirror `test_agent_golden_settle_timeout_includes_step_and_excerpt`: force near-zero settle after GET or POST Send and assert `UiWaitTimeoutError.diagnostics["step"]` is `wait_response_after_mapping_get_send` or `wait_response_after_mapping_post_send` plus `response_excerpt`. | [PYPOST-955](https://pypost.atlassian.net/browse/PYPOST-955) |
| TD-2 | Low | Shared Send settle + timeout rewrap helper | Extract `_wait_response` pattern from mapping / env GET / seed POST if a third GUI Send module copies the same try/except + excerpt shape. | [PYPOST-956](https://pypost.atlassian.net/browse/PYPOST-956) |
| TD-3 | Low | Caplog proof for `name=url_router` in mapping GUI module | Optional sibling to PYPOST-870 golden caplog — low signal once unit + install log contract exist. | [PYPOST-957](https://pypost.atlassian.net/browse/PYPOST-957) |

### Accepted / out of scope (do not ticket)

- Full multi-URL / multi-method regression matrix — requirements NFR minimalism.
- Migrating env GET / seed POST to Mapping stubs — explicit out of scope.
- Router miss behavior in GUI — unit-covered; fail-loud contract unchanged.
- Per-URL route logging on stub install — observability decision (Step 6): noise without CI gain.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | Inventory gate intentional; Mapping stub is production fixture API |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None for scenario code |
| Hardcoded values | Status label + catalog URLs — same as siblings |
| Merge / release blocker debt | **None** for scenario AC; harness doc sync is Step 8 |

**SAFE TO CLOSE** — GUI multi-URL Mapping Send is proven on the real UI → Send
→ response-panel path. Remaining items are Step 8 discoverability, optional
timeout-diagnostic coverage, and shared-helper hygiene — not acceptance gaps.

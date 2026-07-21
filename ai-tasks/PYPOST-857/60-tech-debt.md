# PYPOST-857: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Seeded workspace fixtures meet DoD: builders + `write_agent_e2e_seed`,
isolated session proof via identity/model/items, inventory doc, and module
timeout markers. Items below are non-blocking follow-ups or work already
owned by sibling stories / Step 7.

## Shortcuts Taken

- **Builders + docs only (no committed golden JSON).** Architecture Option A;
  inventory lives in `pypost/fixtures/agent_e2e_seed.py` and is mirrored in
  `doc/dev/agent_e2e_seed.md`. Drift detection (Option C) deferred until it
  becomes a real maintenance issue.
- **FR8 via identity + model/item enumeration only.** Drive-then-snapshot was
  the alternate architecture path; blank-ready snapshot name scan correctly
  avoided. Presence proof does not open seeded requests or select the seeded
  env before asserting.
- **Present env ≠ active env.** Tests assert `Agent E2E` is listed and
  `currentText() == "No Environment"` — matching product default without
  `last_environment_id`. No select-and-resolve assertion for `base_url`.
- **No `AgentAppSession` seed hook.** Callers compose
  `write_agent_e2e_seed` + injectable dirs; packaging stays with PYPOST-858.
- **`logging.md` catalog deferred to Step 7.** Events
  `agent_e2e_seed_completed` / `agent_e2e_seed_failed` are implemented;
  catalog entry is Step 7 (noted in `50-observability.md`).
- **Full `make check` not re-run in this step.** Step 4 validated `make lint`
  plus `tests/test_agent_e2e_seed.py` (3 passed). Seed module is listed under
  `make test-agent-e2e`.

## Code Quality Issues

- **Hardcoded `collections=1` in success log.** INFO uses literal `1` instead
  of deriving from the written collection list; fine for a fixed catalog,
  slightly brittle if inventory grows.
- **Tree label format coupling.** Product-facing asserts use
  `f"GET {SEED_GET_REQUEST_NAME}"` / `POST …` because the sidebar shows
  `{method} {name}`. Documented in inventory; still a UI-format dependency.
- **Helper is re-export-heavy.** `tests/helpers/agent_e2e_seed.py` re-exports
  many constants for PYPOST-858 consumers; intentional, not dead code.
- **Architecture vs implementation:** no meaningful deviation — Option A
  writer, preferred FR8 identity path, unchanged lifecycle API.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Persist inventory via StorageManager | Covered |
| Seed present after ready (tree model + env items) | Covered |
| Isolation (seeded session does not bleed into blank) | Covered |
| Explicit timeout markers | Covered (`pytestmark = timeout(60)`) |
| `agent_e2e_seed_failed` ERROR + re-raise (caplog C1) | Not covered (optional) |
| Select seeded env / open request then snapshot | Not covered (optional FR8 path 2) |
| Variable resolution of `{{base_url}}` after select | Not covered (optional FR3 depth) |
| Docs ↔ constant inventory drift guard | Not covered (architecture Option C) |
| Full `make check` / sole `make test-agent-e2e` gate | Not re-run this step |

No timeout-marker blockers.

## Performance Concerns

None. Seed write is two small JSON persists; GUI proof is one offscreen
session load. Not a DoD concern.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Session fixture + `agent_e2e` marker packaging | [PYPOST-858](https://pypost.atlassian.net/browse/PYPOST-858) |
| Deterministic HTTP layer | [PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859) |
| Failure artifacts | [PYPOST-860](https://pypost.atlassian.net/browse/PYPOST-860) |
| Make / CI entry for full env pack | [PYPOST-861](https://pypost.atlassian.net/browse/PYPOST-861) |
| `logging.md` catalog for seed events | Step 7 (this story) |

### NON-BLOCKER

#### Caplog coverage for seed write failure

- **Priority:** Low
- **Description:** Unit test that forces `StorageManager` persist failure,
  asserts `agent_e2e_seed_failed` under
  `caplog.at_level(ERROR, logger="pypost.fixtures.agent_e2e_seed")`, and
  confirms the exception is re-raised (do-testing C1).
- **Remediation:** Add one mocked failure test in
  `tests/test_agent_e2e_seed.py`.
- **Jira:** [PYPOST-862](https://pypost.atlassian.net/browse/PYPOST-862)

#### Optional drive-then-snapshot / resolve proof

- **Priority:** Low
- **Description:** After ready, select `Agent E2E`, expand collection / open
  Seed GET, then assert via snapshot or URL field identity that
  `{{base_url}}` / method match inventory. Strengthens FR3/FR4 beyond
  sidebar presence.
- **Remediation:** Extend product-facing tests when env-pack scenarios need
  active-env or open-request guarantees; otherwise leave to consumers.
- **Jira:** [PYPOST-863](https://pypost.atlassian.net/browse/PYPOST-863)

#### Inventory drift guard (code ↔ doc)

- **Priority:** Low
- **Description:** Architecture deferred builders + committed golden JSON
  (Option C) until drift hurts. A lightweight assert that inventory
  constants match names listed in `doc/dev/agent_e2e_seed.md`, or a
  single-source generator, would catch doc/code skew.
- **Remediation:** Add only if inventory churn increases; not needed for
  the current fixed four-row catalog.
- **Jira:** [PYPOST-864](https://pypost.atlassian.net/browse/PYPOST-864)

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** — module `timeout(60)` |
| Deviations from architecture | None — Option A + FR8 identity path |
| Hardcoded values | Inventory constants intentional; log `collections=1` minor |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR9 satisfied by fixture pack, isolation, inventory
doc, and ready-after identity proof. Remaining gaps are optional hardening or
sibling packaging, not blockers for this story.

## Worklog

```
tokens_used: 14500
role: execution
step: 6
step_name: review
```

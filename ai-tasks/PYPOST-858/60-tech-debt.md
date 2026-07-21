# PYPOST-858: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Shared packaging meets DoD: registered `agent_e2e` marker, function-scoped
blank + seeded fixtures, harness migration without coverage loss, make
selection via `-m "agent_e2e and not slow"` with documented file-list
override, and timeouts on all harness modules. Items below are
non-blocking follow-ups or work already owned by sibling stories.

## Shortcuts Taken

- **Function scope, not pytest session scope.** Jira “session fixture”
  means packaging for `AgentAppSession`; sharing one mutable app across
  mutating tests would violate FR7 / env-contract isolation.
- **Two fixtures (blank + seeded), not always-seeded.** Preserves blank /
  golden / lifecycle proofs; env scenarios that need inventory use
  `seeded_agent_e2e_session`.
- **Multi-session tests keep direct `AgentAppSession`.** Fixtures yield
  one instance per request; isolation proofs need two independent
  sessions (architecture decision).
- **Golden HTTP remains a one-off patch.** Deterministic HTTP layer is
  PYPOST-859; blank fixture only.
- **`--strict-markers` not enabled.** Registration alone satisfies AC;
  strict mode is optional project-wide hygiene.
- **Module-level `agent_e2e` mark.** Pure storage unit test in
  `test_agent_e2e_seed.py` is selected by the marker with the rest of
  the module (intentional; cheap).

## Code Quality Issues

- **Hardcoded `ready_timeout=30.0`** in both fixtures (mirrors prior
  harness defaults). Could be a shared constant later; not a DoD issue.
- **Documented harness table vs discovery.** `make test-agent-e2e` grows
  with any new `@pytest.mark.agent_e2e` module; the table in
  `agent_e2e.md` can lag until authors update docs.
- **Architecture vs implementation:** no meaningful deviation — Option A
  function scope, Option B blank+seeded, Option B plugin + marker make.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Blank fixture ready gate | Covered via migrated lifecycle/identity/… |
| Seeded fixture inventory after ready | Covered (`seeded_agent_e2e_session`) |
| Multi-session isolation | Covered (direct API, still marked) |
| Marker + make selection | Covered (`make test-agent-e2e` → 31) |
| Explicit timeout markers | Covered (module `timeout(60)`) |
| Caplog for `agent_e2e_fixture_ready` | Not covered (optional) |
| File-list `PYTEST_ARGS` override CI proof | Documented; not a separate automated gate |
| `--strict-markers` | Not enabled (optional) |

No timeout-marker blockers.

## Performance Concerns

None relative to DoD. Function-scoped rebuild cost matches pre-migration
per-test `with AgentAppSession` blocks. Marker collection deselects the
rest of the suite quickly.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Deterministic HTTP layer | [PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859) |
| Failure artifacts | [PYPOST-860](https://pypost.atlassian.net/browse/PYPOST-860) |
| Make / CI entry for full env pack | [PYPOST-861](https://pypost.atlassian.net/browse/PYPOST-861) |
| PYPOST-854 marker/make overlap for `agent_e2e` | Absorbed by this story |

### NON-BLOCKER — need NEW Jira Debt tickets

#### Enable pytest `--strict-markers` (or document deferral)

- **Priority:** Low
- **Description:** Registration prevents unknown-mark warnings for
  `agent_e2e`, but typos of other marks still warn only. Enabling
  `--strict-markers` in `pyproject.toml` addopts would turn unknown marks
  into errors project-wide.
- **Remediation:** Add `--strict-markers` after a one-time audit of
  existing marks, or document intentional deferral in testing.md.
- **Jira:** [PYPOST-865](https://pypost.atlassian.net/browse/PYPOST-865)

#### Keep `agent_e2e.md` harness table synced with marked modules

- **Priority:** Low
- **Description:** Default make selection is `-m agent_e2e`; the
  documented module table can drift when new modules are marked without
  updating the umbrella doc.
- **Remediation:** Checklist in PR template / agent_e2e.md, or a cheap
  test that asserts marked modules ⊆ documented list (or generates the
  table).
- **Jira:** [PYPOST-866](https://pypost.atlassian.net/browse/PYPOST-866)

#### Optional caplog proof for packaging ready event

- **Priority:** Low
- **Description:** No automated assert that
  `agent_e2e_fixture_ready mode=blank|seeded` is emitted. Useful for
  logging-catalog regressions; not required for AC.
- **Remediation:** One small test with
  `caplog.at_level(INFO, logger="tests._pytest_plugins.agent_e2e")`.
- **Jira:** [PYPOST-867](https://pypost.atlassian.net/browse/PYPOST-867)

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None — function scope, two fixtures, plugin |
| Hardcoded values | `ready_timeout=30.0` intentional parity |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR9 satisfied by marker registration, blank +
seeded fixtures, harness migration, make dual selection, and docs.
Remaining gaps are optional hygiene or sibling stories, not blockers.

## Worklog

```
tokens_used: 28000
role: execution
step: 6
step_name: review
```

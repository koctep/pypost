# PYPOST-870: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: installing the shared HTTP stub emits
`agent_e2e_http_stub_installed` under caplog; module timeout marker present.
No production changes; no blockers.

## Shortcuts Taken

- **Single catalog name.** Proof asserts `name=golden_ok` only. Other
  catalog / `url_router` / custom names remain optional (AC is the install
  event, not exhaustive `name=` matrix).
- **Hardcoded event prefix.** Assert string matches production /
  `logging.md` (intentional).
- **Dedicated pure-unit module.** Proof lives in
  `tests/test_agent_e2e_http_stub_logs.py` (mirrors PYPOST-867 packaging
  logs) rather than extending `tests/test_agent_e2e_http.py` — keeps
  behavioral stub tests separate from logging-catalog proofs.

## Code Quality Issues

- None material. Module follows sibling HTTP / packaging caplog style.
- Dedicated pure-unit module (no `agent_e2e` marker) keeps proof out of the
  harness table — intentional.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Install → `agent_e2e_http_stub_installed name=golden_ok` | Covered (this ticket) |
| Other catalog names (`seed_get_ok`, `seed_post_ok`, …) | Not covered (optional) |
| Mapping install → `name=url_router` | Not covered (optional) |
| Custom `name=` override | Not covered (optional) |
| Live GUI path re-assert of same event | Not covered (optional; unit path sufficient for AC) |

No timeout-marker blockers.

## Performance Concerns

None. Pure unit test is sub-millisecond; no GUI session.

## Follow-up Tasks

### Already tracked (do not reticket)

None specific to this HTTP-stub install caplog debt beyond the closed
parent [PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859) item
that spawned this ticket. Sibling packaging ready proof:
[PYPOST-867](https://pypost.atlassian.net/browse/PYPOST-867).

### NON-BLOCKER

#### Optional caplog matrix for other install name tokens

- **Priority:** Lowest
- **Description:** Optionally assert
  `agent_e2e_http_stub_installed name=` for `seed_get_ok`,
  `seed_post_ok`, `double_body_lock_ok`, `url_router`, and an explicit
  custom `name=` so catalog rename regressions are wider than golden_ok.
- **Remediation:** Parametrize
  `test_stub_agent_e2e_http_logs_installed_event` (or add siblings) in
  `tests/test_agent_e2e_http_stub_logs.py`.
- **Jira:** [PYPOST-903](https://pypost.atlassian.net/browse/PYPOST-903)

- **Jira:** [PYPOST-904](https://pypost.atlassian.net/browse/PYPOST-904)

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** — module `timeout(10)` |
| Deviations from architecture | None — test-only as planned |
| Hardcoded values | Event prefix intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR4 and DoD satisfied. Remaining items are optional
name-matrix / live-path polish (PYPOST-903 / PYPOST-904).

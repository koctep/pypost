# PYPOST-829: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

H3 confirmed and fixed: both storage gateways tear down finished workers with
`deleteLater()` + short `wait(100)` before draining pending work; WARNING on
wait timeout; stress canary green. Items below are non-blocking follow-ups.
**Do not create Jira tickets in this step** — tech-debt sync fills the Jira
column later.

## Shortcuts Taken

- **Duplicated finish teardown in both gateways.** Env and collection
  `_on_worker_finished` share the same capture → `deleteLater` → short `wait`
  → WARNING → pending-restart pattern and the same `_WORKER_FINISH_WAIT_MS`
  constant. Architecture allowed an optional shared private helper; kept
  inline for a minimal, attributable fix (same pattern as tabs/code_editor
  connect-site hygiene, but finish-slot ordered for pending restart).
- **No `caplog` assertion for the wait-timeout WARNING.** Observability
  intentionally skipped it — timeout is expected to be rare on the happy path;
  the stress canary covers segfault / stranded-completion regression.
- **Full `make check` not re-run.** Step 3–4 validated `make lint` plus focused
  gateway + responsiveness + stress isolation (**20 passed**). Same scoped
  pattern as sibling harness tickets (PYPOST-827 / 828).
- **Stress harness keeps module-local `QApplication`.** Matches existing gateway
  unit-test pattern; shared-`qapp` alignment remains PYPOST-830.

## Code Quality Issues

- **Finish-path DRY** — see Shortcuts / TD-1. Two modules, one lifecycle rule;
  drift risk if a future change touches only one gateway.
- **Hardcoded `_WORKER_FINISH_WAIT_MS = 100`.** By design (architecture: tens to
  a few hundred ms; must not become unbounded GUI `wait()`). Raise only with
  field evidence of WARNING spam — not a refactor target now.

No naming, structure, or pending-restart semantic issues in the product fix.

## Missing Tests

| Scenario | Status |
| --- | --- |
| ≥200 rapid cycles + pending restart + GC (env) | Covered (stress) |
| ≥200 rapid cycles + queued second load + GC (collection) | Covered (stress) |
| H3 idle-but-missing-completion fingerprint assertion | Covered (stress) |
| Gateway unit + responsiveness isolation after fix | Covered (20 passed) |
| Wait-timeout WARNING via `caplog` | Not covered — intentional (rare path) |
| Negative probe that drops `deleteLater`/`wait` and expects fail | Not added — stress canary is the regression |
| Suite-prefix (tabs/code_editor then process_until) green | Not claimed — non-H3 crash under prefix; see Already tracked |
| Full `make check` green after this story | Not re-run for PYPOST-829 |

Timeout markers: `pytestmark = pytest.mark.timeout(120)` on
`tests/test_storage_gateway_h3_stress.py`; related gateway/responsiveness
modules retain existing markers. **No timeout-marker blockers.**

## Performance Concerns

None material. Short `wait(100)` runs on the GUI thread only after
`QThread.finished` has already been delivered to the finish slot; it usually
returns immediately. Stress canary cost ~12 s total for both gateways — kept as
a permanent regression probe (architecture Phase 2b).

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Lowest | Optional shared finish-teardown helper for both gateways | Extract only if a third consumer appears or drift becomes likely; not required for DoD | Jira: [PYPOST-881](https://pypost.atlassian.net/browse/PYPOST-881) |
| TD-2 | Low | Run full `make check` when sibling suite noise is clear | Deferred scoped gate; not a DoD blocker | Jira: [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882) |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Align remaining gateway / stress tests on shared `qapp`; suite event-loop affinity | [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) |
| Suite-prefix crash entering `test_process_until_exits_on_wall_clock_deadline` after tabs/code_editor churn | Same affinity class as above — **not** H3 stranded-completion; out of scope for PYPOST-829 (see `30-findings.md`) |
| Tabs-presenter close-focus / land-on-plus failures | PYPOST-824 / 825 / 826 (and related) — unrelated to gateway lifecycle |
| Wire `worker_operation` into env gateway timeout detail | [PYPOST-878](https://pypost.atlassian.net/browse/PYPOST-878) |
| Port hang-resistant wait into env-presenter nested wait | [PYPOST-877](https://pypost.atlassian.net/browse/PYPOST-877) |

### Planned this ticket (not separate Debt)

- Step 7: update `doc/dev/environment_storage_async.md` (and collection loading
  notes) for finish-path `deleteLater` / short `wait` / WARNING event names —
  not a Debt ticket.

## User documentation

N/A — internal gateway lifecycle hygiene; no `doc/user/` updates. Developer
docs are Step 7.

## Blocker Review

**SAFE TO CLOSE**

- DoD met: H3 confirmed under Approach C; both gateways fixed symmetrically;
  pending restart preserved; stress + isolation green; WARNING on wait timeout.
- TD-1 / TD-2 are polish and quality-gate deferrals, not acceptance gaps.
- Non-H3 suite-prefix / process_until noise is owned by PYPOST-830 (and related
  tabs tickets); not recreated here.
- No missing pytest timeout markers.

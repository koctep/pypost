# PYPOST-1297: Technical Debt Analysis

Scope: the only changed file is `tests/test_websocket_outbound_metrics_repro.py`. It adds the
helpers `_outbound` and `_run_loopback_send_table`, the row constants `_LOOPBACK_*`, and the
test `test_real_loopback_send_records_outbound_metrics_and_reaches_peer`.
`git diff -- pypost` is empty. There is no production change.

There are **no technical-debt blockers**. Every item below is NON-BLOCKER. No new Jira issue
is needed. The pre-existing items already have Jira keys.

## Shortcuts Taken

- **Coverage-only evidence lives in a document, not in the suite (TD-3, Low, no follow-up).**
  The Step 3 mutation probe `tests/test_pypost_1297_mutation_probe.py` was temporary. The
  orchestrator deleted it at the Step 3 gate. The only proof that the test fails for the
  intended reasons (M1-M4) is the record in `30-failing-repro.md`. A durable mechanism, such as
  a committed probe module or a mutation-testing tool, is **not warranted**, for these reasons:
  - A committed probe would be a set of tests that are designed to fail. Wrapping them in
    `pytest.raises` would turn them into tests about the test, coupled to private presenter and
    adapter methods (`_on_frame_sent`, `QtWebSocketTransport.send_*`). Each probe would also open
    four more real sockets in every `make check`.
  - The assertions are plain equality checks on deltas, with fixed messages. A later edit can
    weaken them only by changing those lines, which code review sees directly.
  - The repository has no mutation-testing target. Adding one would be a tooling decision for
    the whole suite, not for this test.
- **Open path bypasses the presenter (TD-4d, Low, no follow-up).** The test calls
  `controller.open(...)` directly, not `presenter.handle_connect`. So the session-slot policy,
  URL resolution and the presenter connect flow are not exercised. The DoD covers the send path
  and metric recording only. The sends use the real `controller.send_*` →
  `frame_sent` → `_on_frame_sent` chain that the tab uses. Requirements allow this, and the
  architecture chose it on purpose.

## Code Quality Issues

- **Coupling to internals (TD-4c, Low, no follow-up).** The new code reads metrics only through
  the public `CollectorRegistry.get_sample_value` API and the series names from the metrics
  catalog. It touches no private attribute. It does depend on `MetricsRegistry.registry` being a
  per-instance `CollectorRegistry`, which is the documented isolation design. The older
  PYPOST-1288 tests in the same module still use the private `_value.get()`. That code is out of
  scope and was not changed. It is cosmetic, so no follow-up.
- **`None` treated as `0.0` in `_outbound` (TD-4f, Low, no follow-up).** `get_sample_value`
  returns `None` for a series that was never incremented, or for a wrong name or label. A
  renamed metric would therefore read `0` before and after. This does **not** hide a defect in
  this table. Rows 0 and 1 expect a count delta of +1 and a non-zero bytes delta, so a missing
  or renamed series fails on row 0 or row 1. The zero-byte rows alone could not detect a missing
  bytes series, but they always run after rows 0 and 1. If the rows are ever reordered or split
  so that a zero-byte row runs alone, it should assert that the series exists. This is recorded
  as a note, not a task.
- **Duplication with existing tests (TD-4e, Low, no follow-up).**
  `test_real_loopback_roundtrip` (`tests/test_websocket_session_controller.py`) also sends text
  and binary through the real adapter. It checks the inbound echo and `frame_sent` payloads, and
  it has no metrics. The new test checks outbound metrics and peer receipt, with no echo. The
  overlap is one connection setup, and the assertions do not overlap. The PYPOST-1288
  `FakeTransport` tests cover blocked and rejected sends, which a real socket cannot produce
  on demand. All three layers stay. Merging them would lose either isolation or failure clarity.
- **Old wait style in the existing loopback test (Low, no follow-up).**
  `test_real_loopback_roundtrip` still uses 50-iteration `processEvents` loops instead of
  `wait_until`. It was out of scope (DoD: leave it unchanged) and it passes. Cosmetic.
- **Module name (Low, no follow-up).** `test_websocket_outbound_metrics_repro.py` now holds
  both the PYPOST-1288 repro and a real-socket integration test. The module docstring names both
  tasks. A rename would only churn history.
- **Import source (Low, no follow-up).** `wait_until` is imported from `pypost.agent.ui_wait`,
  not from the `tests/helpers/qt_wait.py` re-export. Both styles exist in `tests/` (7 and 4
  modules). No convention is enforced.

## Missing Tests

- **Timeout markers: compliant, no blocker.** The module has `pytestmark =
  pytest.mark.timeout(30)`. The new test has its own `@pytest.mark.timeout(60)`. Every wait is
  `wait_until(..., timeout=5.0)`, so the worst case is 5 waits × 5 s = 25 s, within 60 s.
- **Teardown completeness (TD-4b, Low, no follow-up).** `presenter.teardown()` in `finally`
  stops the flush timer, closes the session with code 1000 and aborts it. The fixture
  `ws_test_server` stops the server. The `WebSocketSessionController` and its child
  `QtWebSocketTransport` are not `deleteLater`'d. They are freed by Python reference counting
  when the helper returns. This matches every other controller test in the module and in
  `test_websocket_session_controller.py`. No leak or cross-test effect was seen in the Step 4 and
  Step 5 runs. If Qt object lifetime warnings appear later, add `controller.deleteLater()` to
  the `finally` block.
- **Out of scope by the requirements:** inbound metrics, control frames, and blocked, invalid
  or rejected sends on a real socket. PYPOST-1288 covers the last three with `FakeTransport`.
- No DoD criterion is left without a test. See the Step 4 DoD trace in `00-roadmap.md`.

## Performance Concerns

- **Real-socket test in the suite (TD-4a, Low, no follow-up).** The test opens one loopback
  connection and sends four messages, in about 1.9-2.1 s per run (Step 3 and Step 4). Under
  full parallel `make check` load, the 5 s open and receipt waits are the flakiness risk. The
  waits are bounded and use the same 5 s budget as the other `ws_test_server` tests. The peer
  is `SILENT`, so no inbound traffic interleaves with the outbound assertions. Metric deltas are
  asserted synchronously before any wait, so a slow event loop can only cause a
  `not received by peer` timeout, never a wrong metric result. The test did not fail in the one
  full `make check` run (Step 5), the three isolated runs (Step 4), or the targeted runs. If it
  ever flakes, raise the receipt wait first. Do not drop the peer check, because the DoD
  requires it.
- No production performance impact. No runtime code changed.

## DoD Status Note

The DoD says `make check` must show no failure outside PYPOST-1299, PYPOST-1298, PYPOST-1263,
PYPOST-1305 and PYPOST-1306. The Step 5 `make check` run also failed
`test_env_persistence_e2e.py`, a temp-dir flake that is not in that set. Step 5 triaged it as
not caused by this task: it passed 3 of 3 times on the current tree and 15 of 15 times at
`286b3a4c`, and the diff does not touch that code. It was filed as PYPOST-1311.

**Resolved.** The gate is baseline-relative: a confirmed, filed flaky failure belongs to the
filed pre-existing set (`failing-tests-triage.md`). The gate owner (orchestrator) confirmed that
PYPOST-1311 joins that set. The `make check` criterion is therefore met, baseline-relative.
No open decision remains.

## User Documentation

User documentation in `doc/` is N/A: there is no user-facing change. This is a test-only
coverage task.

## Follow-up Tasks

No new Jira issue is needed. Summary:

| ID | Item | Priority | Follow-up | Existing key |
| --- | --- | --- | --- | --- |
| TD-1a | `make check` exit-policy test timeout | NON-BLOCKER, pre-existing | n (tracked) | [PYPOST-1299][] |
| TD-1b | `test_env_persistence_e2e` temp-dir flake | NON-BLOCKER, pre-existing | n (tracked) | [PYPOST-1311][] |
| TD-2 | `make lint` does not run flake8 on `tests/` | NON-BLOCKER, pre-existing | n (tracked) | [PYPOST-1303][] |
| TD-3 | Mutation evidence only in `30-failing-repro.md` | Low | n | — |
| TD-4a | Real-socket timing risk (5 s waits under load) | Low | n | — |
| TD-4b | Controller not `deleteLater`'d | Low | n | — |
| TD-4c | Registry coupling; PYPOST-1288 `_value.get()` | Low | n | — |
| TD-4d | Open path bypasses `presenter.handle_connect` | Low | n | — |
| TD-4e | Overlap with roundtrip and `FakeTransport` tests | Low | n | — |
| TD-4f | `None` read as `0.0` in `_outbound` | Low | n | — |

Pre-existing items:

- **NON-BLOCKER — pre-existing:**
  `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing`
  timed out (120 s worker kill) in `make check`. Existing Jira: [PYPOST-1299][].
- **NON-BLOCKER — pre-existing, flaky:**
  `tests/test_env_persistence_e2e.py::test_presenter_load_shows_no_env_when_key_missing_for_encrypted_data`
  failed with `OSError: [Errno 39] Directory not empty` in `TemporaryDirectory.__exit__` under
  full-suite load, and passed in isolation. Existing Jira: [PYPOST-1311][]. See the DoD Status
  Note above.
- **NON-BLOCKER — pre-existing:** `make lint` runs flake8 on `pypost/` only, so the changed test
  module gets no static analysis from the gate. Step 5 reviewed it by hand (100-character
  limit, no unused names). Existing Jira: [PYPOST-1303][].

[PYPOST-1299]: https://pypost.atlassian.net/browse/PYPOST-1299
[PYPOST-1303]: https://pypost.atlassian.net/browse/PYPOST-1303
[PYPOST-1311]: https://pypost.atlassian.net/browse/PYPOST-1311

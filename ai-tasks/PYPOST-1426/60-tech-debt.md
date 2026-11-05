# PYPOST-1426: Technical Debt Analysis

## Shortcuts Taken

1. **Simulated faults via library-service doubles (no live TCP/TLS)**:
   Network drop and mid-stream reset are injected as `ConnectionResetError` /
   `BrokenPipeError` and abort-callback blocks rather than a real socket that
   closes mid-`recv`. This keeps CI deterministic; true HTTP session abort
   registration remains PYPOST-1454.
2. **Error-substring matching on dialog labels**:
   Assertions match substrings (`reset`, `json`, `schema`, `broken pipe`) in the
   user-facing banner text derived from `str(exc)`. Stable structured error codes
   on the banner are not introduced.
3. **Discovery corrupt-manifest matrix deferred**:
   Suite focuses on remote *collection* fetch/import per ticket scope; listing
   failures during `ManifestDiscoveryWorker` are only covered indirectly by
   existing discovery tests.

## Code Quality Issues

1. Fault helper and dialog repro share wait/processEvents patterns with
   `test_variable_import_virtualization_repro.py` — a shared Qt wait helper for
   discovery/fetch idle could reduce duplication (out of scope).
2. `fail_then_recover_side_effect` uses a mutable dict counter rather than
   `itertools.count` / closure int; acceptable for tests, not production style.

## Missing Tests

1. **Live HTTP/TLS mid-stream RST with session.close on CancellationToken**:
   Still needs a real client transport that registers abort callbacks (pairs with
   PYPOST-1454).
2. **Slow-drip partial response that eventually succeeds**:
   Not covered — only hard failures and cancel-during-block are asserted.
3. **Discovery-path truncated library manifest catalog JSON**:
   Not in this suite; could break combo population differently than fetch.

## Performance Concerns

1. Dialog fault tests open a full `ImportCollectionVariablesDialog` per case
   (~150–300ms each). Acceptable for ten focused cases; parametrize carefully if
   expanding matrix.

## Follow-up Tasks

1. **Shared Qt idle-wait helper for import-dialog tests**:
   - Suggested SP: 2
   - Jira: [PYPOST-1455](https://pypost.atlassian.net/browse/PYPOST-1455)
   - Extract `_wait_for_manifest_discovery` / fetch-idle helpers used across
     virtualization, discovery, abort, and fault-injection repros into
     `tests/helpers/` to avoid drift.
2. **Discovery corrupt-catalog fault-injection cases**:
   - Suggested SP: 3
   - Jira: [PYPOST-1456](https://pypost.atlassian.net/browse/PYPOST-1456)
   - Inject truncated/invalid JSON during `list_manifest_collections` /
     connection listing and assert discovery error banner + retry (PYPOST-1424 UX).
3. **Slow-drip / delayed-success remote read characterization**:
   - Suggested SP: 2
   - Jira: [PYPOST-1457](https://pypost.atlassian.net/browse/PYPOST-1457)
   - Assert loading chrome stays visible and UI remains responsive while a
     remote read dribbles then completes without error.
4. **`NON-BLOCKER — pre-existing`: Pre-existing lockfile drift**:
   - Jira: [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)
   - Test node: `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`
5. **`NON-BLOCKER — pre-existing`: Makefile test suites time out under parallel load**:
   - Jira: [PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413)
6. **Related (already ticketed): HTTP session abort registration**:
   - Jira: [PYPOST-1454](https://pypost.atlassian.net/browse/PYPOST-1454)
   - Suggested SP: 3 (already on ticket)

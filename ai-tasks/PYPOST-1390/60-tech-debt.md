# PYPOST-1390: Technical Debt Analysis

## Shortcuts Taken

1. **Toggle later-span shift remains linear** — Out of scope by design. `handle_click` still walks every later span to apply `delta`. Bisect only needed ordered starts; redesigning offset tracking (piece table / Fenwick / B-tree) was deferred.
2. **No MouseMove throttling** — Requirements explicitly exclude event debouncing as a substitute for better hit resolution. After bisect, hover cost is O(log N) per move; throttling remains optional if profiling still shows event-loop pressure on low-end machines.
3. **Inclusive `end_pos` quirk frozen** — Formatter records `end_pos` as the exclusive write cursor, but hit-testing treats both ends inclusive. Preserved for semantic freeze (FR-2); not “fixed” to exclusive ends.
4. **No parallel `starts` cache** — Architecture chose `key=attrgetter("start_pos")` on the live list to avoid dual-structure sync on toggle. Accepted trade-off (cheap attr reads vs sync risk).

## Code Quality Issues

1. **Repro instruments private `_spans`** — `tests/test_pypost_1390_failing_repro.py` assigns `_InstrumentedSpans` onto `controller._spans` with `# type: ignore[assignment]`. Acceptable for deterministic visit accounting; a public test hook was not added to avoid widening production API. *Accepted by design / low risk — no ticket.*
2. **`span_at` docstring length** — Slightly longer than neighboring one-liners; documents bisect + inclusive contract deliberately for maintainers. No refactor needed.

## Missing Tests

1. **Timeout markers** — Module `pytestmark = pytest.mark.timeout(30)` on the PYPOST-1390 suite. **Zero blockers.**
2. **Wall-clock hover benchmarks** — Intentionally omitted (flaky). Logarithmic visit budget + oracle parity cover AC-1 / AC-5.
3. **Extreme N (thousands of spans)** — Suite uses N=512. Larger synthetic loads are optional polish, not required for DoD. *Out of scope / not required — no ticket.*

## Performance Concerns

1. **O(N) later-span shift on each toggle** — Still the remaining interactivity cost when many spans exist and the user reveals many tokens in sequence. Lower frequency than hover, but grows with span count.
2. **Unthrottled MouseMove** — Event volume is unchanged; only per-event work improved. Residual risk on very low-end hardware if the rest of the event filter (cursor / tooltip) dominates.

## Follow-up Tasks

### Pre-existing / flaky suite failures (Step 4 triage)

Pre-existing / flaky suite failures triaged during Step 4 (`make test` at working tree vs baseline `5aadedc85295d393027b7fa72f6e3742b71d674d`). Verdict for all: **NON-BLOCKER — pre-existing** (or flaky with same root cause at base). Not caused by `span_at` bisect.

| Test id(s) | Verdict | Jira |
| --- | --- | --- |
| `tests/test_bundled_examples_packaging.py::test_explicit_packages_cover_application_tree_and_examples` | NON-BLOCKER — pre-existing | [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) |
| `tests/test_makefile_install_seed_contract.py::test_committed_seed_covers_independent_source_inventory` | NON-BLOCKER — pre-existing | [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) |
| `tests/test_http_client.py` (blank_path_segment_rejected cluster) | NON-BLOCKER — pre-existing | [PYPOST-1534](https://pypost.atlassian.net/browse/PYPOST-1534) |
| `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift` | NON-BLOCKER — pre-existing | [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397) |
| `tests/test_mcp_server_impl.py` (RequestData / defaults cluster) | NON-BLOCKER — pre-existing | [PYPOST-1535](https://pypost.atlassian.net/browse/PYPOST-1535) |
| `tests/test_mcp_process_tool_refresh_repro.py::test_process_mode_refresh_collection_isolates_neighbor_and_proxy_servers` | NON-BLOCKER — flaky (port bind); passes solo / re-run | [PYPOST-1546](https://pypost.atlassian.net/browse/PYPOST-1546) |
| `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` | NON-BLOCKER — pre-existing | [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475) |
| `tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery` | NON-BLOCKER — pre-existing | [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475) |
| `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics` | NON-BLOCKER — pre-existing | [PYPOST-1492](https://pypost.atlassian.net/browse/PYPOST-1492) |

### New follow-ups from this implementation

| ID | Priority | Description | Notes / Jira |
| --- | --- | --- | --- |
| TD-1 | Low | Replace linear later-span offset shifting in `ResponseMaskController.handle_click` with an ordered offset structure (piece table / Fenwick / similar) so toggle cost stays sublinear under high span counts | Deferred from PYPOST-1379 / 1380; left out of PYPOST-1390 scope. Jira: [PYPOST-1547](https://pypost.atlassian.net/browse/PYPOST-1547) |
| TD-2 | Low | Optional viewport MouseMove throttling / debouncing for mask hover feedback if profiling still shows event-loop pressure after O(log N) `span_at` | Explicitly out of scope for PYPOST-1390; optional residual. Jira: [PYPOST-1548](https://pypost.atlassian.net/browse/PYPOST-1548) |

## Notes

- Step 3 repro `tests/test_pypost_1390_failing_repro.py` is green after bisect.
- Inclusive-end freeze and private `_spans` instrumentation are accepted by design (no tickets).
- Related already-ticketed masking debt (not re-filed): PYPOST-1391, PYPOST-1392, PYPOST-1396, PYPOST-1388.

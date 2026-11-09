# PYPOST-1492: Technical Debt Analysis

## Shortcuts Taken

- Regenerated `ai-tasks/PYPOST-376/baseline-metrics.md` only (`http_client.py`
  Baseline LOC `378`→`395`) without refactoring `pypost/core/http_client.py` to
  reclaim LOC. Matches ticket scope: restore snapshot equality while caps and
  assertion rigor stay unchanged.
- Did not raise `FILE_CAPS` / Cap column (395 ≤ 418). Cap raise deferred until
  growth actually approaches the ceiling with intentional justification.

## Code Quality Issues

- `pypost/core/http_client.py` Baseline LOC is now **395 / 418** (~23 lines /
  ~5.5% headroom). Further legitimate growth will need extraction or a
  justified cap raise before another snapshot refresh alone can absorb drift.
- No runtime Python was edited in this task; quality of the generator /
  equality gate stack is unchanged.

## Missing Tests

- None for this scope. Existing coverage is sufficient:
  - `make check-baseline-metrics` (cap enforcement)
  - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
    (exact snapshot equality)
- No new tests were added; none were required by DoD.

## Performance Concerns

None. Markdown snapshot regeneration has no runtime performance impact.

## Follow-up Tasks

### From this implementation

| Item | Priority / class | Notes |
| ---- | ---------------- | ----- |
| Prefer extract/split of `http_client.py` before raising Cap 418 | Medium / NON-BLOCKER | Headroom ~23 LOC after this refresh; no ticket filed here (scope was snapshot-only) |

### Pre-existing / flaky suite failures (NON-BLOCKER)

Base commit: `369b96a50d024a4a0302f53c32f933adf67f3507`.
Working-tree change for this task: regenerate
`ai-tasks/PYPOST-376/baseline-metrics.md` only.

| Test id / cluster | Verdict | Jira |
| --- | --- | --- |
| `tests/test_http_client.py` (blank path / TEMPLATE cluster) | NON-BLOCKER — pre-existing (fails at base) | [PYPOST-1534](https://pypost.atlassian.net/browse/PYPOST-1534) |
| `tests/test_mcp_server_impl.py` (RequestData `assertIs` / defaults) | NON-BLOCKER — pre-existing (fails at base) | [PYPOST-1535](https://pypost.atlassian.net/browse/PYPOST-1535) |
| `tests/test_bundled_examples_packaging.py::test_explicit_packages_cover_application_tree_and_examples` | NON-BLOCKER — pre-existing | [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) |
| `tests/test_makefile_install_seed_contract.py::test_committed_seed_covers_independent_source_inventory` | NON-BLOCKER — pre-existing | [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) |
| `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift` | NON-BLOCKER — pre-existing (`check-lock-dev` stale; PYPI drift) | [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397) |
| `tests/test_pypost_1077_verification_gates.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` | NON-BLOCKER — pre-existing | [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475) |
| `tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery` | NON-BLOCKER — pre-existing | [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475) |
| `tests/test_mcp_stdio_harness.py::test_harness_stderr_collection` | NON-BLOCKER — flaky (failed full suite; passed re-run / base) | [PYPOST-1493](https://pypost.atlassian.net/browse/PYPOST-1493) |
| `tests/test_mcp_process_reconfigure_repro.py::test_process_reconfigure_rejects_candidate_and_restores_service[before-bind-same-endpoint]` | NON-BLOCKER — flaky (EADDRINUSE under parallel; passed re-run / base) | [PYPOST-1552](https://pypost.atlassian.net/browse/PYPOST-1552) |

None of the above are caused by the SOLID snapshot regeneration.

No blockers relative to PYPOST-1492 acceptance criteria.

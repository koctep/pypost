# Roadmap: PYPOST-1356

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `10-requirements.md`: offline upgrade/copy scenario, complete user guidance,
    explicit existing-server/copy exclusion, and baseline-relative Make verification.
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `20-architecture.md`: real UI/persistence/registry/tool-list workflow with a fake
    transport boundary, bounded cleanup, documentation coverage, and Step3 N/A rationale.
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A - no behavioral change. This task adds one offline acceptance scenario
    and documentation for the already delivered Built-in/paired-copy/collection-copy
    behavior. The independently accepted architecture found no concrete runtime defect:
    existing registry start resolves shipped contents afresh and workspace configurations
    use canonical lookup. No production fix is planned.
  - [x] Step4 will add `tests/test_mcp_builtin_upgrade_e2e.py` and may be immediately
    green. No API deletion, invalid-input setup, skipped assertion, or artificial red
    expectation is needed. If it reveals an actual runtime gap, record exact evidence
    and reassess scope/workflow rather than silently changing production or calling it baseline.
  - [x] No production or test changes in Step3; independent N/A acceptance review PASS.
- [x] **STEP 4: Development**
  - [x] Iteration 1: one connected offline acceptance scenario using real editors,
    canonical persistence, settings controller, registry resolution and MCP tool schemas.
    Only the socket/thread transport is replaced. Initial focused run corrected lowercase
    normalized tool-name expectations; second run passed (no runtime changes needed).
  - [x] Iteration 2: user feature guide plus inbound/outbound guide links; shipped updates,
    both copies, Save/Cancel boundaries and explicit existing-server/copy exclusions.
  - [x] Four focused modules passed: new upgrade scenario, 18 paired-environment cases,
    16 collection-copy cases and registry regressions; `/tmp/pypost1356-step4-focused.log`.
  - [x] `make lint typecheck check-baseline-metrics verify-ai-tasks` passed;
    `/tmp/pypost1356-step4-quality.log`. Explicit test-file flake8 through a temporary
    Make target passed; default lint includes user Markdown/link validation.
  - [x] Final acceptance rerun passed with actual Save buttons, copied request-content
    comparison, and successful bounded teardown; `/tmp/pypost1356-step4-final-repro.log`.
    Explicit test-file lint passed; `/tmp/pypost1356-step4-final-test-lint.log`.
  - [x] `make lint-docs check-docs-links verify-ai-tasks` passed;
    `/tmp/pypost1356-step4-docs.log`.
  - [x] Full `make check` completed: 391 files, 378 passed, 6 failed, 7 skipped,
    310.13 seconds; `/tmp/pypost1356-step4-check.log`. New acceptance and related
    regressions passed. Exact baseline classification is recorded below.
  - [x] No runtime edits or acceptance gaps; Step4 independent review PASS.
- [x] **STEP 5: Code Cleanup**
  - [x] `40-code-cleanup.md`: removed one unused test-only snapshot assignment;
    reviewed test/user-guide formatting without runtime changes.
  - [x] `make lint typecheck`, explicit test-file lint, and focused acceptance rerun
    passed; `/tmp/pypost1356-step5-quality.log`, `-test-lint.log`, and `-test.log`.
    Prior full-suite baseline classification is preserved; no broad rerun needed.
- [x] **STEP 6: Observability**
  - [x] `50-observability.md`: test/docs-only applicability, existing structured copy,
    registry, activity and bounded teardown diagnostics; safe copy-helper fields reviewed.
  - [x] No runtime/log/metric/test edits or new error path; prior focused behavior and
    privacy-contract validation reused.
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `60-tech-debt.md`: accepted offline transport/installer coverage limits, no
    task-created acceptance gap, and all six exact baseline failures linked to
    PYPOST-1361/1299/1363. Previously filed 1298/1362 distinguished as not observed.
- [x] **STEP 8: Dev Docs**
  - [x] Extended `doc/dev/predefined_collection_library.md` with exact offline test
    command, real/fake boundaries, stable-path upgrade and detached-copy behavior,
    configuration/cleanup limits, troubleshooting, source pointers and user-guide link.
  - [x] Explicit developer-guide Markdown/link checks through a temporary Make target
    passed; `/tmp/pypost1356-step8-guide.log`. Default `make lint-docs check-docs-links
    verify-ai-tasks` also passed; `/tmp/pypost1356-step8-docs.log`. No runtime/test changes.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` - step not started
- `[/]` - step in progress
- `[x]` - step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1356/10-requirements.md`
- Requested documentation targets: `doc/user/mcp-client.md` or a linked feature page;
  developer pointers to bundle discovery and curated view in `bundled_resources.py` and
  `builtin_collections.py`. No documentation outside task artifacts changes in Step 1.

### STEP 2: Architecture

- `ai-tasks/PYPOST-1356/20-architecture.md`

### STEP 3: Failing Repro

- N/A - no behavioral change; reviewed-design applicability rationale above and in
  `20-architecture.md`. The connected acceptance scenario is a Step4 artifact.

### STEP 4: Development

- `tests/test_mcp_builtin_upgrade_e2e.py`: one connected offline scenario, explicit
  60-second timeout and bounded waits/teardown. Real editor actions, canonical environment
  and collection persistence, saved settings, registry fresh-load, and MCP tool listing.
  The manager substitutes only socket/thread transport; no network or credentials required.
- `doc/user/builtin-mcp.md`, linked from `mcp-client.md` and `mcp-tools.md`: all requested
  source, copy, update, examples-library, whole-library, and no-migration guidance.
- Focused command: `make test PYTEST_ARGS='tests/test_mcp_builtin_upgrade_e2e.py
  tests/test_mcp_builtin_paired_env.py tests/test_mcp_builtin_collection_copy.py
  tests/test_mcp_server_registry.py -q'` (argument shown wrapped for readability).
- Static/type/cap/artifact command: `make lint typecheck check-baseline-metrics verify-ai-tasks`.
- Full gate command: `make check`.

#### Full-gate baseline failures

| Exact node | Evidence and classification |
| --- | --- |
| `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` | [PYPOST-1361](https://pypost.atlassian.net/browse/PYPOST-1361): recorded dialog LOC 1031 versus discovered 1219. |
| `tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery` | PYPOST-1361: same 1031 versus 1219 stale dialog snapshot. |
| `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics` | PYPOST-1361: stored SOLID LOC snapshot differs; cap checks pass. |
| `tests/test_pytest_exit_policy.py::test_make_test_fails_closed_when_parallel_runner_is_missing` | [PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299): nested make install timed out after 60 seconds. |
| `tests/test_makefile_exit_behavior.py::TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test` | [PYPOST-1363](https://pypost.atlassian.net/browse/PYPOST-1363): baseline fixture/environment failure; flake8 reporter raises KeyError 'default'. |
| `tests/test_makefile_target_filtering.py::TestTargetFiltering::test_lint_succeeds_after_install` | Same baseline flake8 reporter failure; distinct from the filed flock timeout. |

The two reporter failures reproduced in the unchanged narrow retry (2 failed modules,
22.11 seconds), `/tmp/pypost1356-step4-fixture-retry.log`, with this exact command:

```sh
make test PYTEST_ARGS='tests/test_makefile_exit_behavior.py::TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test tests/test_makefile_target_filtering.py::TestTargetFiltering::test_lint_succeeds_after_install -q'
```

Baseline equivalence is established by an empty diff against the task base for the complete
fixture build inputs: `Makefile`, `pyproject.toml`, `scripts/run_parallel_tests.py`,
`tests/makefile_test_helpers.py`, and both failing test modules. The fixture copies only
Makefile/parallel runner, generates its minimal project, and hardlinks a prewarmed venv.
Neither the new acceptance test nor user documentation is included in that isolated seed.
The observed flake8 version is 7.4.1. Stale/corrupt prewarmed metadata is a hypothesis,
not an established cause. Follow-up [PYPOST-1363](https://pypost.atlassian.net/browse/PYPOST-1363) is estimated at 5 SP and verified in Jira; no unrelated fix
or new baseline installation was attempted. Existing PYPOST-1298/1362 did not produce
additional failures in this run. No broad gate repeat is needed.

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1356/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1356/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1356/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.

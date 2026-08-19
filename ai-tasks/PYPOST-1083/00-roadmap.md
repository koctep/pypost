# Roadmap: PYPOST-1083

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `refactoring/PYPOST-1083-mcp-dialog-open-count`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1083/00-roadmap.md`
  - `ai-tasks/PYPOST-1083/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1083/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [ ] Red test: `tests/test_mcp_controls_presenter.py::test_open_mcp_servers_with_controller_logs_info_and_constructs_dialog`
    (extended in place per `20-architecture.md`) — added `controller.mcp_server_count.return_value = 2`,
    `controller.mcp_server_count.assert_called_once()`, and
    `controller.mcp_server_configurations.assert_not_called()`. Fails today with
    `AttributeError: Mock object has no attribute 'mcp_server_count'` at line 98
    (`MagicMock(spec=McpServerController)` rejects the attribute because the Protocol has no
    `mcp_server_count` member yet). All other tests in the file still pass (5 passed, 1 failed).
- [x] **STEP 4: Development**
  - [x] Added `mcp_server_count() -> int` to the `McpServerController` Protocol
    (`pypost/ui/presenters/mcp_controls_presenter.py`), implemented on
    `McpServerSettingsController` as `len(self._settings.mcp_servers)`
    (`pypost/ui/mcp_server_controller.py`), and switched the `_open_mcp_servers` log call
    site to use it instead of `len(controller.mcp_server_configurations())`.
  - [x] `PYTEST_ARGS="tests/test_mcp_controls_presenter.py -v" make test` green (6 passed);
    `make lint` clean.
  - [x] Full suite (`make test`): 2320 passed, 7 failed, 22 deselected — all 7 pre-existing,
    triaged per `_shared/failing-tests-triage.md` against base commit `2b770ada` (throwaway
    baseline worktree, full-suite comparison). None caused by this task.
    - 6 node ids fail identically at baseline and HEAD (`test_cli_re_encrypt_dry_run`,
      `test_cli_re_encrypt_dry_run_json_includes_reencrypt_stats`,
      `test_cli_re_encrypt_reports_reencrypt_stats`,
      `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`,
      `test_markdown_snapshot_matches_current_metrics`,
      `test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`).
    - 2 node ids (`test_bulk_re_encrypt_does_not_skip_with_plaintext_hidden` /
      `test_bulk_re_encrypt_dry_run_projects_active_kid`) are flaky/order-dependent within
      `test_encryption_migration.py` (confirmed via isolated re-run at HEAD: different node id
      fails each time, mtime-resolution race and kid-hash randomness).
    - Jira: 3 new node ids added as a comment on
      [PYPOST-1088](https://pypost.atlassian.net/browse/PYPOST-1088) (already tracked the
      other 2 encryption-flakiness node ids); 2 new Debt issues filed —
      [PYPOST-1110](https://pypost.atlassian.net/browse/PYPOST-1110) (qapp alignment, 1 SP)
      and [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) (audit/baseline
      snapshot drift, 3 SP). Recorded as NON-BLOCKER — pre-existing.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1083/40-code-cleanup.md` — `flake8`/`make lint` clean, targeted pytest
    (6 passed), mypy baseline drift confirmed pre-existing (unaffected by this task's files
    via stash comparison). No code edits needed; diff already clean.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1083/50-observability.md` — verified the existing
    `mcp_servers_dialog_opened server_count=%d` INFO log (`mcp_controls_presenter.py`
    `_open_mcp_servers`) is unchanged in level/message/semantics; only its count source
    changed to the cheaper `mcp_server_count()` accessor (no internal logging, per Step 4).
    `PYTEST_ARGS="tests/test_mcp_controls_presenter.py -v" make test`: 6 passed. No new
    metric warranted; none added.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1083/60-tech-debt.md` — no new debt from this task's own change (clean
    one-line accessor + Protocol member + one call-site swap); one low-risk "Missing Tests" note
    (no dedicated controller-level unit test for `mcp_server_count()`, unlike its sibling
    `mcp_server_configurations()`) — not filed as a Jira issue, opportunistic follow-up only.
    Pre-existing Step 4 test failures transcribed under Follow-up Tasks with their existing Jira
    links (PYPOST-1088, PYPOST-1110, PYPOST-1111), all NON-BLOCKER — pre-existing. Targeted
    tests re-verified green (18 passed: `tests/test_mcp_controls_presenter.py` +
    `tests/test_mcp_server_controller.py`).
- [x] **STEP 8: Dev Docs**
  - Searched `doc/dev/` for references to the `McpServerController` Protocol,
    `mcp_server_configurations()`, and the MCP servers dialog-open flow. Found the Protocol
    surface enumerated in `doc/dev/mcp_integration.md` (§4 `McpServerSettingsController`);
    updated its bullet list to add `mcp_server_count` and note it returns
    `len(self._settings.mcp_servers)` without the deep copy that
    `mcp_server_configurations` does, and that `_open_mcp_servers`'s
    `mcp_servers_dialog_opened` log now uses it. `doc/dev/presenter_architecture.md`
    (method-stub listing, no Protocol member enumeration) and `doc/dev/testing.md`
    (describes the log event and test coverage generically, not the count's data source)
    were checked and needed no change — neither described the deep-copy-vs-`len()`
    implementation detail that changed. `doc/dev/logging.md`'s `mcp_servers_dialog_opened`
    entry is unaffected (message/level/field unchanged, per Step 6).
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1083/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1083/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1083/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1083/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1083/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)

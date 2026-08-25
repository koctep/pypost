# PYPOST-1156: Observability Implementation

## Scope Note

PYPOST-1156 is a research and decomposition story. No `pypost/` production code, daemon process,
or service was added or changed — Steps 3 and 4 were **N/A** (no behavior to test, no code to
write). There is therefore nothing that executes in production **for this task**, so PYPOST-1156
itself has no logs and no metrics to add.

The epic it decomposes ([PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)) does
carry observability obligations identified during research. Those are confirmed below as
cross-references to the child implementation stories — not new decisions invented for this step.

## Logging Implementation

### Added Logs

None added by PYPOST-1156 — no code exists for this task to log from.

Existing WebSocket lifecycle logging from Epic PYPOST-1123 (WS-10, `doc/dev/logging.md`,
`doc/dev/websocket_settings_session_ceiling_and_metrics.md`) is unchanged by this research task.
Blank-tab creation paths do not introduce new log events in the research scope; any future
logging for draft-tab lifecycle (e.g., first connect from an unsaved profile) would be owned by
the implementation stories that add the behavior.

### Log Structure

Not applicable to PYPOST-1156's own changes (no code, no log calls).

## Metrics Implementation (if applicable)

Not applicable to PYPOST-1156 itself — no code, no metrics registry entries added by this task.

### Research finding — new-tab protocol attribution (NFR-5 / FR-1.1)

[`20-architecture.md`](20-architecture.md) section **R-3 Metrics extension** documents that
`track_gui_new_tab_action(source)` today records only the creation source (`plus_button`,
`shortcut`, `collections_context`, `unknown`). Functional requirements FR-1.1 and NFR-5 require
protocol attribution when users choose HTTP vs WebSocket at blank-tab creation.

**Deferred to [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) (WS-TM-1):**

- Extend `track_gui_new_tab_action` (or add a sibling counter) with a `protocol` label
  (`http` | `websocket`).
- Wire the label from `TabsPresenter.open_blank_tab(protocol, source)` after the protocol picker
  resolves.
- Add tests in `tests/test_metrics_manager.py` (proposed red test in WS-TM-1 Step 3).

No other new metrics were identified for the blank-tab WebSocket mode beyond this extension.
Existing WebSocket session metrics (connect duration, message counts, probe outcomes) from WS-10
remain sufficient for draft and saved profile tabs once the editor path exists.

### Performance Metrics

None added by this task. Draft WebSocket tabs consume session slots like saved profiles
(`ws_max_concurrent_sessions`); no separate metric is required at research time.

### Business Metrics

Designed, not yet built — owned by **WS-TM-1 (PYPOST-1157)**:

- **New tab by source and protocol**: extend GUI new-tab counter with `protocol` dimension (see
  above).

### System Health Metrics

None added by this task.

## Monitoring Integration

- [ ] Prometheus metrics for new-tab protocol label — deferred to PYPOST-1157 (WS-TM-1)
- [ ] Existing WebSocket metrics unchanged (WS-10 / PYPOST-1136)

## Validation Results

- [x] Confirmed no production code changed in PYPOST-1156
- [x] Metrics extension requirement documented in `20-architecture.md` R-3
- [x] Owning story identified: PYPOST-1157 (WS-TM-1) with proposed test location
- [x] No logging or metrics obligation silently dropped — deferred items named explicitly

## Notes

- STEP 6 is left at `[/]` in `00-roadmap.md` — per `td-roadmap`, the executing agent does not
  mark its own step `[x]`; that is the acceptance-gate owner's action after review passes.
- Full observability implementation for blank-tab flows (if any beyond the new-tab counter) will
  be validated when child stories PYPOST-1157 … PYPOST-1163 run their own Step 6 cycles.

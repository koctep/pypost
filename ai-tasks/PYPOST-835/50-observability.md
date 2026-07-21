# PYPOST-835: Observability Implementation

## Logging Implementation

### Added Logs

Snapshot capture is an on-demand agent/harness API. Full trees must never be
logged (size + secret risk). Primary proof remains the CI/test gate; one DEBUG
summary gives operators duration/size without dumping values.

- **EMERG / ALERT / CRIT / ERR / WARNING / NOTICE / INFO**: none added —
  snapshot is not a lifecycle control path (launch/ready/shutdown stay in
  PYPOST-833). INFO would be noisy if agents poll after every action.
- **DEBUG**:
  - `pypost.agent.ui_snapshot` — `ui_snapshot_captured` after a successful
    capture (`node_count`, `named_count`, `duration_ms`). Scalars only; never
    the tree, node values, `env_vars`, or `hidden_keys`.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value` per `doc/dev/logging.md`)
- Includes context: yes (node counts and duration only)
- Log levels: DEBUG

Diagnostics for snapshot correctness:

- Automated: `tests/test_ui_snapshot.py` — shape/hierarchy, masking of hidden
  values, truncation, and ready integration via `AgentAppSession`
- Manual: call `capture_ui_snapshot` / `AgentAppSession.ui_snapshot()` after
  `is_ui_ready` and inspect the returned dict (not logs)

## Metrics Implementation (if applicable)

### Performance Metrics

No Prometheus / OTel instruments. Capture duration is logged as `duration_ms`
on the DEBUG event above. Agent sessions bind an ephemeral metrics port
(PYPOST-833), so scrapeable counters would not outlive the session.

### Business Metrics

None. Snapshot is a harness/verification contract, not a user-product action.

### System Health Metrics

None new.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — not applicable for ephemeral agent sessions
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] CI / test gate — `tests/test_ui_snapshot.py` under `make test` (offscreen)
- [x] Log aggregation — DEBUG event follows `event_name key=value` convention
  (`doc/dev/logging.md`); catalog entry deferred to Step 7

## Validation Results

Validation results:
- [x] Logs use `%` formatting and snake_case event names
- [x] Large data structures are not logged (no tree / values / env dumps)
- [x] Secrets never appear in logs (sanitizer applies to returned values only;
  log fields are integers)
- [x] Masking covered by unit tests (`HIDDEN_PLACEHOLDER` / hidden keys)
- [x] Existing lifecycle logs (`agent_session_*`, `main_window_ui_ready`)
  unchanged
- [ ] Metrics collection — N/A

## Notes

- Intentional minimalism relative to dumping snapshots: like PYPOST-834, avoid
  per-call INFO spam; unlike 834, one DEBUG summary is useful because capture
  cost and tree size vary with UI state.
- Exceptions during capture propagate to the caller without a dedicated
  `_failed` event (same as other pure agent API helpers).
- Catalog `ui_snapshot_captured` in `doc/dev/logging.md` in Step 7 (Dev Docs),
  consistent with PYPOST-833.
- Sibling action/settle stories may add outcome logs on *their* paths; do not
  log snapshot payloads there either.

# PYPOST-920: Observability Implementation

## Verdict

**No new production logs or metrics required.** This story adds stable widget
identities (`RESPONSE_STATUS` / `RESPONSE_BODY`) to the catalog and applies
them via `set_widget_id` in `ResponseView.init_ui`. Identity apply is silent,
matching existing `RESPONSE_PANEL` stamping. No new agent primitives or
request paths were introduced.

## Logging Implementation

### Added Logs

None. Widget identity is applied once at construction; it is not an
operational control path that needs INFO-level events.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A — per-widget id assignment would be noisy on every create
- **DEBUG**: N/A — prefer spot-check / wait-timeout failures over spam

### Why no new logs

| Change | Observability impact |
| --- | --- |
| `RESPONSE_STATUS` / `RESPONSE_BODY` in `widget_ids.py` | Catalog constants only |
| `set_widget_id` on `status_label` / `body_view` in `init_ui` | Identity only; same silent pattern as `RESPONSE_PANEL` in `__init__` |
| Golden settle via `wait_for_text` | Reuses existing wait observability (below) |
| Spot-check assertions | CI failure is the regression signal |

Do **not** log response body or status display text on id apply. Large
payloads must stay out of logs per project convention.

### Existing harness logging (reused, unchanged)

Golden / agent paths that call `wait_for_text` on the new ids already emit
DEBUG events from `pypost.agent.ui_wait` (documented in
[logging.md](../../doc/dev/logging.md)):

| Event | Level | Key fields | When |
| --- | --- | --- | --- |
| `ui_wait_settled` | DEBUG | `condition`, `waited_ms`, `timeout_s` | Text matched within timeout |
| `ui_wait_timeout` | DEBUG | `condition`, `waited_ms`, `timeout_s` | Wait exhausted; raises `UiWaitTimeoutError` with scalar diagnostics (`widget_id`, `found`, clipped `expected` / `actual_text`) |

No changes to `ui_wait.py` were required for this story.

### Log Structure

Log format used:
- Structured logs: N/A for new statements (none added)
- Includes context: N/A
- Log levels: unchanged; existing wait events use `key=value` DEBUG style

Diagnostics for missing identities:

- Automated: `tests/test_ui_identity_spotcheck.py` fails if
  `RESPONSE_STATUS` / `RESPONSE_BODY` are absent after UI ready
- Harness: `wait_for_text` timeout / `found=False` when ids are missing
- Manual: `findChild` / `objectName` using constants from
  `pypost.ui.widget_ids`

## Metrics Implementation (if applicable)

### Performance Metrics

None. Setting `objectName` / `accessibleIdentifier` is O(1) at construction.
No response-time or throughput series for identity apply.

### Business Metrics

None. Identity is a harness / agent contract, not a user-product action.

### System Health Metrics

None new.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — not applicable
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [ ] Log aggregation (ELK, Loki, etc.) — not applicable
- [x] CI / test gate — identity spot-check + golden e2e under `make test`

## Validation Results

Validation results:
- [x] No new production log statements introduced
- [x] Large / sensitive structures are not logged (N/A — no new logs; waits
  clip expected/actual text in timeout diagnostics only)
- [x] Spot-check proves status/body identities after ready
- [x] Golden settle uses existing `ui_wait_settled` / `ui_wait_timeout`
- [ ] Metrics collected — N/A (none added)
- [x] Existing lifecycle logs (`main_window_ui_ready`, `agent_session_*`)
  unchanged and still the right place to confirm UI readiness before lookup

## Notes

- Agents should wait for UI ready before resolving ids (same as other key
  widget ids).
- Lookup-failure telemetry belongs in the wait/action layer (already present
  via `ui_wait_*` and `UiWaitTimeoutError`), not on every `set_widget_id`.
- Optional future DEBUG catalog event (e.g. `ui_widget_id_applied`) remains
  deferred non-blocking debt from the identity program (PYPOST-834); this
  story does not introduce it.
- Developer-doc catalog updates are Step 8 (FR7), not runtime observability.
- Observability ready for production: **yes** — no production monitoring gap
  for silent identity apply; harness waits retain existing DEBUG coverage.

# PYPOST-975: Observability Implementation

## Scope

Path A tests-only hardening — live agent e2e negative select proofs for the
product `COLLECTION_TREE`. Production `_select_tree` / `session.ui_select` are
unchanged. NFR-4 and AC-5 require no new log or metric behaviour; this step
documents existing coverage as sufficient.

## Observability Requirements Analysis

| Component | Monitoring need | Outcome |
| --- | --- | --- |
| Live missing-label select | Actionable CI / author failure | Existing exception |
| Live top-level OOR select | Actionable CI / author failure | Existing exception |
| Successful `ui_select` | Duration / outcome scalars | Existing DEBUG (not hit) |
| Perf / business metrics | N/A for negative proofs | None required |

Critical path under test: `seeded_agent_e2e_session` → `session.ui_select` →
`ui_select` → `_select_tree` → raise before success DEBUG log.

## Logging Implementation

### Added Logs

No new log statements — production logging unchanged.

Existing production observability for the paths under test:

- **ERR** (via exception): `UiTargetNotInteractableError` with actionable
  `reason` (`option not found: …` / `option index out of range: …`) and
  `widget_id` — raised by `_select_tree` in `pypost/agent/ui_actions.py` when
  select fails. Live proofs assert the same substrings as PYPOST-942 fixture
  tree negatives.
- **DEBUG** (success path only): `ui_action_applied primitive=select
  widget_id=… outcome=ok duration_ms=…` after a successful select. Negative
  proofs never reach this line; no option text or model payload is logged.

| Level | Location | Status for this task |
| --- | --- | --- |
| **EMERG** | — | N/A |
| **ALERT** | — | N/A |
| **CRIT** | — | N/A |
| **ERR** | `_select_tree` via `UiTargetNotInteractableError` | Existing; covered by live proofs |
| **WARNING** | — | N/A |
| **NOTICE** | — | N/A |
| **INFO** | — | N/A |
| **DEBUG** | `ui_select` success `ui_action_applied` | Existing; not hit by negatives |

### Log Structure

- Structured logs: yes for success DEBUG (`primitive`, `widget_id`, `outcome`,
  `duration_ms` key=value scalars only)
- Includes context: exceptions include `widget_id` and `reason`; no large
  tree/model dumps
- Log levels: none added (existing DEBUG + exception ERR contract)

## Metrics Implementation (if applicable)

Not applicable — tests-only task; no metrics changes (NFR-4).

### Performance Metrics

N/A — no new response-time, throughput, or error-rate metrics. Existing
`duration_ms` on successful select remains as before.

### Business Metrics

N/A

### System Health Metrics

N/A

## Monitoring Integration

- [ ] Prometheus metrics — N/A
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.) — N/A

## Validation Results

- [x] No new logs required — existing error contract covered by Step 4 live
  proofs (`test_live_collection_tree_missing_option_raises`,
  `test_live_collection_tree_index_out_of_range_raises`)
- [x] Metrics N/A
- [x] Logging / failure messaging works in error scenarios — pytest asserts
  `option not found` / `option index out of range` on live tree
- [x] Large data structures are not logged — unchanged (scalars / exception
  reason only)
- [x] Production observability documented as unchanged and sufficient

## Notes

- Diagnostic surface for harness authors is the raised
  `UiTargetNotInteractableError` string (fixture-parity substrings), not a new
  log line — same stance as PYPOST-942 / PYPOST-974.
- Success-path DEBUG `ui_action_applied` remains the observability for ok
  selects; covered historically by `test_ui_action_applied_caplog` for fill;
  select contract unchanged from prior agent UI work.
- No DEBUG teardown or option-label logging added to live proofs.
- Follow-ups, if any, belong in `60-tech-debt.md` (Step 7).

# PYPOST-857: Observability Implementation

## Logging Implementation

### Added Logs

Seed write is a short fixture helper. Logs use scalars only (paths, ids,
counts) — never request bodies, variable maps, or full model dumps. Seed has
no secrets by design; still omit `base_url` values and POST body from logs.

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR** (via `logger.exception`):
  - `pypost.fixtures.agent_e2e_seed` — `agent_e2e_seed_failed` when
    `StorageManager` persist raises (`data_dir`); exception context included;
    error is re-raised for the caller
- **WARNING**: none (storage may emit its own load/save warnings independently)
- **NOTICE**: none (stdlib logging has no NOTICE; significant events use INFO)
- **INFO**:
  - `pypost.fixtures.agent_e2e_seed` — `agent_e2e_seed_completed` after
    successful persist (`data_dir`, `collection_id`, `collections`,
    `requests`, `env_id`, `envs`)
- **DEBUG**: none — builders are pure; completion INFO is enough for harness
  grepping

Renamed Step 3 event `agent_e2e_seed_written` → `agent_e2e_seed_completed`
to match outcome suffixes in `doc/dev/logging.md`.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value` per `doc/dev/logging.md`)
- Includes context: yes (`data_dir`, inventory ids and counts)
- Log levels: INFO, ERROR (via `logger.exception`)

## Metrics Implementation (if applicable)

### Performance Metrics

None. Seed write is a few small JSON files; architecture explicitly skips
Prometheus / OTel instruments for this story.

### Business Metrics

None. Fixture inventory size is fixed and logged as INFO scalars, not
scrapeable counters.

### System Health Metrics

None new. Persistence failures surface via `agent_e2e_seed_failed` and
existing `StorageManager` error events.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — not applicable for test/agent seed helpers
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] Log aggregation — events follow project `event_name key=value`
  convention for grep/CI allowlists (`doc/dev/logging.md`)
- [x] CI / test gate — `tests/test_agent_e2e_seed.py` under
  `make test-agent-e2e`

## Validation Results

Validation results:
- [x] Logs use `%` formatting and snake_case event names
- [x] Failure path logs ERROR then re-raises
- [x] Large data structures are not logged (no bodies, vars, or models)
- [x] Success path emits `agent_e2e_seed_completed` with inventory counts
- [x] Unit persist test still passes after event rename
- [x] Catalog entry in `doc/dev/logging.md` — Step 7 (Dev Docs)

## Notes

- Downstream `StorageManager` may also emit
  `save_environments_completed` on the same write; seed events are the
  fixture-level boundary for agent e2e authors.
- Test helper `tests/helpers/agent_e2e_seed.py` does not log; it only wraps
  temp dirs + `write_agent_e2e_seed`.
- Assertion messages in product-facing tests remain the primary diagnostic
  for missing inventory after ready (architecture Step 5 note).

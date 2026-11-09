# PYPOST-1388: Observability Implementation

## Logging Implementation

### Added Logs

Hierarchical selector evaluation moved from linear `_path_selectors` scans to an
in-module `PathSelectorTrie` with mutable path breadcrumbs. Observability stays at
the compile-once / tree-completion boundaries only — never on the per-key hot path —
so high-frequency GUI formatting and MCP redaction do not emit log noise or leak
payload values.

- **EMERG**: N/A — in-memory trie match and breadcrumb walk cannot take down the host.
- **ALERT**: N/A — no operator-urgent failure mode in selector evaluation.
- **CRIT**: N/A — no unrecoverable engine state; empty / miss paths short-circuit.
- **ERR**: N/A — non-container roots and empty engines return without raising.
- **WARNING**: N/A — misses and empty catalogs are expected steady-state outcomes.
- **NOTICE**: N/A — significant lifecycle events remain DEBUG for this hot path.
- **INFO**: N/A — compile and redact events stay DEBUG to avoid production volume.
- **DEBUG**:
  - `pypost/core/json_selector_engine.py` (`JsonSelectorEngine._compile`):
    `json_selector_engine_compiled raw_count=%d bare_keys_count=%d
    path_selectors_count=%d trie_size=%d` — emitted once after partitioning bare
    keys and inserting hierarchical token sequences into `PathSelectorTrie`.
    `trie_size` is the count of distinct terminal paths indexed (architecture
    compile-once boundary). Counts only; raw selector strings and values omitted.
  - `pypost/core/json_selector_engine.py` (`JsonSelectorEngine.redact_tree`):
    `json_selector_engine_redact_tree_completed masked_count=%d` — emitted after
    breadcrumb stack traversal finishes; logs masked node count only.
  - Retained consumer diagnostics (unchanged this ticket; documented in
    PYPOST-1394 / PYPOST-1378): sanitizer skip/complete events and GUI span /
    click-to-reveal DEBUG lines continue to cover MCP and desktop surfaces.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value ...`)
- Includes context: yes (`raw_count`, `bare_keys_count`, `path_selectors_count`,
  `trie_size`, `masked_count`)
- Log levels: DEBUG

### Zero Sensitive Data Leakage Guarantees

1. **No secret values** — never format masked field contents into log strings.
2. **No selector dumps** — compile logs emit integer catalog sizes only.
3. **No body dumps** — redact completion logs `masked_count` only.
4. **No per-match logging** — trie walks and breadcrumb push/pop stay silent on
   the hot path (architecture: high-frequency GUI + MCP consumers).
5. **Automated check** — `test_json_selector_engine_observability_and_zero_leak`
   in `tests/test_pypost_1394_failing_repro.py` asserts compile/`trie_size`,
   redact completion, and absence of fixture secrets in log records.

## Metrics Implementation (if applicable)

### Performance Metrics

- **Compile-once sizing**: `trie_size` / `path_selectors_count` / `bare_keys_count`
  diagnose catalog shape after `_compile` without timing probes in production.
- **Redaction volume**: `masked_count` from `redact_tree` completion.
- **Hot-path cost**: not instrumented with timers or counters in production logs;
  efficiency is guarded by Step 3 repro tests (depth-bounded trie walk, single
  breadcrumb list identity). Optional private match-probe seams remain test-only
  per architecture.

### Business Metrics

- **Masked Field Count**: `masked_count` / consumer `masked_fields_count` (MCP /
  GUI surfaces unchanged).
- No new Prometheus series required for this internal algorithm change; existing
  `hidden_value_masks_applied_total{surface=...}` continues to cover masking.

### System Health Metrics

- **Component status**: trie emptiness short-circuits via `PathSelectorTrie.is_empty`
  / `JsonSelectorEngine.is_empty`; reflected indirectly when compile logs show
  `trie_size=0` with only bare keys or an empty catalog.
- **Resource usage**: no new gauges; stack breadcrumbs avoid per-level path list
  allocation (validated in tests, not logged).

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (no new series; reuse existing masking surface counters)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [x] Log aggregation (structured `event_name key=value` ingestible by ELK / Loki)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (`json_selector_engine_compiled` includes
  `trie_size`; redact completion unchanged)
- [x] Metrics / counts collected correctly (`PathSelectorTrie.size` exposed for
  compile diagnostics)
- [x] Logging works for empty and non-empty catalogs without raising
- [x] Large data structures are not logged (counts only)
- [x] Zero sensitive data leak covered by existing observability unit test
  (extended for `trie_size=1`)
- [x] No per-key / per-match DEBUG on trie walk or breadcrumb push/pop

## Notes

- Architecture mandates compile-once trie indexing and stack breadcrumbs for
  FR-2/FR-3; light DEBUG belongs at compile and redact completion only.
- `PathSelectorTrie.size` is a read-only diagnostic property for logs/tests; it
  is not part of the public MCP/GUI engine contract beyond structured DEBUG.
- STEP 6 remains `[/]` in `ai-tasks/PYPOST-1388/00-roadmap.md` until the
  acceptance gate owner marks `[x]`.

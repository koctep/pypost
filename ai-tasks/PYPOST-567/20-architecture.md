# PYPOST-567: Architecture

## Approach

Parse a captured pytest live-log file (`tests.txt`) produced by `make test` with
`log_cli = true` in `pytest.ini`. No runtime hooks or pytest plugins — offline analysis only.

## Components

| Component | Role |
| --- | --- |
| `tests.txt` | Baseline capture (937 passed, 72 ERROR, 138 WARNING lines) |
| `scripts/parse_test_log_inventory.py` | Parser: extract level, logger, message, adjacent test |
| `ai-tasks/PYPOST-567/inventory.md` | Human-readable summary grouped by logger |
| `ai-tasks/PYPOST-567/inventory.csv` | Flat export for spreadsheet review |

## Parsing rules

1. Track `current_test` from pytest node id lines (`tests/...::...`).
2. Match live-log lines: `HH:MM:SS LEVEL logger: message`.
3. Group by logger; sub-group by message prefix; tag expected/suspicious/unknown.
4. Reconcile counts with baseline grep totals.

## Outputs for downstream tasks

- PYPOST-568: ERROR groups for `worker`, `tabs_presenter`, `collection_tree_actions`
- PYPOST-570: quantified noise attributable to `log_cli_level = WARNING`
- PYPOST-571: allowlist candidates from **expected**-tagged groups

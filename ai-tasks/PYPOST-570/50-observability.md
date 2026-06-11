# PYPOST-570: Observability

Documents how `pytest.ini` live logging affects observability of test runs.

| Surface | With `log_cli_level=WARNING` | After recommended CI change |
| --- | --- | --- |
| Local `make test` | 210 live lines on green run | Unchanged |
| CI job log | 210 live lines on green run | Quiet; guardrail via PYPOST-571 |
| Inventory tooling | `scripts/parse_test_log_inventory.py` | Still valid on captured `tests.txt` |

No new metrics or application log statements.

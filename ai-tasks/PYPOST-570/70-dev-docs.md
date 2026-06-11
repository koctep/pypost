# PYPOST-570: Dev Docs

Updated `doc/dev/testing.md` with a **Pytest live logging (`log_cli`)** section covering:

- Current `pytest.ini` settings and why they emit noise on green runs.
- PYPOST-567 baseline counts (72 ERROR, 138 WARNING).
- Recommended split: keep local defaults; disable in CI; PYPOST-571 guardrail.
- Link to `ai-tasks/PYPOST-570/log-cli-review.md` for full option analysis.

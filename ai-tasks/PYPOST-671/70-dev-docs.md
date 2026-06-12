# PYPOST-671: Dev Docs

## Existing coverage

`doc/dev/testing.md` already documents pytest live logging in the **Pytest live logging
(`log_cli`)** section (PYPOST-570):

- `pytest.ini` defaults (`log_cli = true`, `log_cli_level = WARNING`).
- Recommendation to disable in CI with `-o log_cli=false`.
- Local quiet override example.

## Optional follow-up

The **CI guardrails** section still describes a single `pytest.log` tee capture. Post-PYPOST-671,
CI uses `--log-file=pytest.log` for the verifier and `pytest-output.txt` for duration audit.
A one-line note there would align docs with the workflow split; not required to close this ticket.

## Pointer

See `doc/dev/testing.md` — Pytest live logging (`log_cli`) and CI guardrails sections.

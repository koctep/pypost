# PYPOST-874: Dev Docs

## Overview

Recorded **ENABLE** for optional CI upload of agent e2e failure artifacts.
On `agent-e2e` job failure, `artifacts/agent_e2e/` is uploaded as Actions
artifact `agent-e2e-failure-artifacts` (`if: failure()`,
`if-no-files-found: ignore`).

## Architecture

- **Dump producer** — PYPOST-860 hook/helper (unchanged).
- **CI consumer** — `actions/upload-artifact` on job `agent-e2e` only.
- **Lock** — `tests/test_agent_e2e_ci_failure_upload_doc.py` guards docs +
  YAML.

## Usage

No new make targets. Run the lock with:

```bash
make test PYTEST_ARGS='tests/test_agent_e2e_ci_failure_upload_doc.py -v'
```

After a red `agent-e2e` CI run: open the Actions run → Artifacts →
`agent-e2e-failure-artifacts`.

## Configuration

| Setting | Value |
| --- | --- |
| Path | `artifacts/agent_e2e/` |
| Artifact name | `agent-e2e-failure-artifacts` |
| Gate | `if: failure()` |
| Missing path | `ignore` |

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Lock fails on missing phrases | Restore ENABLE section in failure-artifacts / agent_e2e / testing docs |
| Lock fails on missing upload step | Restore failure upload under job `agent-e2e` |
| Artifact missing after red job | Fail may predate dumps (`make install`); check job logs |
| Want matrix upload too | See unticketed follow-up in `60-tech-debt.md` |

## Files updated

| File | Change |
| --- | --- |
| `.github/workflows/test.yml` | Failure upload + summary note on `agent-e2e` |
| `doc/dev/agent_e2e_failure_artifacts.md` | ENABLE CI upload section |
| `doc/dev/agent_e2e.md` | CI / config / troubleshooting |
| `doc/dev/testing.md` | § Agent e2e failure artifact CI upload; makefile table |
| `tests/test_agent_e2e_ci_failure_upload_doc.py` | Doc/workflow lock |

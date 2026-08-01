# PYPOST-909: Dev Docs

## Overview

Recorded **ENABLE** for optional CI upload of agent e2e failure artifacts
from the main `test` matrix. On matrix cell failure,
`artifacts/agent_e2e/` is uploaded as Actions artifact
`agent-e2e-failure-artifacts-${{ matrix.python-version }}`
(`if: failure()`, `if-no-files-found: ignore`). Dedicated job
`agent-e2e` upload (PYPOST-874) is unchanged.

## Architecture

- **Dump producer** — PYPOST-860 hook/helper (unchanged).
- **CI consumers** — `actions/upload-artifact` on jobs `agent-e2e` (874)
  and `test` matrix (909).
- **Lock** — `tests/test_agent_e2e_ci_matrix_failure_upload_doc.py`
  guards docs + YAML for the matrix path.

## Usage

No new make targets. Run the lock with:

```bash
make test PYTEST_ARGS='tests/test_agent_e2e_ci_matrix_failure_upload_doc.py -v'
```

After a red main `test` matrix cell: open the Actions run → Artifacts →
`agent-e2e-failure-artifacts-<python-version>`.

## Configuration

| Setting | Value |
| --- | --- |
| Path | `artifacts/agent_e2e/` |
| Artifact name | `agent-e2e-failure-artifacts-${{ matrix.python-version }}` |
| Gate | `if: failure()` |
| Missing path | `ignore` |

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Lock fails on missing phrases | Restore ENABLE section naming PYPOST-909 + matrix |
| Lock fails on missing upload step | Restore failure upload under job `test` |
| Artifact missing after red cell | Fail may predate dumps; check job logs |
| Want only dedicated-job upload | See PYPOST-874; matrix remains ENABLE here |

## Files updated

| File | Change |
| --- | --- |
| `.github/workflows/test.yml` | Failure upload + summary note on `test` |
| `doc/dev/agent_e2e_failure_artifacts.md` | Matrix ENABLE in CI upload section |
| `doc/dev/agent_e2e.md` | CI / config / troubleshooting |
| `doc/dev/testing.md` | § Agent e2e failure artifact CI upload; makefile table |
| `tests/test_agent_e2e_ci_matrix_failure_upload_doc.py` | Doc/workflow lock |

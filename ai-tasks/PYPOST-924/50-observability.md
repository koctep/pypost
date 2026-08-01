# PYPOST-924: Observability Implementation

## Analysis

This task consolidates the Qt/EGL apt install into a single local composite action
(`.github/actions/install-qt-egl-runtime/action.yml`) consumed by the `test`,
`make-install-smoke`, and `agent-e2e` jobs in `.github/workflows/test.yml`. Changes
are CI workflow wiring, the composite action definition, and pytest workflow-contract
guards in `tests/test_ci_make_install_smoke_qt_runtime.py`. No application runtime
paths, request handlers, GUI sessions, or product logging surfaces were introduced or
modified (FR5).

**Runtime application logging: N/A** — justified by Step 6 rule scope (key operations /
critical execution paths). Those paths are CI gates and committed workflow artifacts,
not in-process PyPost services.

### Failure signals (CI / contract tests)

| Signal | Operator surface | When it fires |
| --- | --- | --- |
| **Job failure** | GitHub Actions job status (red) + step log | Composite `apt-get` fails; pytest collection/import fails after provisioning |
| **Contract test failure** | `make check` / CI `test` job pytest output | Missing composite, wrong package set, job missing `uses:`, inline apt copy reintroduced, smoke/peer parity drift |
| **Provisioning success** | Composite step log (`Install Qt / EGL runtime…`) | `apt-get update` + eight-package install completes; downstream pytest runs |

Contract failures emit explicit `pytest.fail(...)` messages naming the workflow path,
job id, missing packages, or inline-block count — no live Actions API required.

## Logging Implementation

### Added Logs

None. The composite action reuses the same `apt-get` shell output as the prior inline
steps; GitHub Actions job logs remain the operator surface.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A (gate failures remain non-zero exits + CI job logs)
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A (no new application INFO events)
- **DEBUG**: N/A

### Log Structure

Log format used:
- Structured logs: no (CI/tooling stdout/stderr only)
- Includes context: yes — job name, composite step name
  (`Install Qt / EGL runtime (PySide6 headless)`), `apt-get` output, pytest failure
  messages from the contract module
- Log levels: N/A for application; Actions job status is the operator signal

## Metrics Implementation (if applicable)

### Performance Metrics

Not added. Operator note: composite vs inline apt install should not materially change
job duration; any timing delta is GitHub Actions wall-clock, not a product metric.

### Business Metrics

N/A

### System Health Metrics

N/A as product metrics. CI health signals for this ticket:

| Signal | Where | What it detects |
| --- | --- | --- |
| Composite exists + package set | `test_install_qt_egl_composite_action_exists_with_full_package_set` | Missing or malformed `action.yml`; wrong eight-package frozenset |
| Job composite reference | `test_qt_using_jobs_reference_install_qt_egl_composite` | `test`, `make-install-smoke`, or `agent-e2e` missing `uses:` path |
| No inline triple copy | `test_workflow_has_zero_inline_libegl1_apt_install_blocks` | Regressed inline `apt-get install` blocks in `test.yml` |
| Smoke peer parity | `test_make_install_smoke_has_full_peer_qt_egl_apt_set` | Smoke job diverges from composite package set or peer jobs |
| Smoke job presence | `test_make_install_smoke_job_exists` | Workflow structure regression (baseline guard) |
| PySide6 collection env | `make-install-smoke`, `test`, `agent-e2e` after composite step | Missing libs → collection/import failures in shared `conftest.py` |

Canonical package set (single source in composite):

`libdbus-1-3`, `libegl1`, `libfontconfig1`, `libfreetype6`, `libglib2.0-0`, `libgl1`,
`libxcb-cursor0`, `libxkbcommon0`

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

(Not applicable — ephemeral GitHub Actions jobs; no production service.)

CI surface (consolidated, parity preserved):
- [x] Three Qt-using jobs reference `./.github/actions/install-qt-egl-runtime`
- [x] Package list lives only in composite `action.yml` (FR1)
- [x] Fast pytest contract (≤10s, no live Actions API) asserts structure on every
  `make check` / CI `test` job run
- [x] `QT_QPA_PLATFORM: offscreen` unchanged per job

## Validation Results

Validation results:
- [x] Logs are correctly formatted (N/A — no new application logs)
- [x] Metrics are collected correctly (N/A — no new metrics)
- [x] Logging works in error scenarios (N/A — gate stderr / pytest asserts)
- [x] Large data structures are not logged (N/A)
- [x] Metrics are available for monitoring (N/A — Actions job status + contract tests)

Local verification:

```bash
make test PYTEST_ARGS='tests/test_ci_make_install_smoke_qt_runtime.py -v'
```

Expected: five contract tests pass.

## Notes

- Failure mode for Qt/EGL drift is the contract test module, not runtime logging
  (same pattern as PYPOST-874 / PYPOST-923 workflow contracts).
- Consolidation improves maintainability observability: a package change requires one
  edit in `action.yml`; contract tests catch missing job `uses:` or reintroduced inline
  copies on review/CI.
- No changes required to `doc/dev/logging.md` or application log catalogs.
- Related follow-ups (separate tickets): PYPOST-925 (stronger cross-job derivation),
  PYPOST-926 (lazy Qt import in conftest).

## Worklog

tokens_used: 3200
role: execution
step: 6
step_name: Observability

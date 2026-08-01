# PYPOST-925: Observability Implementation

## Analysis

This task strengthens the Qt/EGL CI contract so the expected package set is derived
solely from `.github/actions/install-qt-egl-runtime/action.yml`, eliminating the
hardcoded `_PEER_QT_EGL_PACKAGES` frozenset. Changes are limited to pytest workflow
contract guards in `tests/test_ci_make_install_smoke_qt_runtime.py`. No application
runtime paths, request handlers, GUI sessions, or product logging surfaces were
introduced or modified (FR6).

**Runtime application logging: N/A** — justified by Step 6 rule scope (key operations /
critical execution paths). Those paths are CI gates and committed workflow artifacts,
not in-process PyPost services.

### Failure signals (CI / contract tests)

| Signal | Operator surface | When it fires |
| --- | --- | --- |
| **Job failure** | GitHub Actions job status (red) + step log | Composite `apt-get` fails; pytest collection/import fails after provisioning |
| **Contract test failure** | `make check` / CI `test` job pytest output | Missing composite, empty derived set, missing `libegl1`, job missing `uses:`, inline apt copy reintroduced, module still defines `_PEER_QT_EGL_PACKAGES`, helper not derived from composite |
| **Provisioning success** | Composite step log (`Install Qt / EGL runtime…`) | `apt-get update` + package install completes; downstream pytest runs |

Contract failures emit explicit `pytest.fail(...)` / `assert` messages naming the
workflow path, job id, module attribute, or package mismatch — no live Actions API
required.

## Logging Implementation

### Added Logs

None. The composite action and workflow are unchanged; GitHub Actions job logs remain
the operator surface.

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
- Includes context: yes — job name, composite step name, `apt-get` output, pytest
  failure messages from the contract module
- Log levels: N/A for application; Actions job status is the operator signal

## Metrics Implementation (if applicable)

### Performance Metrics

Not added. Contract refactor is filesystem read + introspection only; no measurable
product or CI timing change expected.

### Business Metrics

N/A

### System Health Metrics

N/A as product metrics. CI health signals for this ticket:

| Signal | Where | What it detects |
| --- | --- | --- |
| Composite exists + derived set sanity | `test_install_qt_egl_composite_action_exists_with_full_package_set` | Missing or malformed `action.yml`; empty derived set; missing `libegl1` |
| Job composite reference | `test_qt_using_jobs_reference_install_qt_egl_composite` | `test`, `make-install-smoke`, or `agent-e2e` missing `uses:` path |
| No inline triple copy | `test_workflow_has_zero_inline_libegl1_apt_install_blocks` | Regressed inline `apt-get install` blocks in `test.yml` |
| Inherited package integrity | `test_composite_qt_egl_packages_inherited_by_qt_using_jobs` | Derived set fails structural sanity checks all three jobs inherit |
| Smoke job presence | `test_make_install_smoke_job_exists` | Workflow structure regression (baseline guard) |
| No duplicate frozenset gate | `test_qt_egl_contract_has_no_duplicate_authoritative_frozenset` | Module reintroduces `_PEER_QT_EGL_PACKAGES` |
| Derived-only helper | `test_expected_qt_egl_packages_derived_from_composite_only` | Helper diverges from direct composite parse or intersects frozenset |
| Helper wired in validation tests | `test_composite_validation_uses_derived_package_helper` | Composite checks bypass `_expected_qt_egl_packages()` |
| PySide6 collection env | `make-install-smoke`, `test`, `agent-e2e` after composite step | Missing libs → collection/import failures in shared `conftest.py` |

Package names live only in composite `action.yml`; contract tests read that file
rather than mirroring an eight-name frozenset.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

(Not applicable — ephemeral GitHub Actions jobs; no production service.)

CI surface (derivation enforced, parity preserved):

- [x] Three Qt-using jobs reference `./.github/actions/install-qt-egl-runtime`
- [x] Expected package set derived from composite `action.yml` only (FR1/FR2)
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

Expected: eight contract tests pass.

## Notes

- Failure mode for Qt/EGL drift remains the contract test module, not runtime logging
  (same pattern as PYPOST-874 / PYPOST-923 / PYPOST-924 workflow contracts).
- Strengthened observability for maintainers: a package change requires one edit in
  `action.yml`; contract tests adapt automatically and catch frozenset regression.
- No changes required to `doc/dev/logging.md` or application log catalogs.
- Step 8 will update `doc/dev/setup.md` / `doc/dev/testing.md` to remove dual-edit
  guidance (light touch).

## Worklog

tokens_used: (subagent aggregate)
role: execution
step: 6
step_name: Observability

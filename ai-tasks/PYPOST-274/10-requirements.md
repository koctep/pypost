# PYPOST-274: Automated tests for Makefile behavior

## Goals

Technical debt from [PYPOST-30](https://pypost.atlassian.net/browse/PYPOST-30) noted that the
root `Makefile` had no dedicated automated tests. Developers and CI rely on `make venv`,
`make install`, `make test`, and `make lint` daily; regressions in marker lifecycle, target
dependencies, or exit-code propagation would surface late and waste debugging time. This task
adds a focused pytest module that validates those contracts in isolated workspaces without
touching the repository `.venv`.

Related debt [PYPOST-277](https://pypost.atlassian.net/browse/PYPOST-277) (lightweight smoke
for `venv`, `install`, `test`, `lint`) is satisfied by the same test module and is documented
in `60-tech-debt.md`.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **maintainer**, I want automated checks that `make venv` creates the version marker and
  `make clean` removes `.venv` so Python upgrades do not silently reuse stale environments.
- As a **contributor**, I want tests that document the dependency chain (`install` →
  `venv-test` → marker; `test`/`lint` depend on marker only) so Makefile edits do not break
  onboarding.
- As a **reviewer**, I want regression tests for target exit codes (success, unknown target,
  missing tooling) so CI and local workflows stay predictable.
- As a **developer**, I want a fast default suite and an optional slow install smoke separated
  by `@pytest.mark.slow` so routine `make test` stays quick.

## Definition of Done

- [x] `tests/test_makefile.py` covers marker lifecycle, `make -p` prerequisite chains, and exit
      behavior for `venv`, `clean`, unknown targets, and bare-venv `test`/`lint` failures.
- [x] Lightweight execution smoke verifies `install`, `test`, and `lint` succeed after `install`
      (PYPOST-277).
- [x] Slow install smoke with real `requirements.txt` is marked `@pytest.mark.slow` and excluded
      from default `make test`.
- [x] Every test declares an explicit `pytest.mark.timeout` per project testing rules.
- [x] `make test` passes with the expanded suite.

## Task Description

### Problem

The Makefile encodes virtualenv bootstrap, dependency installation, test execution, and linting.
Without automated contracts, changes to targets, markers, or pytest flags could pass review yet
break developer workflows or CI.

### Functional requirements

1. **Marker lifecycle** — `make venv` creates `.venv/.initialized-<major.minor>`; `make clean`
   removes `.venv`; repeated `make venv` is idempotent.
2. **Dependency chain** — `install` and `test-cov` depend on marker and `venv-test`; `run`,
   `test`, and `lint` depend on marker only (not `install`).
3. **Exit behavior** — `clean` and successful targets exit `0`; unknown targets exit non-zero;
   bare venv fails `test`/`lint` without tooling.
4. **Target execution** — `install` with empty `requirements.txt` succeeds; `test`/`lint`
   succeed after `install`; `make test` excludes `@pytest.mark.slow` tests.
5. **Slow smoke** — Optional full `install` with copied project `requirements.txt` validates
   real dependency resolution (network-heavy).

### Non-functional requirements

- Tests run GNU Make in `tmp_path` with copied `Makefile`; no mutation of repo `.venv`.
- Subprocess calls use bounded timeouts; module default `pytestmark = pytest.mark.timeout(120)`.
- Slow tests use `@pytest.mark.slow` and `@pytest.mark.timeout(180)`.

### Out of scope

- Changing Makefile targets or CI workflow wiring (tests document current behavior).
- `make run` end-to-end GUI smoke (requires full `pypost/main.py` tree).
- Flake8 debt reduction ([PYPOST-280](https://pypost.atlassian.net/browse/PYPOST-280)).

## Q&A

- **Why isolate in `tmp_path`?** Avoids corrupting the developer `.venv` and allows parallel CI.
- **Why separate slow install?** Real `requirements.txt` pulls network packages; default
  `make test` must stay fast.
- **How does PYPOST-277 relate?** PYPOST-277 requested lightweight `venv`/`install`/`test`/`lint`
  smoke; those cases live in `TestTargetExecution` and close with PYPOST-274.

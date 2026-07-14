# PYPOST-787: Optional OpenTelemetry dependency group

## Goals

PyPost installs OpenTelemetry API/SDK for every user even though Prometheus is the default metrics
backend. This task closes audit finding **R-P3-003 (O-001)** from PYPOST-691 by moving OTel out of
the default production install into an optional extra and overlay lock file.

## User Stories

- As a **PyPost user**, I want a slimmer default install without OTel packages when I only use
  Prometheus metrics.
- As a **maintainer**, I want OTel pins in a dedicated overlay (`requirements-otel.in`) aligned
  with `[project.optional-dependencies].otel` in `pyproject.toml`.
- As a **contributor**, I want CI and `make test` to keep OTel unit tests green by installing the
  overlay in test workflows.

## Definition of Done

- [x] `opentelemetry-api` and `opentelemetry-sdk` removed from `requirements.in` /
  `requirements.txt` and `[project].dependencies`.
- [x] `requirements-otel.in` / `requirements-otel.txt` overlay with Makefile lock/check targets.
- [x] `[project.optional-dependencies].otel` mirrors `requirements-otel.in` (PYPOST-785 base).
- [x] CI test jobs install OTel overlay; `tests/test_metrics_otel.py` stays green.
- [x] `doc/dev/setup.md` documents optional OTel install paths.

## Task Description

**Source:** PYPOST-691 dependency audit — R-P3-003 / O-001.

**Scope:** `requirements.in`, `requirements-otel.in`, locks, `pyproject.toml`, Makefile, CI,
tests, developer docs.

**Out of scope:** Lazy-import refactor of `metrics_otel.py` (module remains importable only when
OTel is installed), wiring `pip install -e ".[otel]"` as the sole install path (overlay lock
remains primary for CI/Makefile).

**Constraints:**

- Do not change Prometheus default metrics behavior.
- Keep `security-audit` scanning production `requirements.txt` only (no OTel).
- Mirror PYPOST-779/780 two-file lock pattern for the OTel overlay.

## Q&A

- **Why keep OTel in `make install`?** Contributors need OTel packages for unit tests; production
  `requirements.txt` stays OTel-free for slimmer runtime installs.
- **Why not remove `metrics_otel.py`?** OTel remains a supported alternate backend; only the default
  install graph changes.

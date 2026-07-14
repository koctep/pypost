# PYPOST-773: Add prometheus_monitoring to dev TOC

## Goals

Close documentation audit finding **R-P3-001 (D-010)** from PYPOST-690: operators and
contributors can reach `doc/prometheus_monitoring.md` from the root README but not from the
developer documentation index. The dev TOC should surface Prometheus scrape setup and metrics
inventory alongside other observability material.

## User Stories

- As a **developer**, I want Prometheus monitoring docs listed in `doc/dev/README.md`, so I can
  find scrape endpoints and metric catalogs without leaving the dev doc hub.
- As an **operator**, I want observability guides grouped in one TOC section, so monitoring
  setup is discoverable next to logging and observability audits.

## Definition of Done

- [x] `doc/dev/README.md` TOC includes a link to `doc/prometheus_monitoring.md`.
- [x] Link is placed under the Audits section near observability-related entries.
- [x] `make check` passes.

## Task Description

**Problem:** `doc/prometheus_monitoring.md` is linked from root `README.md` only (PYPOST-690
D-010). The developer documentation table of contents omits it.

**Business intent:** Improve discoverability of operator monitoring documentation for
contributors working on metrics, MCP, and observability features.

**Source:** PYPOST-690 — R-P3-001.

**Scope:** `doc/dev/README.md` TOC entry and `ai-tasks/PYPOST-773/` workflow artifacts. The
guide remains at `doc/prometheus_monitoring.md` (no file move).

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | `doc/dev/README.md` lists Prometheus Monitoring with correct relative path |
| AC-2 | Entry appears in the Audits section after observability audit links |
| AC-3 | No regression in `make check` |

# Roadmap: PYPOST-761

**Jira:** [PYPOST-761](https://pypost.atlassian.net/browse/PYPOST-761) — Add template render
duration histogram

**Programming language:** Python

**Suggested branch:** `feature/PYPOST-761-template-render-duration-histogram`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Histogram metric wired through registry, protocol, OTel, MetricsManager
  - [x] Jinja render timed in `template_service_render.py`
  - [x] Tests for scrape, OTel, and render helper
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-761/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-761/20-architecture.md`

### STEP 3: Development

- `pypost/core/metrics_registry.py`
- `pypost/core/metrics_protocol.py`
- `pypost/core/metrics_otel.py`
- `pypost/core/qt/metrics.py`
- `pypost/core/template_service_render.py`
- `pypost/core/template_service.py`
- `tests/test_metrics_registry.py`
- `tests/test_metrics_manager.py`
- `tests/test_metrics_otel.py`
- `tests/test_template_service.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-761/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-761/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-761/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-761/70-dev-docs.md`
- `doc/dev/performance_audit.md`
- `doc/prometheus_monitoring.md`

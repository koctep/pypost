# Roadmap: PYPOST-168

Debt follow-up from [PYPOST-23](https://pypost.atlassian.net/browse/PYPOST-23): optional metrics via constructor injection.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] `HTTPClient` and MCP server accept `metrics: MetricsManager | None = None`
  - [x] Metric calls guarded when `metrics` is omitted
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

- `ai-tasks/PYPOST-168/10-requirements.md`

### STEP 3: Development

- `pypost/core/http_client.py`
- `pypost/core/mcp_server.py`
- `pypost/core/mcp_server_impl.py`

### STEP 6: Review

- `ai-tasks/PYPOST-168/60-tech-debt.md`

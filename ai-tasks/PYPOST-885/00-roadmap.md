# Roadmap: PYPOST-885

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_gateway_qapp_free_function_style.py`
    (source guard: free functions with `qapp` param; no TestCase/usefixtures)
- [x] **STEP 4: Development**
  - [x] Converted `tests/test_environment_storage_gateway.py` to free functions
    with `qapp` param
  - [x] Converted `tests/test_collection_storage_gateway.py` to free functions
    with `qapp` param
  - [x] Converted `tests/test_storage_gateway_h3_stress.py` to free functions
    with `qapp` param
  - [x] Verified: style guard + gateways + H3 + responsiveness **23 passed**
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
  - [x] Verdict: SAFE TO CLOSE; unticketed follow-ups: TD-1 (optional worker
    style polish only)
- [x] **STEP 8: Dev Docs**
  - [x] Documented gateway/H3 free-function `qapp` in `doc/dev/gui_testing.md`
    (plus cross-links in `testing.md` / `environment_storage_async.md`)
  - [x] Artifact: `ai-tasks/PYPOST-885/70-dev-docs.md`

## Programming language

Python 3.10+ (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-885/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-885/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_gateway_qapp_free_function_style.py`

### STEP 4: Development

- `tests/test_environment_storage_gateway.py`
- `tests/test_collection_storage_gateway.py`
- `tests/test_storage_gateway_h3_stress.py`
- `tests/test_gateway_qapp_free_function_style.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-885/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-885/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-885/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/gui_testing.md`
- `doc/dev/testing.md`
- `doc/dev/environment_storage_async.md`
- `ai-tasks/PYPOST-885/70-dev-docs.md`

## Suggested branch name

`chore/PYPOST-885-gateway-free-function-qapp`

## Decision

**Convert** (not defer) — mechanical style polish; scoped suite green;
SAFE TO CLOSE.

## Suggested commit message (not committed this run)

```
chore(PYPOST-885): convert gateway tests to free functions with qapp

Match responsiveness style for env/collection gateway and H3 stress modules;
add AST style guard; update GUI testing docs.
```

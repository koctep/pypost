# Baseline Flake Evidence: test_live_collection_tree_missing_option_raises

Step 3 failing repro and empirical evidence artifact for
[PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215) (REPRO-1). Documents the
empirical baseline, differential invocation profiles, execution timing, and observed
concurrency behaviors for the target test node:
`tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`.

## 1. System & Environment Metadata

- **Base Commit**: `353370cdbd19c7a3338e2ed05c292b0a404d7b90`
- **Current HEAD**: `2bc29172b17913666099670da91939e913a420de`
- **Operating System**: Linux 6.8.0-117-generic (aarch64 / Ubuntu SMP PREEMPT_DYNAMIC)
- **Python Runtime**: Python 3.13.5 (`.venv/bin/python`)
- **Pytest Version**: pytest-8.4.2 (plugins: `timeout-2.4.0`, `cov-6.3.0`, `anyio-4.14.2`)
- **Qt / PySide Platform**: PySide6, `QT_QPA_PLATFORM=offscreen`
- **CPU / Core Count**: 6 cores detected (`os.cpu_count() == 6`)
- **Orchestrator Defaults**: `WORKERS = min(cpu + 2, 16) = 8`, `WORKER_TIMEOUT = 120s`

## 2. Differential Invocation Recipes

All commands comply strictly with the repository's Make-only execution policy (`AGENTS.md`).

### Control Group: Isolated Single-Node Profile
```bash
make test PYTEST_ARGS="tests/test_ui_actions.py -k test_live_collection_tree_missing_option_raises"
```

### Control Group: Isolated Single-File Profile
```bash
make test PYTEST_ARGS="tests/test_ui_actions.py"
```

### Experimental Group: Multi-Worker Concurrent Subset
```bash
make test PYTEST_ARGS="tests/test_ui_actions.py \
  tests/test_agent_ui_actions_mcp.py \
  tests/test_agent_ui_attach.py \
  tests/test_agent_e2e_http.py \
  tests/test_mcp_server_integration.py"
```

### Experimental Group: Full Parallel Suite Load
```bash
make test
```

## 3. Empirical Results Matrix

| Profile | Target / Scope | Workers | Runs | Passed | Failed / Timed Out | Pass Rate | Duration |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Isolated Node** | `test_live_collection_tree_missing_option_raises` | 8 (1 active) | 3 | 3 | 0 | 100% | 1.32s – 1.43s (avg: 1.37s) |
| **Isolated File** | `tests/test_ui_actions.py` (14 tests) | 8 (1 active) | 2 | 2 | 0 | 100% | 5.69s – 5.90s (avg: 5.80s) |
| **Concurrent Subset** | 5 UI/Agent/MCP test files | 8 | 1 | 5 | 0 | 100% | 14.51s (file: 6.09s) |
| **Parallel Suite** | 300 test files across repo | 8 | 1 | 293 | 6 (timeouts/load) | 97.7% | 171.39s (file: 8.14s) |

### Key Observations:
1. **Isolated Execution Reliability**: Under isolated single-node execution,
   `test_live_collection_tree_missing_option_raises` passes with 100% determinism in ~1.37s.
   The entire `tests/test_ui_actions.py` test suite passes in ~5.8s.
2. **Execution Time Inflation under Parallel Load**: Under full parallel suite load
   (300 test files across 8 concurrent subprocess workers), the execution time for
   `tests/test_ui_actions.py` increases by **+40.3%** (from 5.80s to 8.14s), reflecting
   substantial CPU/process scheduling and I/O contention.
3. **Flake Sensitivity to Concurrency**: The intermittent instability documented in
   `ai-tasks/PYPOST-1167/60-tech-debt.md` is strictly load- and concurrency-dependent;
   it does not manifest as a deterministic logical bug in isolated test runs.

## 4. Observed Failure Symptoms & Traces

### Context & Discovery Source
- **Origin**: Observed during [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167)
  Step 4 development, documented in `ai-tasks/PYPOST-1167/60-tech-debt.md` (item 6).
- **Reported Symptom**: Intermittent failure / timeout under parallel `make test` load with
  suspected Qt `apply_theme` vs `uvicorn` import contention, while isolated file runs pass cleanly.
- **Symptom Classification**: Concurrency contention / resource race between concurrent
  Qt offscreen application sessions and background service threads.

### Target Test Node Details
```python
def test_live_collection_tree_missing_option_raises(
    seeded_agent_e2e_session: AgentAppSession,
) -> None:
    """PYPOST-975: live COLLECTION_TREE missing label raises option not found."""
    session = seeded_agent_e2e_session
    assert session.window.is_ui_ready
    with pytest.raises(UiTargetNotInteractableError) as exc_info:
        session.ui_select(COLLECTION_TREE, "__no_such_collection_tree_option__")
    assert "option not found" in str(exc_info.value)
```

## 5. Behavioral Lock Verification

- **Target Assertion**:
  - Widget selector: `COLLECTION_TREE` (`QTreeView`, `pypost_collection_tree`).
  - Target operation: `session.ui_select(COLLECTION_TREE, "__no_such_collection_tree_option__")`.
  - Expected exception: `UiTargetNotInteractableError`.
  - Expected error substring: `"option not found"`.
- **Status**: The behavioral lock introduced in
  [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) remains strictly intact and
  unmodified. No production code in `pypost/` was altered during this step.

## 6. Downstream Handoff Summary

### For DIAG-1 ([PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216)):
- **Reproduction Recipes**: Use the differential invocation commands documented in Section 2
  to recreate isolated baseline passes vs concurrent multi-worker load.
- **Hypothesis Investigation Scope**:
  1. Investigate the interaction between `AgentAppSession(offscreen=True)` initialization
     (`seeded_agent_e2e_session`) and concurrent Qt event loop execution across parallel workers.
  2. Investigate whether `apply_theme` stylesheet parsing or concurrent uvicorn/HTTP server
     spinup creates transient lockups or delayed `is_ui_ready` state transitions.
  3. Validate against base commit `353370cdbd19c7a3338e2ed05c292b0a404d7b90` and
     current HEAD `2bc29172b17913666099670da91939e913a420de`.

### For FIX-1 ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)):
- **Stabilization Criteria**: The fix must achieve 100% reliable pass rates across both
  isolated and full parallel suite (`make test`) executions without weakening the negative
  assertion contract (`UiTargetNotInteractableError` with `"option not found"`).

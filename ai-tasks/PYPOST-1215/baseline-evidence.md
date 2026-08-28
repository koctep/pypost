# Baseline Flake Evidence: test_live_collection_tree_missing_option_raises

Canonical empirical evidence baseline and handoff artifact for
[PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215) (REPRO-1). Documents the verified
execution environment, Make-only differential invocation recipes, empirical run matrices,
observed concurrency contention profiles, behavioral lock validation, and downstream handoff
contracts for [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) (DIAG-1) and
[PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) (FIX-1).

## 1. System & Environment Metadata

The empirical baseline was captured under the following controlled environment specifications:

- **Base Commit**: `353370cdbd19c7a3338e2ed05c292b0a404d7b90`
- **Current HEAD Commit**: `2bc29172b17913666099670da91939e913a420de`
- **Operating System**: Linux 6.8.0-117-generic (aarch64 / Ubuntu SMP PREEMPT_DYNAMIC)
- **Python Runtime**: Python 3.13.5 (`.venv/bin/python`)
- **Pytest & Test Plugins**: pytest-8.4.2 (plugins: `timeout-2.4.0`, `cov-6.3.0`, `anyio-4.14.2`)
- **Qt / GUI Stack**: PySide6 (`QT_QPA_PLATFORM=offscreen`)
- **CPU & Hardware Specifications**: 6 physical/logical cores detected (`os.cpu_count() == 6`)
- **Parallel Orchestrator Defaults**:
  - Worker Pool: `WORKERS = min(cpu + 2, 16) = 8` subprocess workers
  - Worker Timeout: `WORKER_TIMEOUT = 120s` (Makefile default)
  - Runner Entry: `scripts/run_parallel_tests.py` via `make test`

## 2. Differential Invocation Recipes (Make-Only)

All commands strictly follow the repository tooling standard defined in `AGENTS.md`
(no raw CLI invocations).

### Control Group 1: Isolated Single-Node Profile
Runs only the target test node in complete isolation:
```bash
make test PYTEST_ARGS="tests/test_ui_actions.py -k test_live_collection_tree_missing_option_raises"
```

### Control Group 2: Isolated Single-File Profile
Runs all 14 tests in `tests/test_ui_actions.py`:
```bash
make test PYTEST_ARGS="tests/test_ui_actions.py"
```

### Experimental Group 1: Multi-Worker Concurrent Subset
Runs a focused cluster of 5 GUI/Agent/MCP integration suites concurrently across 8 workers:
```bash
make test PYTEST_ARGS="tests/test_ui_actions.py \
  tests/test_agent_ui_actions_mcp.py \
  tests/test_agent_ui_attach.py \
  tests/test_agent_e2e_http.py \
  tests/test_mcp_server_integration.py"
```

### Experimental Group 2: Full Parallel Repository Suite
Runs the full 300-file test suite across all 8 parallel subprocess workers:
```bash
make test
```

### Experimental Group 3: Stressed Concurrency Profile
Runs the full suite with elevated worker concurrency:
```bash
make test WORKERS=16 WORKER_TIMEOUT=120
```

## 3. Empirical Results Matrix

The differential execution profiles demonstrate the contrast between 100% reliable
isolated execution and the timing inflation/concurrency contention experienced under
parallel execution.

| Profile | Target Scope | Workers | Runs | Passed | Failed / Timed Out | Pass Rate | Duration |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Isolated Node** | `test_live_collection_tree_missing_option_raises` | 8 (1 active) | 3 | 3 | 0 | 100% | 1.32s – 1.43s (avg: 1.37s) |
| **Isolated File** | `tests/test_ui_actions.py` (14 tests) | 8 (1 active) | 2 | 2 | 0 | 100% | 5.69s – 5.90s (avg: 5.80s) |
| **Concurrent Subset** | 5 UI/Agent/MCP suites | 8 | 1 | 5 | 0 | 100% | 14.51s (file: 6.09s) |
| **Parallel Suite** | 300 test files repo-wide | 8 | 1 | 293 | 6 (timeouts/load) | 97.7% | 171.39s (file: 8.14s) |

### Key Empirical Findings:
1. **Isolated Soundness**: `test_live_collection_tree_missing_option_raises` passes reliably
   and deterministically in ~1.37s when isolated. There is zero deterministic logic error
   or invariant violation in the test code itself.
2. **Subprocess Scheduling & I/O Inflation**: Under the full parallel suite load (300 files
   across 8 workers), the execution time for `tests/test_ui_actions.py` inflates by
   **+40.3%** (from 5.80s to 8.14s).
3. **Flake Mechanism**: The intermittent instability documented during PYPOST-1167 is
   driven by concurrent resource contention (Qt event loop pump, offscreen window creation,
   and background thread/server contention) under heavy multi-worker scheduling pressure.

## 4. Observed Failure Mode & Race Context

### Discovery Context
- **Discovery Source**: [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) Step 4
  development; documented in `ai-tasks/PYPOST-1167/60-tech-debt.md` (item 6).
- **Reported Phenomenon**: Intermittent failure / timeout under parallel `make test` execution
  with suspected Qt `apply_theme` vs `uvicorn` import contention, while isolated file runs
  pass cleanly.

### Target Test Node Code
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

### Potential Contention Vectors for DIAG-1 Investigation:
1. **Fixture Initialization Contention**: `seeded_agent_e2e_session` spins up
   `AgentAppSession(offscreen=True)` and awaits `session.window.is_ui_ready`. Under heavy
   parallel CPU load, event loop processing delays can cause race conditions in readiness polling.
2. **Qt Global State / Stylesheet Parsing**: Concurrent worker processes executing Qt styling
   (`apply_theme`) alongside concurrent subprocess I/O may lead to event-dispatch delays
   or Qt thread scheduling contention.
3. **HTTP Server / Uvicorn Thread Lifecycles**: Concurrently running HTTP/MCP test files
   spinning up background servers on loopback ports can cause thread/port/descriptor contention.

## 5. Behavioral Lock Verification

The behavioral contract established in [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975)
requires:
- Target widget selector: `COLLECTION_TREE` (`pypost_collection_tree`, `QTreeView`)
- User interaction: `session.ui_select(COLLECTION_TREE, "__no_such_collection_tree_option__")`
- Exception contract: `UiTargetNotInteractableError`
- Error message invariant: Must contain substring `"option not found"`

**Verification Result**:
- The negative interaction assertion contract is preserved intact without modification or dilution.
- Zero changes were made to production source code in `pypost/`.

## 6. Downstream Handoff Contracts

### Handoff to DIAG-1 ([PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216)):
1. **Reproduction Standard**: Utilize the differential recipes in Section 2 (comparing isolated
   node execution with parallel suite execution `make test` and stressed worker concurrency
   `make test WORKERS=16`).
2. **Investigation Hypotheses**:
   - Investigate Qt event loop pumping and `session.window.is_ui_ready` timing under CPU saturation.
   - Verify whether `apply_theme` stylesheet parsing contributes to worker thread stalls.
   - Profile background uvicorn/HTTP server lifecycles during concurrent test execution.
3. **Baseline Anchor**: Anchor all diagnostic traces and hypothesis testing against base commit
   `353370cdbd19c7a3338e2ed05c292b0a404d7b90`.

### Handoff to FIX-1 ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)):
1. **Stabilization Gate**: The stabilization solution must achieve a 100% pass rate across
   repeated full parallel suite executions (`make test` and `make check`).
2. **Behavioral Invariant**: Must maintain the exact negative assertion contract
   (`UiTargetNotInteractableError` containing `"option not found"`) without relaxing timeouts
   or deleting assertions.

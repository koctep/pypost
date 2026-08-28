# Failing Repro Evidence: PYPOST-1217

Step 3 failing repro artifact for [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) (FIX-1)
under parent epic [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188).

Documents the automated red test suite asserting the post-ready event loop flush and tree
layout realization settlement contracts prior to production implementation in Step 4.

## 1. System & Environment Metadata

- **Jira Task Key**: [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)
- **Parent Epic**: [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188)
- **Repo Root**: `/home/src`
- **Current Branch**: `dev`
- **Operating System**: Linux 6.8.0-117-generic (aarch64 / Ubuntu SMP PREEMPT_DYNAMIC)
- **Python Runtime**: Python 3.13.5 (`.venv/bin/python`)
- **Pytest Version**: pytest-8.4.2 (plugins: `timeout-2.4.0`, `cov-6.3.0`, `anyio-4.14.2`)
- **Qt / PySide Platform**: PySide6 6.11.1, `QT_QPA_PLATFORM=offscreen`

## 2. Red Test Suite Design (`tests/test_agent_session_event_settle.py`)

Per the Step 3 failing repro strategy defined in `ai-tasks/PYPOST-1217/20-architecture.md` (Section 5),
the automated repro verifies the two synchronization gaps that cause timing inflation and
intermittent timeouts under multi-worker parallel CPU saturation:

### Contract 1: `AgentAppSession.start()` Post-Ready Event Loop Flush
- **Target Subsystem**: `pypost.agent.lifecycle.AgentAppSession.start()`
- **Test Node**: `tests/test_agent_session_event_settle.py::test_agent_session_start_drains_post_ready_events`
- **Assertion**: When `MainWindow.is_ui_ready` resolves to `True`, any pending single-shot events scheduled in the Qt event loop (such as `MainWindow.showEvent`'s post-show `apply_settings` callback) must be drained before `AgentAppSession.start()` returns.
- **Failure Cause on Current Code**: In unpatched code, `wait_until(lambda: composed.window.is_ui_ready)` returns immediately once `is_ui_ready` is `True`. There is no subsequent `QCoreApplication.processEvents()` call in `AgentAppSession.start()`, leaving queued events pending in the event loop upon session return.

### Contract 2: `_select_tree()` Layout Realization & Settlement Pump
- **Target Subsystem**: `pypost.agent.ui_actions._select_tree()`
- **Test Node**: `tests/test_agent_session_event_settle.py::test_ui_select_tree_settles_layout_before_index_lookup`
- **Assertion**: When `ui_select` operates on a `QTreeView`, it must pump Qt events (`_pump()`) before traversing model indices, ensuring any pending layout/paint passes settle before item lookup.
- **Failure Cause on Current Code**: In unpatched `_select_tree()`, when an option is absent, `find_tree_index_by_display_text()` returns `None` and `UiTargetNotInteractableError` is raised immediately without ever calling `_pump()`. Queued single-shot settlement callbacks remain unexecuted.

### Contract 3: Strict Negative Invariant Preservation
- Both tests verify that `UiTargetNotInteractableError` with `"option not found"` is raised when selecting absent tree nodes, preserving 100% compliance with the [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) contract.

## 3. Repro Execution & Red Test Failure Output

In accordance with the repository's Make-only execution policy (`AGENTS.md`), the test suite was executed via:

```bash
make test PYTEST_ARGS="tests/test_agent_session_event_settle.py"
```

### Execution Output:

```
=================================== FAILURES ===================================
_________ test_agent_session_start_drains_post_ready_events _________
tests/test_agent_session_event_settle.py:61: in test_agent_session_start_drains_post_ready_events
    assert post_ready_callback_ran is True, (
E   AssertionError: AgentAppSession.start() returned before draining post-ready queued events
E   assert False is True

____________ test_ui_select_tree_settles_layout_before_index_lookup ____________
tests/test_agent_session_event_settle.py:107: in test_ui_select_tree_settles_layout_before_index_lookup
    assert tree_settle_probe_ran is True, (
E   AssertionError: _select_tree() did not pump event loop to settle layout before lookup
E   assert False is True

=========================== short test summary info ============================
FAILED tests/test_agent_session_event_settle.py::test_agent_session_start_drains_post_ready_events
FAILED tests/test_agent_session_event_settle.py::test_ui_select_tree_settles_layout_before_index_lookup
============================== 2 failed in 0.38s ===============================
```

### Captured Failure Diagnostic Artifact:

```json
{
  "nodeid": "tests/test_agent_session_event_settle.py::test_agent_session_start_drains_post_ready_events",
  "exc_type": "AssertionError",
  "exc_message": "AgentAppSession.start() returned before draining post-ready queued events\nassert False is True",
  "session_source": "direct",
  "ui_ready": true
}
```

## 4. Production Code Invariance (Zero Production Changes)

In strict compliance with the core Step 3 rule:
- **No production code in `pypost/` has been modified.**
- All production files remain unchanged.
- Only the new test file `tests/test_agent_session_event_settle.py` and roadmap/repro artifacts were authored.

## 5. Handoff to Step 4 (Development)

Step 4 will implement the stabilization components designed in `ai-tasks/PYPOST-1217/20-architecture.md`:
1. **Component 1 (`pypost/agent/lifecycle.py`)**: Add deterministic post-ready event loop flush (`QCoreApplication.processEvents()`) in `AgentAppSession.start()` immediately after `wait_until(is_ui_ready)` returns.
2. **Component 2 (`pypost/agent/ui_actions.py`)**: Add `_pump()` (`QCoreApplication.processEvents()`) to `_select_tree()` before model index lookup.
3. **Component 3 (Invariant Validation)**: Confirm `UiTargetNotInteractableError` containing `"option not found"` continues to be raised cleanly.
4. **Verification**: Confirm `tests/test_agent_session_event_settle.py` transitions from RED to GREEN, followed by full parallel test suite verification (`make check`).

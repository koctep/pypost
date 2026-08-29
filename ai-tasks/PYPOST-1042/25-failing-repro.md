# Failing Repro: PYPOST-1042

## Overview

PYPOST-1042 is a contract test coverage task: the production refusal behavior in `pypost/agent/ui_actions.py:_select_tree` (`UiTargetNotInteractableError(widget_id, "tree has no model")`) already exists and is correct, but has no dedicated test asserting it.

Per `20-architecture.md` (AC-7, FR-6), Step 3 creates the mutation-evidence test suite `tests/test_ui_actions_tree_no_model_mutation.py` containing 4 evidence items that verify the contract test `test_select_tree_no_model_raises` is load-bearing.

In Step 3, the contract test has not yet been added to `tests/test_ui_actions.py`. Consequently, running the evidence suite produces 4 clean assertion failures demonstrating that the required contract test is missing.

## Executed Command

```bash
make test PYTEST_ARGS="tests/test_ui_actions_tree_no_model_mutation.py"
```

## Pytest Output (Red)

```text
INFO parallel_test_run_started workers=8 enable_coverage=False report_json= test_targets=tests/test_ui_actions_tree_no_model_mutation.py pytest_arg_count=0
[  1/1  ] tests/test_ui_actions_tree_no_model_mutation.py ... FAILED (1.42s)
INFO test_file_completed file=tests/test_ui_actions_tree_no_model_mutation.py status=failed exit_code=1 duration_seconds=1.42 progress=1/1

=================================== FAILURES ===================================
ERROR test_file_failed file=tests/test_ui_actions_tree_no_model_mutation.py exit_code=1 duration_seconds=1.42
__________ FAILURES: tests/test_ui_actions_tree_no_model_mutation.py ___________
============================= test session starts ==============================
platform linux -- Python 3.13.5, pytest-8.4.2, pluggy-1.6.0 -- /home/src/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/src
configfile: pyproject.toml
plugins: timeout-2.4.0, cov-6.3.0, anyio-4.14.2
collecting ... collected 4 items

tests/test_ui_actions_tree_no_model_mutation.py::test_repro_contract_catches_guard_removed_text_option FAILED [0ms] [ 25%]
tests/test_ui_actions_tree_no_model_mutation.py::test_repro_contract_catches_guard_removed_index_option FAILED [0ms] [ 50%]
tests/test_ui_actions_tree_no_model_mutation.py::test_repro_contract_catches_reason_reworded[by-text] FAILED [0ms] [ 75%]
tests/test_ui_actions_tree_no_model_mutation.py::test_repro_contract_catches_reason_reworded[by-index] FAILED [0ms] [100%]

=================================== FAILURES ===================================
____________ test_repro_contract_catches_guard_removed_text_option _____________
tests/test_ui_actions_tree_no_model_mutation.py:86: in test_repro_contract_catches_guard_removed_text_option
    contract_fn = _contract_test()
                  ^^^^^^^^^^^^^^^^
tests/test_ui_actions_tree_no_model_mutation.py:41: in _contract_test
    raise AssertionError(
E   AssertionError: tests/test_ui_actions.py must define test_select_tree_no_model_raises (PYPOST-1042 contract test)
---------------------------- Captured stderr setup -----------------------------
Detected locale "en_US.UTF-8" with character encoding "ANSI_X3.4-1968", which is not UTF-8.
Qt depends on a UTF-8 locale, and has switched to "en_US.UTF-8" instead.
If this causes problems, reconfigure your locale. See the locale(1) manual
for more information.
____________ test_repro_contract_catches_guard_removed_index_option ____________
tests/test_ui_actions_tree_no_model_mutation.py:99: in test_repro_contract_catches_guard_removed_index_option
    contract_fn = _contract_test()
                  ^^^^^^^^^^^^^^^^
tests/test_ui_actions_tree_no_model_mutation.py:41: in _contract_test
    raise AssertionError(
E   AssertionError: tests/test_ui_actions.py must define test_select_tree_no_model_raises (PYPOST-1042 contract test)
_____________ test_repro_contract_catches_reason_reworded[by-text] _____________
tests/test_ui_actions_tree_no_model_mutation.py:114: in test_repro_contract_catches_reason_reworded
    contract_fn = _contract_test()
                  ^^^^^^^^^^^^^^^^
tests/test_ui_actions_tree_no_model_mutation.py:41: in _contract_test
    raise AssertionError(
E   AssertionError: tests/test_ui_actions.py must define test_select_tree_no_model_raises (PYPOST-1042 contract test)
____________ test_repro_contract_catches_reason_reworded[by-index] _____________
tests/test_ui_actions_tree_no_model_mutation.py:114: in test_repro_contract_catches_reason_reworded
    contract_fn = _contract_test()
                  ^^^^^^^^^^^^^^^^
tests/test_ui_actions_tree_no_model_mutation.py:41: in _contract_test
    raise AssertionError(
E   AssertionError: tests/test_ui_actions.py must define test_select_tree_no_model_raises (PYPOST-1042 contract test)
============================= top 5 slowest tests ==============================
     0ms  tests/test_ui_actions_tree_no_model_mutation.py::test_repro_contract_catches_reason_reworded[by-index]
     0ms  tests/test_ui_actions_tree_no_model_mutation.py::test_repro_contract_catches_guard_removed_text_option
     0ms  tests/test_ui_actions_tree_no_model_mutation.py::test_repro_contract_catches_reason_reworded[by-text]
     0ms  tests/test_ui_actions_tree_no_model_mutation.py::test_repro_contract_catches_guard_removed_index_option
=========================== short test summary info ============================
FAILED [0ms] tests/test_ui_actions_tree_no_model_mutation.py::test_repro_contract_catches_guard_removed_text_option
FAILED [0ms] tests/test_ui_actions_tree_no_model_mutation.py::test_repro_contract_catches_guard_removed_index_option
FAILED [0ms] tests/test_ui_actions_tree_no_model_mutation.py::test_repro_contract_catches_reason_reworded[by-text]
FAILED [0ms] tests/test_ui_actions_tree_no_model_mutation.py::test_repro_contract_catches_reason_reworded[by-index]
============================== 4 failed in 0.11s ===============================
```

## Failure Reason Analysis

The failures occur because `_contract_test()` checks `tests.test_ui_actions.test_select_tree_no_model_raises` via `getattr` and raises `AssertionError: tests/test_ui_actions.py must define test_select_tree_no_model_raises (PYPOST-1042 contract test)`.

No production code in `pypost/` has been altered. Step 4 will introduce `test_select_tree_no_model_raises` to `tests/test_ui_actions.py`, turning both the contract test and all 4 evidence items in `tests/test_ui_actions_tree_no_model_mutation.py` GREEN.

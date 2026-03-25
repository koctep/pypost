# PYPOST-84: Architecture — ScriptExecutor patch targets class not instance

## 1. Summary

This is a **comment-only change** to `tests/test_request_service.py`. No production code is
modified. The goal is to make the `@staticmethod` contract of `ScriptExecutor.execute` explicit
at each of the four mock sites so that future refactorers are immediately aware of the
dependency.

---

## 2. Context

### 2.1 Production code contract

`pypost/core/script_executor.py:49` declares:

```python
@staticmethod
def execute(script, request, response, variables):
    ...
```

`pypost/core/request_service.py:281` calls it as a class-level static call:

```python
ScriptExecutor.execute(...)          # no instantiation
```

### 2.2 Mock pattern implications

When `unittest.mock.patch` replaces `ScriptExecutor` with a `MagicMock`, attribute access on
the mock directly reflects the class-level API:

| Production call style | Correct mock target |
|---|---|
| `ScriptExecutor.execute(...)` — `@staticmethod` | `mock_executor.execute.return_value` |
| `ScriptExecutor().execute(...)` — instance method | `mock_executor.return_value.execute.return_value` |

The current mocking approach is **functionally correct** for the existing `@staticmethod`
design. The risk is silent breakage if `execute` is ever promoted to an instance method.

---

## 3. Change Plan

### 3.1 Affected file

| File | Type of change |
|---|---|
| `tests/test_request_service.py` | Add inline comments only |

No other files are touched (FR-2).

### 3.2 Four patch sites

Each site follows this pattern:

```python
with patch("pypost.core.request_service.ScriptExecutor") as mock_executor:
    mock_executor.execute.return_value = (...)   # <-- comment goes here
```

#### Site 1 — line 64 (`test_execute_post_script_populates_logs_and_variables`)

```python
# ScriptExecutor.execute is a @staticmethod, so mock_executor.execute (not
# mock_executor.return_value.execute) is the correct target. If execute is ever
# converted to an instance method, change this to:
#   mock_executor.return_value.execute.return_value = (...)
mock_executor.execute.return_value = ({"x": 1}, ["log"], None)
```

#### Site 2 — line 72 (`test_execute_post_script_error_sets_script_error_field`)

```python
# ScriptExecutor.execute is a @staticmethod, so mock_executor.execute (not
# mock_executor.return_value.execute) is the correct target. If execute is ever
# converted to an instance method, change this to:
#   mock_executor.return_value.execute.return_value = (...)
mock_executor.execute.return_value = ({}, [], "SyntaxError")
```

#### Site 3 — line 217 (`test_script_error_populates_execution_error_script_category`)

```python
# ScriptExecutor.execute is a @staticmethod, so mock_executor.execute (not
# mock_executor.return_value.execute) is the correct target. If execute is ever
# converted to an instance method, change this to:
#   mock_executor.return_value.execute.return_value = (...)
mock_executor.execute.return_value = ({}, [], "NameError: x not defined")
```

#### Site 4 — line 237 (`test_script_error_tracks_metrics`)

```python
# ScriptExecutor.execute is a @staticmethod, so mock_executor.execute (not
# mock_executor.return_value.execute) is the correct target. If execute is ever
# converted to an instance method, change this to:
#   mock_executor.return_value.execute.return_value = (...)
mock_executor.execute.return_value = ({}, [], "err")
```

### 3.3 Comment wording rationale

The three-line comment is intentionally identical at all four sites so that:

1. A text search for `return_value.execute` will surface all four locations at once when the
   instance-method refactor is eventually done.
2. The comment is self-contained — it explains _why_ the current form is correct and _what_
   must change if the contract changes.

---

## 4. Verification

```
make test
```

Expected outcome: all existing tests pass, 0 failures, 0 errors. Coverage threshold (50%) is
unaffected because no executable code is changed.

---

## 5. Acceptance Criteria Mapping

| AC | Criterion | How satisfied |
|---|---|---|
| AC-1 | All four `mock_executor.execute.return_value` lines have an adjacent comment. | Three-line comment inserted immediately above each of the four assignment lines. |
| AC-2 | Comment states what must change if `execute` becomes an instance method. | Comment explicitly says `mock_executor.return_value.execute.return_value`. |
| AC-3 | `make test` passes with 0 failures and 0 errors. | No executable code is modified; test behaviour is unchanged. |
| AC-4 | No changes outside `tests/test_request_service.py`. | Only one file is touched. |

---

## 6. Out of Scope (unchanged from requirements)

- Converting `ScriptExecutor.execute` from `@staticmethod` to an instance method.
- Changing any mock to use `return_value.execute`.
- Modifying any production code.
- Adding `FakeScriptExecutor` or other test helpers.

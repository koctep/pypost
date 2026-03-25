# PYPOST-84: Requirements — ScriptExecutor patch targets class not instance

## 1. Background

Tech-debt item raised in `ai-tasks/PYPOST-52/60-review.md` (severity: MEDIUM).

`tests/test_request_service.py` patches `ScriptExecutor` in four places using:

```python
with patch("pypost.core.request_service.ScriptExecutor") as mock_executor:
    mock_executor.execute.return_value = (...)
```

The review noted that if `RequestService` ever calls `ScriptExecutor().execute(...)` (instance
call), the correct target would be `mock_executor.return_value.execute.return_value`, not
`mock_executor.execute`. The lack of any comment making the current contract explicit is the
source of confusion and carries refactoring risk.

## 2. Current State (verified by code inspection)

| Location | Finding |
|---|---|
| `pypost/core/script_executor.py:49` | `execute` is decorated `@staticmethod` |
| `pypost/core/request_service.py:281` | Called as `ScriptExecutor.execute(...)` — class-level, no instantiation |
| `tests/test_request_service.py:63–64` | `mock_executor.execute.return_value` — no explanatory comment |
| `tests/test_request_service.py:71–72` | `mock_executor.execute.return_value` — no explanatory comment |
| `tests/test_request_service.py:216–217` | `mock_executor.execute.return_value` — no explanatory comment |
| `tests/test_request_service.py:236–237` | `mock_executor.execute.return_value` — no explanatory comment |

**Conclusion**: The current mock approach is **functionally correct** today. The risk is
forward-looking: if `execute` is converted from `@staticmethod` to an instance method during
the PYPOST-43–51 refactoring, all four mock sites will silently produce wrong test behaviour
(the mock will appear to work but will not intercept the actual call path).

## 3. Fix Scope Decision

The fix is a **comment-only clarification** at each of the four patch sites. A full mock
refactor to `return_value.execute` is **not required** at this time because:

1. `@staticmethod` is the intended design (no instance state is needed for script execution).
2. Changing to `return_value.execute` without changing production code would make the tests
   incorrect.
3. If `execute` is ever converted to an instance method, that change will be owned by the
   PYPOST-43–51 task, which must then also update these mock sites.

A comment must be added so that any future refactorer is immediately aware of the dependency.

## 4. Functional Requirements

### FR-1 — Add clarifying comment at each mock site

Each of the four `with patch(...)` blocks must have an inline comment on or immediately above
the `mock_executor.execute.return_value = (...)` line explaining:

- That `execute` is a `@staticmethod` on the real class.
- That this is why `mock_executor.execute` (not `mock_executor.return_value.execute`) is the
  correct target.
- That if `execute` is ever changed to an instance method, this line must be updated to
  `mock_executor.return_value.execute.return_value`.

### FR-2 — No production code changes

`pypost/core/script_executor.py` and `pypost/core/request_service.py` must **not** be
modified. This is a test-only change.

### FR-3 — All existing tests must continue to pass

`make test` (or equivalent) must report 0 failures after the change.

### FR-4 — No new tests required

The fix does not change behaviour; it only adds documentation. No new test cases are needed.

## 5. Affected Files

| File | Change |
|---|---|
| `tests/test_request_service.py` | Add inline comments at lines 64, 72, 217, 237 |

## 6. Out of Scope

- Converting `ScriptExecutor.execute` from `@staticmethod` to an instance method.
- Changing any mock to use `return_value.execute`.
- Modifying any production code.
- Adding `FakeScriptExecutor` or other test helpers.

## 7. Acceptance Criteria

| # | Criterion |
|---|---|
| AC-1 | All four `mock_executor.execute.return_value` lines have an adjacent comment explaining the `@staticmethod` contract. |
| AC-2 | The comment explicitly states what must change if `execute` becomes an instance method. |
| AC-3 | `make test` passes with 0 failures and 0 errors. |
| AC-4 | No changes to any file outside `tests/test_request_service.py`. |

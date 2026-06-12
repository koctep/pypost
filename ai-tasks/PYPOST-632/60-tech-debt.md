# PYPOST-632: Technical Debt Analysis

## Evaluation outcome

**Keep `isalnum()` policy** — do not switch to `str.isidentifier()`.

| Case | `isalnum()` policy | `isidentifier()` |
| --- | --- | --- |
| `x²` | Accept | Reject |
| NFD `naïve` (decomposed) | Reject combining marks | Accept (Python NFKC rules) |
| NFC `café` | Accept | Accept |

Rationale: PyPost intentionally allows some Unicode letter+digit forms that Jinja tokenization
would reject, while still rejecting combining marks and emoji via per-character `isalnum()`.
Switching to `isidentifier()` would reject names like `x²` without user benefit.

Regression tests: `TestIsidentifierDivergencePYPOST632` in `tests/test_variable_name_validation.py`.

## Blocker Review Verdict

**SAFE TO CLOSE**

## Follow-up Tasks

None.

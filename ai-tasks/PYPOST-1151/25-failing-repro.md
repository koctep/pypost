# Step 3 Failing Repro: Template Expression Tokenizer Whitespace Rejection

**Task**: [PYPOST-1151](https://pypost.atlassian.net/browse/PYPOST-1151)  
**Step**: STEP 3 (Failing Repro Test)  
**Target Test Node**: `tests/test_template_expression_tokenizer.py::TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside`  
**Test File**: `tests/test_template_expression_tokenizer.py`

---

## 1. Overview & Context

This task addresses a pre-existing test failure recorded during PYPOST-1149 technical debt tracking (`ai-tasks/PYPOST-1149/60-tech-debt.md`):

> `TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside`: `is_plain_variable_token("{{ host }}")` returns `True`; test expects `False` for whitespace inside delimiters.

In subsequent architectural refinement (PYPOST-1176), the regex patterns and helper functions in `pypost/core/template_expression_tokenizer.py` were split:
- `PLAIN_VARIABLE_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")`: strictly rejects inner whitespace and only matches exact `{{name}}` tokens.
- `LOOSE_PLAIN_VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")`: permits surrounding whitespace inside delimiters for hover lookup.
- `TEMPLATE_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*(.*?)\s*\}\}")`: general non-greedy template placeholder extraction.

Corresponding helper functions:
- `is_plain_variable_token(token)`: uses `PLAIN_VARIABLE_PATTERN.fullmatch`.
- `extract_plain_variable_name(token)`: uses `PLAIN_VARIABLE_PATTERN.fullmatch`.
- `is_loose_plain_variable_token(token)`: uses `LOOSE_PLAIN_VARIABLE_PATTERN.fullmatch`.
- `extract_loose_plain_variable_name(token)`: uses `LOOSE_PLAIN_VARIABLE_PATTERN.fullmatch`.

---

## 2. Test Execution Command

Executed strictly via Make per repository guidelines (`AGENTS.md`):

```bash
make test PYTEST_ARGS="tests/test_template_expression_tokenizer.py -v"
```

---

## 3. Repro & Verification Test Results

### Test Execution Output

```text
INFO parallel_test_run_started workers=8 enable_coverage=False report_json= test_targets=tests/test_template_expression_tokenizer.py pytest_arg_count=1
[  1/1  ] tests/test_template_expression_tokenizer.py ... PASSED (1.28s)
INFO test_file_completed file=tests/test_template_expression_tokenizer.py status=passed exit_code=0 duration_seconds=1.28 progress=1/1

============================== TOP 5 SLOWEST FILES ==============================
1. tests/test_template_expression_tokenizer.py (1.28s)
NOTICE slowest_test_file rank=1 file=tests/test_template_expression_tokenizer.py duration_seconds=1.28

=================================== SUMMARY ====================================
Total Files: 1 | Passed: 1 | Failed: 0 | Skipped: 0
Wall-clock duration: 1.28s | Cumulative CPU duration: 1.28s (1.0x speedup)
INFO parallel_test_run_completed total_files=1 passed=1 failed=0 skipped=0 wall_clock_seconds=1.28 cumulative_duration_seconds=1.28 speedup=1.0
```

### Target Test Node Details

```python
class TestPlainVariablePattern(unittest.TestCase):
    def test_plain_pattern_matches_simple_name(self):
        self.assertTrue(is_plain_variable_token("{{host}}"))
        self.assertEqual(extract_plain_variable_name("{{host}}"), "host")

    def test_plain_pattern_rejects_whitespace_inside(self):
        self.assertFalse(is_plain_variable_token("{{ host }}"))
        self.assertIsNone(extract_plain_variable_name("{{ host }}"))
```

---

## 4. Analysis & Behavioral Verification

| Behavior Under Test | Input Token | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| `is_plain_variable_token` | `"{{host}}"` | `True` | `True` | PASS |
| `extract_plain_variable_name` | `"{{host}}"` | `"host"` | `"host"` | PASS |
| `is_plain_variable_token` | `"{{ host }}"` | `False` | `False` | PASS |
| `extract_plain_variable_name` | `"{{ host }}"` | `None` | `None` | PASS |
| `is_plain_variable_token` | `"{{urlencode(db)}}"` | `False` | `False` | PASS |
| `extract_plain_variable_name` | `"{{urlencode(db)}}"` | `None` | `None` | PASS |

### Findings:
1. The historical defect documented in `ai-tasks/PYPOST-1149/60-tech-debt.md` where `is_plain_variable_token("{{ host }}")` returned `True` has already been resolved by `PLAIN_VARIABLE_PATTERN` (`r"\{\{([a-zA-Z0-9_]+)\}\}"`).
2. The target test node `tests/test_template_expression_tokenizer.py::TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside` passes cleanly and verifies that internal whitespace is strictly rejected for plain variable tokens.
3. No production code modifications were made during this step.
4. In Step 4 (Development), additional whitespace variation assertions (such as leading/trailing space asymmetry like `{{ host}}` and `{{host }}`) will be formally verified and locked in the test suite.

---

## 5. Strict Constraints Verification

- **No Production Code Changes**: No files under `pypost/` were modified.
- **Make-Only Execution**: Tests executed exclusively via `make test`.
- **Hermetic & Bounded**: Module has `pytestmark = pytest.mark.timeout(30)` and runs in ~1.28s.

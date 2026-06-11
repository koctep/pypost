# PYPOST-279: Pytest Exit Code 5 Policy Documentation

## Overview

This task addresses the policy for pytest exit code `5` (no tests collected) in empty-test
repositories. In mature repositories, exit code `5` is treated as a hard failure in `make test` and
CI to prevent silent bypasses of the test suite due to misconfiguration or accidental file
deletions. However, in empty-test repositories or newly initialized projects, this can cause
false-positive build failures.

To resolve this, PyPost introduced support for the `empty_tests_policy` setting, allowing
developers to configure whether a test run with no collected tests is treated as a failure or
a warning.

## Architecture

PyPost customizes pytest's exit behavior by implementing hooks in `tests/conftest.py`:

1. **Option Registration**:
   In `pytest_addoption(parser)`, the custom configuration option `empty_tests_policy` is
   registered with a default value of `"fail"`:
   ```python
   parser.addini(
       "empty_tests_policy",
       help="Policy for pytest exit code 5 (no tests collected): 'fail' or 'warn'",
       default="fail",
   )
   ```

2. **Exit Code Interception**:
   In `pytest_sessionfinish(session, exitstatus)`, PyPost intercepts the session finish event.
   If the exit status is `5` (which indicates no tests were collected), it retrieves the configured
   policy using `session.config.getini("empty_tests_policy")`. If the policy is set to `"warn"`,
   `"warning"`, or `"ignore_and_warn"`, PyPost rewrites `session.exitstatus` to `0` (success),
   prints a warning message to `sys.stderr`, and logs a warning using the `"pytest"` logger.

## Configuration

The exit code policy can be configured using the custom `empty_tests_policy` option in either
`pytest.ini` or `pyproject.toml`.

### Supported Values

- `fail` (default): Exit code `5` is propagated natively, resulting in a test run failure. This
  retains strict safety guardrails.
- `warn` / `warning` / `ignore_and_warn`: Intercepts exit code `5` and rewrites the session exit
  status to `0` (success). It also writes a clear warning message to stderr and logs a warning
  to the `"pytest"` logger.

### Examples

**In `pytest.ini`:**

```ini
[pytest]
empty_tests_policy = warn
```

**In `pyproject.toml`:**

```toml
[tool.pytest.ini_options]
empty_tests_policy = "warn"
```

## Testing

Regression coverage for this policy is implemented in `tests/test_pytest_exit_policy.py`. It
verifies:

1. **Native Pytest Behavior**: Ensures pytest naturally exits with code `5` when no tests are
   collected in an empty directory.
2. **Makefile Propagation**: Ensures that `make test` correctly propagates exit code `5` as a
   failure by default.
3. **Warn Policy Verification**: Simulates `empty_tests_policy = warn` and asserts that the exit
   code is rewritten to `0` and the warning message is output to stderr.
4. **Fail Policy Verification**: Simulates `empty_tests_policy = fail` and asserts that the exit
   code remains `5`.

To run the exit code policy tests locally:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_pytest_exit_policy.py -v
```

## Troubleshooting

### Issue: `empty_tests_policy` setting is ignored

**Symptom**:
Pytest still exits with status `5` even though `empty_tests_policy` is configured to `warn`.

**Solutions**:
1. **Check Configuration Location**: Ensure the setting is placed under the correct section.
   - For `pytest.ini`, it must be in the `[pytest]` section.
   - For `pyproject.toml`, it must be in the `[tool.pytest.ini_options]` section.
2. **Check Policy Value**: Ensure the value is one of `warn`, `warning`, or `ignore_and_warn`.
   Other values (such as `fail` or typo-ridden values) will default to the `fail` policy.
3. **Check pytest.ini Overrides**: Ensure that another configuration file is not overriding your
   settings (e.g., passing `-c` to pytest).

### Issue: `conftest.py` import errors when GUI packages are missing

**Symptom**:
Running pytest fails immediately with `ImportError` or `ModuleNotFoundError` related to `PySide6`
or other GUI dependencies.

**Solutions**:
1. **Virtual Environment Activation**: Ensure you are running pytest from the correct virtual
   environment where dependencies are installed:
   ```bash
   source .venv/bin/activate
   ```
2. **Install Dependencies**: Run `make install` or `pip install -r requirements.txt` to ensure
   all required packages, including `PySide6`, are fully installed.
3. **Offscreen Platform Config**: PyPost sets `QT_QPA_PLATFORM=offscreen` in `tests/conftest.py`
   to allow headless test execution. If running tests in environments without a display server
   (like CI), ensure this environment variable is set or that conftest.py is loaded correctly.


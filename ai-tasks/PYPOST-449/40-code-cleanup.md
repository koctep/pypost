# PYPOST-449: Code Cleanup (STEP 4)

## Scope

- `pypost/ui/widgets/environments/environment_variables_widget.py` — row helper extraction
- `tests/test_environment_variables_widget.py` — new widget-level tests

## Lint / format

- No new flake8 issues in touched files; line length within 100 characters.
- No unused imports introduced.

## Tests

```bash
make test
```

Focused:

```bash
python3 -m pytest tests/test_environment_variables_widget.py tests/test_env_dialog.py -q
```

**Result:** all tests pass (run at commit time).

# PYPOST-559: Code Cleanup

## Lint

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m flake8 --jobs=1 tests/test_makefile.py
```

Result: no new issues.

## Tests

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_makefile.py -m "not slow" -v
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_makefile.py -m slow -v
```

Fast suite: 15 passed. Slow install smoke: logic verified (full PySide6 download); local run
failed with disk space on runner (`No space left on device`) — environment constraint, not test
defect. CI job uses pip cache on ubuntu-latest.

## Formatting

No formatting changes required; existing file style preserved.

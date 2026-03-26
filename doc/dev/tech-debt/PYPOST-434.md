# Technical Debt — PYPOST-434 (pytest / CI hygiene)

This bugfix added `pythonpath = .` to `pytest.ini`.  No new code debt was introduced.
Track optional follow-ups here.

## 1. CI lint gate

`flake8` is installed in `.github/workflows/test.yml` but not executed.  Either add a lint
step or remove the package from the install line.  The codebase currently has many flake8
findings; a dedicated ticket should scope fixes or a phased rollout.

## 2. Qt deprecation warnings

`pypost/ui/widgets/mixins.py` uses deprecated `QMouseEvent.globalPos()`, which produces
pytest warning noise.  Update to the current Qt API in a UI-focused ticket.

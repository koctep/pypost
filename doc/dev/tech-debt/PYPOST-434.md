# Technical Debt — PYPOST-434 (pytest / CI hygiene)

Pytest configuration and dependency metadata now live in `pyproject.toml`. Track optional
follow-ups here.

## 1. CI lint gate

Ruff is installed through the `dev` dependency group but is not executed in CI. The codebase has
existing lint findings; a dedicated ticket should scope fixes before enabling a required lint gate.

## 2. Qt deprecation warnings

`pypost/ui/widgets/mixins.py` uses deprecated `QMouseEvent.globalPos()`, which produces
pytest warning noise.  Update to the current Qt API in a UI-focused ticket.

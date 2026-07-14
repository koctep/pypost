# PYPOST-788: Code Cleanup

## Lint

- Documentation-only change; no Python source modified.
- `make lint` — unchanged (no new flake8 issues).

## Formatting

- Markdown tables aligned with existing `setup.md` style.
- Line length ≤ 100 characters per project rules.

## Test results

- `make check` — lint + fast test suite (no regressions expected).

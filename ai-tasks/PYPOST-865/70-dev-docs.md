# PYPOST-865: Developer Documentation

## Summary

Documented the enabled `--strict-markers` policy in the existing pytest
reference. No new `doc/dev/` file was required — `testing.md` already owns
timeouts and marker guidance; this step completes the strict-markers section
against the architecture decision (enable, not defer).

## Changes

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | § Strict markers (PYPOST-865) completed vs architecture |
| `ai-tasks/PYPOST-865/70-dev-docs.md` | This artifact |

No user-facing docs (developer / test-config only).

## Structure covered

- **Overview** — `--strict-markers` in default `addopts`; unknown marks fail collection
- **Architecture** — single source in `pyproject.toml`; CI inherits (no workflow flag)
- **Usage** — register new custom marks with the change that introduces them
- **Configuration** — registered markers: `timeout`, `slow`, `agent_e2e`
- **Troubleshooting** — unknown-marker usage errors; guard-test drift

## Key developer guidance

1. Keep `"--strict-markers"` in `[tool.pytest.ini_options]` `addopts`.
2. Register every new custom marker under `markers` in the same PR.
3. Do not add a duplicate `--strict-markers` flag in `.github/workflows/`.
4. Verify with:
   `make test PYTEST_ARGS="tests/test_pytest_strict_markers.py -v"`.

## Validation

- [x] `doc/dev/testing.md` documents strict-markers policy vs architecture
- [x] Artifact `70-dev-docs.md` created
- [x] Roadmap STEP 8 marked complete

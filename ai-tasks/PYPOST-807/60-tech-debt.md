# PYPOST-807: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

- `test.yml` job summary `THRESHOLD=70` remains a hardcoded mirror of `addopts` in
  `pyproject.toml` (same pattern as former `pytest.ini` sync documented in PYPOST-88).
- `pythonpath = "."` kept as a fallback despite editable install (PYPOST-806); harmless for
  installed workflows.

## Code Quality Issues

None blocking. Single config consolidation with no behavior change.

## Missing Tests

- No dedicated test asserts pytest reads `[tool.pytest.ini_options]` from `pyproject.toml`
  (full suite passing is sufficient regression signal).

## Performance Concerns

None. Config discovery path change only.

## Follow-up Tasks

None. Resolves PYPOST-785 follow-up item "Migrate pytest config to pyproject.toml".

# PYPOST-839: Technical Debt Analysis

## Shortcuts Taken

- Agent e2e module set is an **explicit Makefile file list**, not a pytest
  marker — avoids touching every sibling test for packaging alone.
- `make check` does **not** depend on `test-agent-e2e` (modules already under
  `make test`); focused target only.
- CI workflow files were not changed; maintainers/agents use the make target
  locally and CI still covers the same tests via the full fast suite.
- Umbrella doc is a facade (links + run guide), not a second full API reference
  for each capability.

## Code Quality Issues

- Makefile `##` help line for `test-agent-e2e` is long (readable in
  `make help`, but denser than shorter targets).
- Future goldens must be manually appended to the Makefile list (documented in
  `agent_e2e.md`); easy to forget without a marker or scripted discovery.

## Missing Tests

- No dedicated Makefile integration assertion that `test-agent-e2e` appears in
  `make help` / runs the expected file list (optional; `test_makefile.py`
  already checks help is non-empty).
- No new product scenarios (by design — packaging only).

## Performance Concerns

- Focused target still launches multiple GUI sessions across modules (~8s
  locally for 27 tests). Acceptable for harness packaging; not a regression
  vs running the same files under `make test`.

## Follow-up Tasks

Jira: [PYPOST-854](https://pypost.atlassian.net/browse/PYPOST-854)

| ID | Priority | Summary | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Optional `@pytest.mark.agent_e2e` + marker-based make target | Reduces manual Makefile list maintenance |
| TD-2 | Low | Optional `test_makefile.py` smoke for `test-agent-e2e` help/prereqs | Parity with other make target tests |
| TD-3 | Low | Optional CI job/step that runs `make test-agent-e2e` alone | Faster signal when only agent stack changes; not required for AC |

No blockers relative to acceptance criteria. Packaging (umbrella doc + make
target + cross-links) is complete; debt is optional ergonomics.

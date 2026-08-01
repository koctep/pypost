# PYPOST-943: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Restored the slow Makefile install smoke seed contract so isolated workspaces
satisfy setuptools dynamic metadata from committed `pyproject.toml`. Changes are
test helpers and a fast seed-contract guard only — no application or CI workflow
edits. Items below are non-blocking follow-ups for Phase D / blocker review.
**Do not create Jira tickets in this step** — Phase D fills the Jira column later.

## Shortcuts Taken

- **Minimal installable tree, not a full package mirror.** `_seed_installable_package`
  copies only `pypost/version.py` and `README.md` atop the existing stub
  `pypost/__init__.py` from `_seed_minimal_project`. Sufficient for current
  `pyproject.toml`; does not materialize the full `pypost/` tree (TD-1).
- **Seed contract derives only version attr + readme paths.** Architecture accepted
  partial package discovery (`pypost/__init__.py` stub) because setuptools
  `packages.find` succeeds with an empty package; future dynamic metadata fields
  are not yet encoded in the contract parser (TD-2).
- **Contract test duplicates fixture assembly.** `_materialize_slow_smoke_seed`
  mirrors `make_workspace_full_deps` (Makefile + pyproject + seed) instead of
  invoking the pytest fixture directly — keeps the contract test free of slow
  marker scope but creates a two-place update surface (TD-3).
- **Post-install sanity unchanged from PYPOST-559.** Slow smoke still imports
  `pydantic` only, not `pypost`, to avoid Qt/system deps in the smoke path (TD-4).
- **Did not chase incidental CI annotations.** Pip cache HTTP 400 restore warning
  and Node.js 20 deprecation on the failing run are confirmed noise per Step 2
  classification; no workflow change required for closure.

## Code Quality Issues

- **Two helpers for the same workspace shape:** `make_workspace_full_deps` (fixture)
  and `_materialize_slow_smoke_seed` (contract test) must stay aligned when the
  slow-smoke seed steps change (TD-3).
- **`_required_seed_paths_from_pyproject` is intentionally narrow.** It parses
  `project.dynamic` / `[tool.setuptools.dynamic] version.attr` and `project.readme`
  only; no shared utility with other packaging contract tests if more land (TD-2).
- **No product Python under `pypost/` changed.** Naming and structure debt in
  application modules is unchanged.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Isolated `make install` with real `pyproject.toml` (slow smoke) | Covered — `TestSlowInstallSmoke` |
| Seed includes dynamic version + readme artifacts (fast contract) | Covered — `test_slow_smoke_seed_includes_pyproject_packaging_artifacts` |
| Explicit timeout markers on changed modules | Covered — module/class marks present; **no timeout blockers** |
| Future dynamic metadata (license-files, scripts, package-data) | Not covered — contract parser would need extension (TD-2) |
| Post-install `import pypost` in isolated workspace | Not covered — inherited pydantic-only check (TD-4) |
| Live GitHub Actions `make-install-smoke` green proof | CI job is the integration signal; not duplicated in pytest |
| Full `make check` including `test_verify_ai_task_artifacts` baseline | Baseline mismatch (257 vs 259) until Step 8 artifacts complete (TD-5) |

## Performance Concerns

None introduced for the product. Operator note: slow smoke remains network-heavy
(roughly 1–3 minutes with pip cache on cold runners) by design (PYPOST-559 NFR2).
The fast seed-contract test adds negligible cost to the default matrix.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Document or assert minimum `pypost/` tree policy for slow-smoke seed (stub `__init__.py` vs fuller mirror) | Today implicit; only breaks if packaging requires modules beyond version/readme | [PYPOST-963](https://pypost.atlassian.net/browse/PYPOST-963) |
| TD-2 | Low | Extend `_required_seed_paths_from_pyproject` when `pyproject.toml` gains additional dynamic/install-time paths (license-files, scripts, package-data) | Fast guard should lead slow smoke, not lag metadata changes | [PYPOST-964](https://pypost.atlassian.net/browse/PYPOST-964) |
| TD-3 | Low | Deduplicate slow-smoke workspace assembly: share one helper between `make_workspace_full_deps` and the seed-contract test | Reduces drift if Makefile copy or seed order changes | [PYPOST-965](https://pypost.atlassian.net/browse/PYPOST-965) |
| TD-4 | Lowest | Optionally add post-install `import pypost` (or version attr read) to slow smoke after install | Inherited pydantic-only check from PYPOST-559; would tighten FR3 without Qt import | [PYPOST-966](https://pypost.atlassian.net/browse/PYPOST-966) |
| TD-5 | Low | Refresh `test_verify_ai_task_artifacts` baseline after Step 8 dev docs land | Expected transient gap during in-flight task (40-code-cleanup § Validation) | [PYPOST-967](https://pypost.atlassian.net/browse/PYPOST-967) |

### Planned this ticket (not separate Debt)

- Step 8: note in `doc/dev/testing.md` that slow smoke isolated workspace seed must
  mirror committed packaging metadata (dynamic version attr, readme), not only
  dependency pins — per architecture Implementation Plan item 5.

### Already tracked / do not reticket from this file alone

| Area | Owner / note |
| --- | --- |
| Slow smoke job design + pydantic import sanity | [PYPOST-559](https://pypost.atlassian.net/browse/PYPOST-559) |
| Real `pyproject.toml` in slow fixture | [PYPOST-806](https://pypost.atlassian.net/browse/PYPOST-806) |
| Dynamic version attr trigger | [PYPOST-808](https://pypost.atlassian.net/browse/PYPOST-808) |
| Smoke job Qt/EGL apt parity | [PYPOST-923](https://pypost.atlassian.net/browse/PYPOST-923) |

## User documentation

N/A for end-user `doc/user/` — CI / test-contract hygiene only. Developer doc
touch deferred to Step 8 (`doc/dev/testing.md`).

## Blocker review

**No blockers.** All tests in changed modules declare explicit `pytest.mark.timeout`
markers. Root cause classified as deterministic test-contract gap; fix aligns seed
with PYPOST-808 packaging metadata. Fast contract test catches future drift without
waiting for network-heavy slow smoke. Safe to proceed to Step 8; Phase D may ticket
Low/Lowest follow-ups after blocker review.

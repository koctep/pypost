# PYPOST-964: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Extended the slow-smoke seed-contract parser and aligned `_seed_installable_package` with
scripts, license-files, and package-data paths. Changes are test helpers and dev docs only.

## Shortcuts Taken

- **Script modules are stubs, not repo copies.** Entry-point targets get minimal `main()`
  stubs; full `pypost/agent/` tree is not mirrored (intentional PYPOST-963 policy).
- **Package-data resolution scans repo globs at test time.** If a glob matches no files, no
  paths are required — seed is not pre-populated for hypothetical future globs until files
  exist in the repo.
- **Parser and seed still duplicate workspace assembly with contract test** — PYPOST-965.

## Code Quality Issues

- `_materialize_slow_smoke_seed` in contract test still mirrors fixture steps manually (965).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Script entry-point module paths in parser | Covered |
| License-files + package-data parser (synthetic pyproject) | Covered |
| Full artifact presence after seed | Covered |
| Live slow smoke after script stubs | Inherited — no behavior change expected |
| Dynamic license-files via `[tool.setuptools.dynamic]` | Parser handles list form; no committed case yet |

## Performance Concerns

None — negligible filesystem work in fast contract tests.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| — | — | None new | Parent PYPOST-943 follow-ups (965–967) remain tracked there | — |

## Blocker review

**No blockers.** Parser, seed, policy constant, and contract tests aligned. Safe to close.

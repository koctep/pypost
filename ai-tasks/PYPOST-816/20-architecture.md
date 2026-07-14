# PYPOST-816: Architecture

## Problem

`doc/dev/setup.md` (PYPOST-772) documents seven- and eight-file ai-tasks standards, but
enforcement is manual. ~257 completed legacy folders predate the standard and lack one or more
required files.

## Components

| Component | Role |
| --- | --- |
| `scripts/verify_ai_task_artifacts.py` | Scan completed tasks; compare violations to baseline |
| `ai-tasks-artifacts-baseline.json` | Frozen map of legacy task → missing required files |
| `Makefile` `verify-ai-tasks` | Developer/CI entry point |
| `tests/test_verify_ai_task_artifacts.py` | Parsing, collection, and baseline parity tests |

## Roadmap completion detection

1. **Collapsed closure:** top-level `- [x] STEP 1–7` (en dash or hyphen) counts as all steps done.
2. **Explicit steps:** top-level `- [x] **STEP N:` lines for N=1..7 must all be `[x]`.
3. Indented sub-items under STEP 3 are ignored for completion.

## Required file sets

- **Standard (7 files):** `00-roadmap.md` through `70-dev-docs.md` per setup.md table (Steps 1–7).
- **Code Audit (8 files):** same set plus `30-audit-report.md` for PYPOST-684–689.

## Baseline gate

```
make verify-ai-tasks
  └─ scripts/verify_ai_task_artifacts.py
       └─ collect violations for completed tasks
       └─ compare task → missing-files map vs ai-tasks-artifacts-baseline.json
```

- **Pass:** current violations exactly match the committed baseline.
- **Fail:** new incomplete closed task, removed legacy gap without baseline refresh, or changed
  missing-file set for a grandfathered task.
- **Refresh:** `python scripts/verify_ai_task_artifacts.py --update-baseline` after intentional
  legacy backfill or baseline adjustment.

## Verification

- `make verify-ai-tasks` — pass with committed baseline.
- `make check` — lint, tests, and artifact verifier all pass.

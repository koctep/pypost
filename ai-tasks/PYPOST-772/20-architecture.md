# PYPOST-772: Architecture

## Approach

Documentation-only change. No application code.

## Target edit

Add `## ai-tasks artifact expectations` to `doc/dev/setup.md` before `## Troubleshooting`.

Content structure:

1. **Standard closed task (7 files)** — top-down workflow artifacts tied to Steps 1–7.
2. **Code Audit 8-file standard** — adds `30-audit-report.md` (PYPOST-684–689 pattern).
3. **Legacy exceptions** — roadmap-only stubs, alternate debt filenames, supplemental reports.
4. **Cross-links** — roadmap template, tech debt inventory, documentation audit metrics.

## Placement rationale

`setup.md` is the first developer doc many contributors open after `make install`. PYPOST-690
recommended `setup.md` or the top-down workflow doc; `setup.md` keeps onboarding and workflow
expectations in one place.

## Out of scope

- `scripts/verify_ai_task_artifacts.py` or CI enforcement (deferred follow-up).
- Backfilling 76 historical folders missing `60-tech-debt.md`.
- Updating `documentation_audit.md` metrics table (snapshot from PYPOST-690).

## Verification

- `rg 'ai-tasks artifact expectations' doc/dev/setup.md` returns the new heading.
- `make check` passes.

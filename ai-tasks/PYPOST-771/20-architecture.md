# PYPOST-771: Architecture

## Approach

Documentation-only change. No application code.

## Target edit

Expand the existing `### Tech debt` block in `doc/dev/README.md`:

1. Keep `[Tech Debt Inventory](tech_debt_inventory.md)` as the first entry.
2. Replace the generic `tech-debt/` directory bullet with eight numbered links — one per
   `doc/dev/tech-debt/PYPOST-*.md` file present in the repo.

## File inventory

| File | TOC label |
| --- | --- |
| `tech-debt/PYPOST-10.md` | Post-request Scripts Tech Debt (PYPOST-10) |
| `tech-debt/PYPOST-11.md` | Settings and Hotkeys Tech Debt (PYPOST-11) |
| `tech-debt/PYPOST-21.md` | Template Service Tech Debt (PYPOST-21) |
| `tech-debt/PYPOST-25.md` | Variable Validation Tech Debt (PYPOST-25) |
| `tech-debt/PYPOST-40.md` | SOLID Audit Tech Debt (PYPOST-40) |
| `tech-debt/PYPOST-431.md` | Qt Mouse Event API Tech Debt (PYPOST-431) |
| `tech-debt/PYPOST-434.md` | Pytest and CI Hygiene Tech Debt (PYPOST-434) |
| `tech-debt/PYPOST-463.md` | History-recording Helper Tech Debt (PYPOST-463) |

## Rationale

- Numbered list matches other TOC sections (Setup, Audits, etc.).
- Descriptive labels include PYPOST IDs for cross-reference with Jira and audit reports.
- Relative paths resolve from `doc/dev/README.md`.

## Out of scope

- Regenerating `tech_debt_inventory.md` or editing debt page content.
- Root `README.md` changes (PYPOST-770).

## Verification

- `rg 'tech-debt/PYPOST-' doc/dev/README.md` returns eight matches.
- `make check` passes.

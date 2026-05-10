# Verification of Closed Jira Tickets vs AI Reports

Date: 2026-03-27

## Scope and method

- Source of truth for closed tickets: Jira project `PYPOST`, `statusCategory = Done`.
- Query strategy: range-based JQL by key intervals plus targeted query for `PYPOST-401..450`
  to avoid MCP pagination duplicates.
- Closed tickets collected: **96** keys.
- Verification sources:
  - ticket folders in `ai-tasks/PYPOST-*`;
  - key mentions in sprint reports under `ai-sprints/**/*.md`.

## Coverage summary

| Category | Count |
| --- | ---: |
| Closed in Jira | 96 |
| Found in `ai-tasks` | 67 |
| Mentioned in `ai-sprints` | 65 |
| Found in both (`ai-tasks` + `ai-sprints`) | 41 |
| Only in `ai-tasks` | 26 |
| Only in `ai-sprints` | 24 |
| Found in neither | 5 |

## Found in neither report source (requires follow-up)

- `PYPOST-377`
- `PYPOST-379`
- `PYPOST-380`
- `PYPOST-384`
- `PYPOST-438`

## Found only in `ai-tasks` (not referenced in `ai-sprints`)

- `PYPOST-2`
- `PYPOST-17`
- `PYPOST-18`
- `PYPOST-19`
- `PYPOST-20`
- `PYPOST-21`
- `PYPOST-22`
- `PYPOST-23`
- `PYPOST-24`
- `PYPOST-25`
- `PYPOST-26`
- `PYPOST-27`
- `PYPOST-28`
- `PYPOST-29`
- `PYPOST-30`
- `PYPOST-31`
- `PYPOST-32`
- `PYPOST-33`
- `PYPOST-34`
- `PYPOST-35`
- `PYPOST-36`
- `PYPOST-38`
- `PYPOST-39`
- `PYPOST-45`
- `PYPOST-53`
- `PYPOST-434`

## Found only in `ai-sprints` (no ticket folder in `ai-tasks`)

- `PYPOST-56`
- `PYPOST-58`
- `PYPOST-59`
- `PYPOST-60`
- `PYPOST-79`
- `PYPOST-86`
- `PYPOST-87`
- `PYPOST-92`
- `PYPOST-93`
- `PYPOST-95`
- `PYPOST-100`
- `PYPOST-103`
- `PYPOST-104`
- `PYPOST-108`
- `PYPOST-110`
- `PYPOST-117`
- `PYPOST-118`
- `PYPOST-121`
- `PYPOST-125`
- `PYPOST-130`
- `PYPOST-131`
- `PYPOST-133`
- `PYPOST-139`
- `PYPOST-142`

## Conclusion

- Full report confirmation (`ai-tasks` + `ai-sprints`) currently exists for **41 / 96**
  closed Jira tickets.
- **55 / 96** closed tickets have partial or missing report coverage and should be
  normalized (either add missing ticket folders, add sprint references, or both).

# Consistency Check: ai-sprints reports vs Jira tickets

Date: 2026-03-27

## Scope

- Checked only issues that are represented as sprint work items in `ai-sprints` tables and are
  closed in Jira (`statusCategory = Done`).
- Excluded non-closed sprint item: `PYPOST-437` (`In Progress`).
- Checked sprint files:
  - `ai-sprints/100/*`
  - `ai-sprints/134/*`
  - `ai-sprints/167/*`

## Coverage

- Sprint-tracked keys found in tables: **43**
- Closed (`Done`) and verified against Jira: **42**
- In progress (not part of closed verification): **1** (`PYPOST-437`)

## Verification method

1. Extracted sprint issue rows (`Key`, `Summary`, `Status`) from backlog/roadmap/report tables.
2. Pulled corresponding Jira issues (`key`, `summary`, `status`) for all closed keys.
3. Compared summary meaning and status alignment:
   - exact match or near-exact match (prefixes like `[HP]`, `[Bug]` allowed);
   - language normalization allowed when meaning is unchanged.

## Result

- **Confirmed mismatches:** **0**
- **Confirmed status conflicts:** **0**

## Normalized-but-consistent cases

- `PYPOST-404`:
  - Jira summary is in Russian.
  - Sprint summary is English (`[Bug] Font size settings not applied on application startup`).
  - Meaning is equivalent.
- `PYPOST-403`:
  - Sprint uses `[HP]` prefix while Jira keeps the same base summary.
- `PYPOST-422`, `PYPOST-423`, `PYPOST-424`:
  - Sprint wording is slightly shortened in some report rows, but defect meaning is preserved.

## Conclusion

For all closed sprint-tracked items, `ai-sprints` reporting is consistent with Jira ticket
intent and status. No contradictory cases were found.

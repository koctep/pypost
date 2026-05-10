# Consistency Check: Jira ticket vs AI task report

Date: 2026-03-27

## Scope

- Checked only tickets that are both:
  - closed in Jira (`statusCategory = Done`);
  - present as folders in `ai-tasks/PYPOST-*`.
- Total checked tickets: **67**.

## Verification method

1. Pulled Jira ticket summaries for the 67 keys.
2. Compared against `ai-tasks/<KEY>/10-requirements.md` titles and content.
3. Ran automatic similarity heuristics (heading/summary token overlap) to find suspicious
   pairs.
4. Performed manual review for all suspicious pairs.

## Result

- **Confirmed mismatches:** **0**
- **Tickets requiring manual review after heuristic scan:** 9
- **Manual review outcome for those 9:** all semantically consistent with Jira

## Manually reviewed keys (all consistent)

- `PYPOST-3` (generic heading, detailed body matches Jira summary)
- `PYPOST-4` (generic heading, detailed body matches Jira summary)
- `PYPOST-9` (title wording differs, requirements match ticket intent)
- `PYPOST-41` (Jira title in Russian, report in English; same intent)
- `PYPOST-404` (generic heading, body clearly matches bug statement)
- `PYPOST-419` (generic heading, body matches ticket summary exactly)
- `PYPOST-421` (requirements text matches retry-exhaustion handling issue)
- `PYPOST-422` (generic heading, body matches misleading metric name issue)
- `PYPOST-424` (wording differs, same defect scope and expected behavior)

## Conclusion

For the current overlap set (`Done` in Jira + existing `ai-tasks` folder), report content and
Jira ticket intent are consistent. No contradictory implementation/reporting cases were found.

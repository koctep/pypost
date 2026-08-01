# PYPOST-930: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Decision **continued DEFER**: ENABLE threshold not met; workflow dual-run
unchanged. Lock + docs encode checklist and continued DEFER.

## Shortcuts Taken

- **No fresh Actions API scrape** — `gh run list` returned empty; assessment
  uses PYPOST-907 published timings plus local collect count (82).
- **Did not implement ENABLE sketch** — correct per threshold bar.

## Code Quality Issues

- None blocking close.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Docs name PYPOST-930 + threshold not met + continued DEFER | Covered (lock) |
| Workflow keeps dual coverage (no `not agent_e2e`) | Covered (lock) |
| ENABLE trim recipe when threshold met | Not implemented — future revisit |

## Performance Concerns

- Intentional 3.11 overlap remains until a trigger fires.

## Follow-Up Tasks

1. **Revisit ENABLE when threshold met**
   - Priority: Low
   - When ≥6m pack step × ≥3 green runs, maintainer pain, or pack ≥120 +
     domination: apply ENABLE sketch (matrix exclude + 3.13 job matrix); flip
     lock.
   - Unticketed — re-open or new Debt when a trigger fires.

2. **Optional: automate CI duration evidence capture** (existing PYPOST-931)

## Blocker Verdict

**SAFE TO CLOSE** — acceptance met via threshold assessment + continued DEFER;
no premature matrix exclusion.

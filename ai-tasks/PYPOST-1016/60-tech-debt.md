# PYPOST-1016: Technical Debt Analysis

**Verdict:** Process-sync debt only (no application-code debt). SAFE TO CLOSE
for this story's DoD. Prefer documenting trade-offs here over opening more
Debt tickets from this review.

Scope reviewed: sync pipeline outcomes (scan → classify → create → link-back →
consolidate → audit), `ai-tasks/PYPOST-1016/*`, residue PYPOST-799–803, new
Debt PYPOST-1018 / PYPOST-1019, and intentionally skipped source rows. No
`pypost/` packages changed.

## Shortcuts Taken

- **Ad-hoc agent scan, not a checked-in scanner** — Step 4 classified 769
  `ai-tasks/*/60-tech-debt.md` files with a one-shot Python heuristic in the
  agent session (TD/D rows, `no Jira yet` markers, skip regexes). There is no
  durable `scripts/` scanner, Makefile target, or CI gate that re-runs the
  completeness check after merge. (Tree now includes this story's own
  `60-tech-debt.md` and sibling artifacts; count drifts.)
- **Conservative intentional skips** — ~35+ rows left unticketed by design
  (accepted, out of scope, resolved, deferred, optional hygiene, conditional
  "only if"). Re-running with looser rules could create noise tickets.
- **Debt issues without Jira Parent field** — New Debt
  [PYPOST-1018](https://pypost.atlassian.net/browse/PYPOST-1018) and
  [PYPOST-1019](https://pypost.atlassian.net/browse/PYPOST-1019) carry the
  source parent in summary (`[PYPOST-542] …`) and description text only.
  Create path did not set Jira `parent` / epic link (verified empty on both).
  Residue PYPOST-799–803 follow the same pattern. Hierarchy in Jira is weaker
  than in markdown.
- **Scoped commit deferred** — Legitimate debt-link / inventory / audit
  updates remain uncommitted until the orchestrator after Step 8. Unrelated
  dirty paths (`doc/user/**`, `examples/**`, `README.md`, `.gitignore`,
  `.codex/**`, sibling PYPOST-1015 / 1017, `PYPOST-376/baseline-metrics.md`)
  must stay out of that commit. DoD commit checkbox stays open until then.
- **Audit log is run-local** — `scripts/untracked_debt_tickets_created.json`
  records this sync's keys; it is not a general ledger of all Debt issues.
- **Residue keys already Done** — PYPOST-799–803 were verified linked for
  traceability and are Done in Jira; they are not open backlog items from
  this story.

## Code Quality Issues

- **No application code debt** — this story did not touch `pypost/`.
- **No material hardcoded values** — browse URLs use the project Atlassian
  host; audit JSON paths and skip regexes lived in the agent session only
  (not checked in as product constants). No magic numbers in app code.
- **Scan heuristics are brittle** — free-form prose follow-ups without a
  TD/D table row or explicit "no Jira" marker can be missed; conversely,
  optional/lowest rows need human judgment beyond regex.
- **Link-back table shapes vary** — some sources use a dedicated `Jira`
  column, others append browse links in Notes. Step 5 fixed several column
  mismatches; future syncs may reintroduce uneven tables.
- **Consolidated inventory is regenerate-only** — long URL lines in
  `00-tech-debt-consolidated.md` are expected; hand-editing that file to
  add tickets remains an anti-pattern (already documented in the skill).
- **Create skill vs Parent wiring** — `jira-create-issue` accepts optional
  `parent` / epic link, but the sync run did not pass it; operators cannot
  filter Debt children from a parent issue in Jira without text search.

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Product / pytest coverage for this story | N/A — process/docs sync |
| Explicit pytest timeout markers | N/A — no new/changed tests |
| Automated unticketed-debt scanner | Missing (documented TD-1) |
| Completeness check in `make check` / CI | Missing (documented TD-1) |
| Assert Debt issues have Jira Parent set | Missing (documented TD-2) |

## Performance Concerns

None material. Full-tree scan of ~769 markdown files is fine for an agent
run. A future checked-in scanner should stay O(files × lines) and avoid
Atlassian API calls in the hot path (classify locally; create only for
true gaps).

## Deviations from Architecture

None material. Delivered flow matches `20-architecture.md` (residue verify →
rescan → create remaining → link-back → completeness → consolidate → commit
gate). Commit remains deferred by design (orchestrator). Step 3 stayed N/A
(no product behavioral change).

## Follow-up Tasks

Documented process improvements for a later sync / tooling story. **Do not
auto-create Jira Debt from this Step 7** unless the orchestrator explicitly
wants them ticketed — prefer keeping this register as the source until then.

- **TD-1 (Medium):** Checked-in scan/classify script or Make target for
  unticketed TD/D rows (non-zero exit). Replaces one-shot agent scan;
  optional CI later.
- **TD-2 (Low):** Set Jira `parent` / epic link on create (not only
  `[PARENT]` in summary). Markdown already carries parent text.
- **TD-3 (Low):** First-class residue vs new keys + skip ledger in sync
  audit JSON / skill. Avoids recreating Done residue keys.

### Intentionally not ticketed (from this sync — do not reopen)

- **PYPOST-152**: optional AppSettings / speculative metrics-path unify
- **PYPOST-179 TD-2**: optional DRY
- **PYPOST-180 / 552**: by-design `/sse` probe URLs
- **PYPOST-181 / 543**: deferred
- **PYPOST-412 / 924 / 925 / 934–936 / 948 / 956**: resolved/done sections
- **PYPOST-442 / 448**: accepted / standard practice / covered implicitly
- **PYPOST-850 / 877 / 878 / 880 / 882 / 886**: explicit do-not-ticket /
  optional hygiene
- **PYPOST-940**: conditional "only if"

### Accepted / out of scope (do not ticket from this story)

- Implementing or closing underlying Debt items (799–803, 1018, 1019, …).
- User-facing `doc/user/**` updates (dev process only; Step 8 may touch
  `doc/dev/` if needed).
- Bidirectional markdown↔Jira product; this story was one sync execution.
- Committing unrelated working-tree dirt (orchestrator scope gate).

## User documentation

N/A — no end-user product behavior or User Guide changes. Dev process notes
belong in Step 8 (`doc/dev/`) only if still needed after this review.

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | Process shortcuts only; none block close |
| Missing tests with timeout markers | **N/A** — no Python tests in scope |
| Hardcoded values | None material in app code |
| Deviations from architecture | None material |
| Acceptance gaps vs DoD | Sync done; commit deferred to orchestrator |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-1016 Step 7; follow-ups are process tooling
hygiene, not ship blockers.


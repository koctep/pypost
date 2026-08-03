# PYPOST-1030: Technical Debt Analysis

**Verdict:** Offline critical-path freshness gate matches architecture and
DoD. Catalog + contract + Makefile + docs shipped. No live credentials in CI.
**SAFE TO CLOSE.** Follow-ups below are optional expansions; leave unticketed
per sprint-task-runner instructions for this run.

Scope reviewed: `examples/collections/jira_mcp_critical_rest_paths.json`,
`tests/test_example_fixtures.py` (critical-path helpers/test), `Makefile`
(`check-jira-mcp-path-freshness`), `doc/dev/jira_mcp_path_freshness.md`,
`doc/dev/testing.md`, `doc/dev/README.md`, `ai-tasks/PYPOST-1030/*`.
Unrelated working-tree noise ignored. No `pypost/` package changes.

## Shortcuts Taken

- **Critical-path subset only** — Locked five TD-4 surfaces, not every
  request in `jira_mcp.json`. Broader inventory remains covered by existing
  capability / stretch / pagination contracts.
- **Human-curated catalog, not live OpenAPI fetch** — CI compares collection
  ↔ checked-in JSON only. Doc freshness still needs a periodic human pass
  (checklist in `doc/dev/jira_mcp_path_freshness.md`).
- **No calendar/reminder automation** — Makefile + docs ritual only; no
  scheduled CI job that pings maintainers to re-review Atlassian docs.
- **Fragment matching** — Uses `url_contains` / optional `url_excludes` /
  `mcp_param` rather than full OpenAPI path templates. Enough to catch the
  named drift modes; not a full schema validator.

## Code Quality Issues

- None material in application packages (no `pypost/` edits).
- Catalog `notes` / `doc_refs` are documentation metadata not asserted by
  tests beyond structural presence of `critical_paths`.

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Catalog file exists and locks five critical ids | Present |
| Collection method/path/`mcp_param` match catalog | Present |
| Create-sprint excludes `/sprint/` path-id form | Present (`url_excludes`) |
| Mutation test for deliberate catalog/collection drift | Missing (TD-1) |
| Locking additional non-critical requests | Out of scope (TD-2) |
| Automated fetch of Atlassian OpenAPI in CI | Out of scope (no live/network) |

Timeout-marker review: **no blocker** — module `pytestmark` already set.

## Performance Concerns

None. Offline JSON load + string contains checks.

## Deviations from Architecture

None material. Delivered Option: catalog lockfile + pytest + Makefile +
maintainer checklist docs.

## Follow-up Tasks

Concrete Debt candidates. **Leave unticketed** for this run (orchestrator /
user said do not create Jira follow-ups).

### TD-1 — Low

- **Item:** Add a small mutation-style unit test (like PYPOST-1028
  `*_rejects_*`) that clones a collection request, alters a critical URL
  fragment, and asserts `assert_jira_mcp_critical_rest_paths_match_catalog`
  fails with a clear message.
- **Notes:** Pins diagnostic quality; optional hardening.
- **Jira:** [PYPOST-1056](https://pypost.atlassian.net/browse/PYPOST-1056)

### TD-2 — Low

- **Item:** Optionally expand the catalog to other high-churn paths (e.g.
  `/myself`, comment create, backlog move) if drift becomes a recurring
  maintainer pain.
- **Notes:** Keep critical set intentional; do not dump the full collection.
- **Jira:** unticketed

### TD-3 — Low

- **Item:** Optional calendar/process reminder (team wiki / quarterly chore)
  to run the maintainer checklist and bump `reviewed_on`.
- **Notes:** Process-only; not a code change.
- **Jira:** unticketed

### Accepted / out of scope (do not ticket from this story)

- Live Jira / network OpenAPI compare in default CI.
- Full OpenAPI dump parity for all curated tools.
- Expanding the MCP tool surface.

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | Catalog subset + human ritual; none block ship |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None material |
| Acceptance gaps vs DoD | **None** — catalog, offline test, Makefile, docs |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-1030.

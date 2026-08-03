# PYPOST-1030: Periodic freshness check for jira-mcp REST paths

## Programming Language

Python for offline fixture-contract tests. Supporting artifacts are curated
JSON (expected REST path catalog) and Markdown (human checklist / docs).

## Goals

Maintainers of the curated Jira Cloud MCP example cannot tell, in CI or a
quick local check, whether the critical REST paths baked into
`jira_mcp.json` still match the paths the team has locked as correct against
Atlassian documentation. Drift (for example reverting to the removed legacy
`/rest/api/3/search`, or losing the dedicated assignee / parent-link routes)
would only be caught by live calls or ad-hoc human review.

**Business goal:** give contributors a repeatable, credential-free freshness
gate so the example’s most failure-prone Jira Cloud / Agile paths stay aligned
with a checked-in expected catalog (and a documented human review checklist
against Atlassian docs), without putting live Jira secrets into CI.

## User Stories

- As a **contributor changing `jira_mcp.json`**, I want CI to fail if a
  critical path (search JQL, sprint create/membership, parent epic link,
  assignee) drifts from the locked expected set, so regressions are caught
  offline.
- As a **maintainer reviewing Atlassian REST docs periodically**, I want a
  short checklist and a Makefile target that re-runs the same offline compare,
  so refreshing the locked catalog is intentional and documented.
- As a **product steward**, I want no live Jira credentials or network calls
  required for this gate, so it stays safe in default CI.
- As an **agent operator**, I want the curated tools to keep using the
  documented modern endpoints (especially `/search/jql` and dedicated assignee /
  parent routes), so skill workflows do not silently break after Atlassian
  deprecations.

## Definition of Done

- [x] A checked-in expected catalog (or equivalent allowlist) locks the
      critical REST path markers for at least: `/search/jql`, sprint create,
      sprint membership, parent-field epic link, and assignee.
- [x] An automated offline test fails when `jira_mcp.json` drifts from that
      locked expected set for those critical entries.
- [x] A Makefile target (and/or documented checklist) lets maintainers re-run
      the same offline check without live credentials.
- [x] Developer docs describe how to refresh the catalog after a human or
      OpenAPI/doc review of Atlassian REST docs.
- [x] Default CI does not require Jira credentials or network calls for this
      gate.
- [x] Existing Jira MCP example fixture contracts remain intact.

## Task Description

**Problem:** Follow-up from PYPOST-1026 TD-4. There is no periodic offline
freshness mechanism for critical Jira Cloud / Agile paths in
`examples/collections/jira_mcp.json` versus current Atlassian REST docs.

**Scope (in):**

- Offline compare of known critical path strings in `jira_mcp.json` against a
  checked-in expected catalog / documented allowlist.
- Focus on: `/search/jql`, sprint create/membership, parent epic link,
  assignee.
- Documented checklist and/or Makefile target for maintainers.
- Updates to `doc/dev` as needed.

**Scope (out):**

- Live Jira calls or credentials in CI.
- Full OpenAPI dump parity or locking every request in the collection.
- Expanding the curated MCP tool surface beyond path freshness.
- Replacing Atlassian MCP or adding an in-process Atlassian server.

**Constraints and assumptions:**

- Doc/OpenAPI compare (human-curated locked catalog) is enough; CI compares
  fixture ↔ catalog only.
- Critical-path set may grow later; this story ships the focused set above.
- Sprint-task-runner autonomous mode: user approval gates are pre-approved.

## Q&A

| Question | Answer |
| -------- | ------ |
| Why not call Atlassian docs from CI? | No live credentials/network in CI; offline catalog compare is enough (ticket). |
| Why only critical paths? | Highest-risk drift surfaces from PYPOST-1026 TD-4; full dump is out of scope. |
| Why a catalog instead of only inline test constants? | Catalog is the maintainable lockfile humans update after doc review; tests enforce match. |
| Related artifact? | `ai-tasks/PYPOST-1026/60-tech-debt.md` TD-4 → this issue. |

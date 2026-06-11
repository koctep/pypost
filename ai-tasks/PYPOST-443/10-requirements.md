# PYPOST-443: Metrics rename migration support for dashboards and alerts

## Goals

PYPOST-422 renamed the Prometheus counter from `email_notification_failures_total` to
`request_retry_exhaustions_total`. Operators who still query the legacy series name in
Grafana dashboards or Prometheus alert rules see empty panels or silent alert gaps after
upgrade. This task reduces operational disruption by defining a clear migration path and
providing transitional compatibility where appropriate.

**Traceability:** Follow-up from [PYPOST-422](https://pypost.atlassian.net/browse/PYPOST-422)
consumer-migration finding (medium).

## User Stories

- **As an SRE/operator**, I want existing dashboards that still reference the legacy metric
  name to continue receiving data during a transition window, so incidents are not missed
  while I update queries.
- **As an SRE/operator**, I want a documented migration checklist (find, replace, verify,
  communicate), so I can upgrade PyPost without guessing which queries to change.
- **As a developer**, I want the canonical metric name and deprecation status documented in
  `doc/dev/`, so future renames follow the same pattern.

## Definition of Done

- A migration plan exists with operator communication checklist and PromQL examples.
- Transitional support is implemented (deprecated alias counter mirroring increments) or
  documented as doc-only with explicit rationale; this task delivers **both** doc and alias.
- Tests verify both `request_retry_exhaustions_total` and the legacy alias export on scrape.
- Developer documentation in `doc/dev/` is updated and linked from the dev docs index.
- Sunset expectations for the legacy alias are stated so operators know when to migrate.

## Task Description

**Problem:** Hard rename (PYPOST-422 option A) removed `email_notification_failures_total`
from the registry. Dashboards and alerts using the old name return no data.

**Expected:** Define migration plan and implement transitional support, including operator
communication checklist.

**Constraints:**

- Canonical series remains `request_retry_exhaustions_total`; legacy name is deprecated only.
- Label semantics (`endpoint`) unchanged.
- No duplicate business logic — single increment path mirrors to alias.
- Sunset timeline documented; alias removal is a future follow-up, not this task.

## Q&A

- **Why not doc-only?** Alias gives immediate relief for unmigrated dashboards; doc drives
  intentional migration and communication.
- **Who owns Grafana updates?** Operators; PyPost provides checklist and dual export window.

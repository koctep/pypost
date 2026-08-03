# PYPOST-1044: Technical Debt Analysis

## Shortcuts Taken

None.  The multi-server lifecycle uses a registry with one manager per
configuration, rather than extending the legacy singleton with mutable active
environment state.

## Code Quality Issues

The review found that the shared top-bar label still said `MCP: OFF` while
registry-owned servers could be running.  This was corrected in scope: the
label now shows only aggregate running/failed counts and receives registry
status updates.  It deliberately does not show server IDs, ports, collection
names, environment names, or credentials.  The review also found that the
old global tool overview could mix collections after multi-server support;
the manager now opens a tools view scoped to the selected server's collection.

No remaining code-quality issue was found in the registry ownership,
transactional reconfiguration, persistence, or per-instance refresh paths.

## Missing Tests

None identified.  The new and changed pytest modules declare explicit timeout
markers. Focused coverage verifies concurrent tool/environment isolation,
enabled auto-start (including disabled rows and partial startup failure
isolation), post-load startup ordering, lifecycle isolation,
pending-reconfiguration Stop cancellation, bind failure containment and
rendering, duplicate-port dialog validation, scoped refreshes, rollback,
persistence validation, aggregate metrics, dialog routing, and the aggregate
top-bar status.

## Performance Concerns

None identified for the requested desktop scale.  Status aggregation is a
small in-memory count over configured instances; no request-time global
collection or environment lookup was added.

## Follow-up Tasks

None.  No separate Jira follow-up is warranted from this review.

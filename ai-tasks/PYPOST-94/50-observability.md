# PYPOST-94: Observability

## Changes

None. Restore remains a synchronous UI path without per-id logging (unchanged from
PYPOST-390).

## Rationale

Performance fix does not alter observable behavior or log output. `refresh_tree_completed`
continues to log collection/request counts on full rebuild.

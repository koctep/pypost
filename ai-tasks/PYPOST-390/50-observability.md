# PYPOST-390: Observability

## Changes

No new logging or metrics. `restore_tree_state` is a synchronous UI path; existing
`refresh_tree_completed` log covers rebuild volume.

## Rationale

Restore is silent by design (same as before). Performance improvement does not change
observable log output.

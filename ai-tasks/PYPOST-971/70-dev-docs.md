# PYPOST-971: Developer Documentation

## Documentation Scope

PYPOST-971 consolidates DisplayRole matching ownership in the agent harness. It
does not change public APIs, user-visible behavior, logging, or metrics.
Canonical developer docs were updated in:

- `doc/dev/ui_actions.md`
- `doc/dev/testing.md`

No user documentation, configuration reference, or release note is needed.

## Changes Made

### UI actions guide

`ui_actions.md` now names the shared helpers in `pypost.agent.tree_index` and
keeps flat-versus-recursive semantics explicit:

| Helper | Documented role |
| --- | --- |
| `display_role_equals` | Single exact DisplayRole string-match policy |
| `find_child_index_by_display_text` | Flat scan of direct children (root for
  model-backed list views); does not recurse |
| `find_tree_index_by_display_text` | Recursive depth-first tree walk; compares
  via `display_role_equals` only |

Also updated:

- Architecture table includes `tree_index.py` (PYPOST-941 / PYPOST-971).
- `ui_select` type table points flat views at the flat helper and trees at DFS.
- Notes that trees must not reuse the flat sibling finder per level (would
  change duplicate-label first-match order).
- Notes that `QListWidget` stays on `findItems` and is outside the shared model
  scan.
- Troubleshooting for option-not-found distinguishes flat root scan vs tree DFS.
- Ownership marker: `tests/test_display_role_scan_ownership.py`.

### Testing guide

`testing.md` now documents the three helpers, flat vs recursive distinction,
the ownership AST marker, and the existing runtime suites.

## Configuration

No new configuration, environment variables, or make targets.

## Validation

Documentation-only change in Step 8. Focused ownership and selection suites were
already green after Step 4; not re-run here.

Relative links in the updated sections target existing files under `doc/dev/`
and `tests/`.

## Review Status

Step 8 remains `[/]` pending documentation review. It must not be marked `[x]`
until approval (FR-10 / AC-8).

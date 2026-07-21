# PYPOST-834: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

All acceptance criteria for stable UI identity are met. Items below are
non-blocking follow-ups (no blockers relative to DoD).

## Shortcuts Taken

- **No production INFO logs for identity apply.** Observability is the
  spot-check plus documented constants; per-widget logging would be noise.
- **Shared role `objectName`s on every request tab.** Agents must scope
  URL/method/Send/response lookup to the current tab. Documented; not a unique
  per-tab id scheme.
- **`accessibleIdentifier` mirror is best-effort.** Uses `getattr` so older Qt
  stubs would skip; project pins PySide6 6.11.1 where the API exists.
- **Full `make check` not re-run.** Step 4 validated `make lint` plus scoped
  identity + lifecycle tests (4 passed).

## Code Quality Issues

- `plus_tab_placeholder` remains an unprefixed historical `objectName` (not
  in the PYPOST-834 key catalog). Optional rename to `pypost_plus_tab_placeholder`
  for consistency.
- Spot-check uses `findChild` + presenter attribute equality; does not assert
  theme re-apply leaves ids intact (construction-only setters make this low risk).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Key identities after UI ready | Covered (`test_key_widgets_expose_stable_identities`) |
| Id literals locale-independent | Covered (`test_widget_ids_are_locale_independent_literals`) |
| Theme change does not clear `objectName` | Not covered (optional) |
| Every new tab gets role ids | Implicit (same constructors); no multi-tab assert |
| Full `make check` green | Not re-run for this story |

Tests have `pytestmark = pytest.mark.timeout(60)` — no timeout-marker blockers.

## Performance Concerns

None. Identity is set once at construction.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Optional assert: theme apply leaves key objectNames | Low risk today | [PYPOST-844](https://pypost.atlassian.net/browse/PYPOST-844) |
| TD-2 | Low | Align `plus_tab_placeholder` to `pypost_` prefix | Not an AC surface | [PYPOST-845](https://pypost.atlassian.net/browse/PYPOST-845) |
| TD-3 | Low | Multi-tab spot-check for role ids | Implicit via constructors | [PYPOST-846](https://pypost.atlassian.net/browse/PYPOST-846) |
| TD-4 | Low | Run full `make check` when sibling noise is clear | Deferred gate | [PYPOST-847](https://pypost.atlassian.net/browse/PYPOST-847) |

Deferred by design (not debt for this ticket):

- Snapshots / actions / waits / golden flow / packaging — sibling stories.
- Exhaustive identity for every dialog and history control.

## Blocker Review

**SAFE TO CLOSE** — FR1–FR10 satisfied by `widget_ids` convention,
applied key surfaces, `doc/dev/ui_identity.md`, and spot-check tests. Listed
gaps are non-blocking; orchestrator may ticket follow-ups separately.

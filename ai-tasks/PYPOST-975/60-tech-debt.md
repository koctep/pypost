# PYPOST-975: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: Path A live `COLLECTION_TREE` negative select proofs
(`test_live_collection_tree_missing_option_raises`,
`test_live_collection_tree_index_out_of_range_raises`) under
`seeded_agent_e2e_session`; fixture-parity substrings; production unchanged;
module `timeout(60)` + `agent_e2e` markers present. Closes PYPOST-942 TD-2.
**Do not create Jira issues in this step** (Phase D later).

## Review Scope

Reviewed task artifacts and the task-owned diff:

- `tests/test_ui_actions.py` (live Path A negatives only; production untouched)
- `ai-tasks/PYPOST-975/` (`10-requirements`, `20-architecture`,
  `40-code-cleanup`, `50-observability`, `00-roadmap`)
- Parent debt: `ai-tasks/PYPOST-942/60-tech-debt.md` TD-2
- Dev-doc readiness for Step 8: `doc/dev/ui_actions.md`, `doc/dev/testing.md`

## Requirements and Architecture Review

| Requirement | Evidence | Verdict |
| --- | --- | --- |
| FR-1 / AC-1 missing label | Live `ui_select` + `"option not found"` | Met |
| FR-2 / AC-2 top-level OOR | Parametrized `-1` / `rowCount()` + substring | Met |
| FR-3 both cases under Path A | Two live tests (OOR parametrized) | Met |
| FR-4 fixture-parity messages | Same substrings as PYPOST-942 tree negatives | Met |
| FR-6 / AC-4 fixture suite retained | Fixture tree negatives unchanged | Met |
| AC-3 agent_e2e + timeout | Module `pytestmark` `timeout(60)`, `agent_e2e` | Met |
| AC-5 / NFR-1–5 no prod change | `pypost/` untouched; Step 6 N/A logs | Met |
| AC-6 closes PYPOST-942 TD-2 | Path A delivered | Met |
| FR-7 / docs accuracy | Cite live proofs in Step 8 (planned) | Pending Step 8 |

No architecture deviation. Path A chosen; Path B correctly rejected (no
harness gap). Step 3 red-before-green correctly N/A (coverage debt only).

## Shortcuts Taken

None that are temporary crutches. Intentional, accepted choices:

- **Green-on-first-run contract tests** — `_select_tree` already raises on the
  live product tree; task is live regression coverage (same stance as
  PYPOST-942 / PYPOST-974).
- **Substring assertions** — `"option not found"` /
  `"option index out of range"` in `str(exc_info.value)`, matching fixture
  suite convention (not full `reason=` / `widget_id=` formatting).
- **`seeded_agent_e2e_session` only** — Preferred non-empty live inventory;
  blank-session negatives were an acceptable fallback, not a residual gap.
- **Dynamic `model.rowCount()` for OOR upper bound** — Survives seed growth
  without hard-coding `1`.
- **Dev docs deferred to Step 8** — Architecture planned optional cite of live
  proofs in `doc/dev/ui_actions.md` / `agent_e2e.md` / testing notes.
- **Full `make check` not re-run in Step 5** — Scoped agent-e2e + flake8;
  `verify-ai-tasks` expects later-step artifacts on an open task folder.

## Code Quality Issues

None material.

- Live proofs sit next to fixture tree negatives in `tests/test_ui_actions.py`.
- Inherit module `pytestmark`; no new markers or helpers required.
- Sentinel missing label `__no_such_collection_tree_option__` cannot collide
  with seed display text.
- `ai-tasks/PYPOST-975/20-architecture.md` table rows exceed 100 characters;
  wrapping would break Markdown tables (same pattern as prior cleanup reports).
  Hygiene only — not a product issue.
- Unrelated `make typecheck` mypy baseline drift (218 → 221) noted in Step 5;
  no PYPOST-975 path reported. Not owned by this story.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Live missing label on `COLLECTION_TREE` | Covered |
| Live top-level OOR (`-1`, `rowCount()`) | Covered (parametrized) |
| Fixture list/tree negatives (PYPOST-942) | Covered (pre-existing) |
| Explicit pytest timeout markers | Present — module `timeout(60)` |
| Nested tree index OOR | Out of scope (top-level contract) |
| Live `METHOD_COMBO` OOR via agent e2e | Out of scope (PYPOST-974 deferred) |
| Blank-session live negatives | Not required — seeded preferred |
| Full `reason=` / `widget_id=` formatting | Not required — suite convention |

Timeout-marker review: **no blocker** under `.cursor/lsr/do-testing.md`.

## Performance Concerns

None. Synchronous `session.ui_select` raises at the call site; no event-loop
polling or network. Seeded session cost matches existing agent e2e pack.

## Observability, Diagnostics, and Privacy

Step 6 confirmed: no new production logs or metrics (NFR-4 / AC-5). Diagnostic
surface remains `UiTargetNotInteractableError` with fixture-parity reason
substrings. Success-path DEBUG `ui_action_applied` unchanged and not hit by
negatives.

## Deviations from Architecture

None. Delivered Path A as designed:

- Live proofs in `tests/test_ui_actions.py` via `seeded_agent_e2e_session`
- Production `_select_tree` / `session.ui_select` untouched
- Fixture negatives retained as synthetic API baseline
- Nested / combo / list-view live negatives left to sibling tickets
- Dev-doc cite deferred to Step 8

## Follow-up Tasks

Concrete Debt candidates for a later sync via `tech-debt-jira-sync` /
`jira-create-issue`. **No Jira browse links yet** (orchestrator tickets in
Phase D). Leave links empty / unticketed.

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent TD-2 (live collection-tree negative select) | This story (PYPOST-975) |
| Fixture list/tree negative select | [PYPOST-942](https://pypost.atlassian.net/browse/PYPOST-942) |
| Combo OOR index contract | [PYPOST-974](https://pypost.atlassian.net/browse/PYPOST-974) |

### NON-BLOCKER

None. No new unticketed Debt follow-ups from this change.

### Accepted / out of scope (do not ticket from this story)

- Nested tree index out-of-range beyond top-level contract (PYPOST-916).
- Live `METHOD_COMBO` / list-view negative select via agent e2e.
- Replacing seed open/click helpers with `ui_select` (selection ≠ open).
- Asserting full exception `reason=` / `widget_id=` formatting.
- Blank-session duplicate live negatives (seeded is the chosen proof).
- Changing production error wording or adding select ERROR logs.
- Step 8 developer-doc cite of live proofs in `doc/dev/ui_actions.md` /
  `doc/dev/testing.md` / agent e2e docs (planned workflow step).
- Unrelated mypy baseline count drift (`make typecheck`).
- Architecture Markdown table rows longer than 100 characters (table
  rendering constraint; same as prior task cleanup notes).

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** — module `timeout(60)` |
| Deviations from architecture | None |
| Acceptance gaps vs DoD | **None** (docs cite → Step 8) |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-975 Step 7; Path A DoD met; no Phase D Debt
tickets required from this story. Dev docs remain for Step 8.

## Validation Evidence

| Check | Result |
| --- | --- |
| Step 4 / 5 live proofs | 3/3 live_collection_tree cases passed |
| Full `tests/test_ui_actions.py` | 38 passed (Step 5) |
| Timeout markers | Module `pytestmark` present |
| `make lint` / flake8 on touched tests | Clean |
| Production `pypost/` | Unchanged |
| Step 6 observability | No-new-log decision documented |

## Documentation Review

User documentation is not applicable (harness / agent e2e only). Canonical
developer docs still describe fixture-only negative select locks
(`doc/dev/ui_actions.md`, `doc/dev/testing.md`) without naming the live
`COLLECTION_TREE` proofs. That update belongs to **Step 8**, not a tech-debt
ticket.

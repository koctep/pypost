# PYPOST-1357: Technical Debt Analysis

Scope: registry + autouse dispose for collection export UI tests and the
collections teardown repro —
`tests/test_collection_export_ui.py`,
`tests/test_collection_export_ui_teardown_repro.py`
(reuse of `tests/helpers/qt_widget_dispose.py`). Production `pypost/` unchanged.

**No item below is a BLOCKER.** Touched modules keep explicit timeout markers
(`pytestmark = pytest.mark.timeout(60)`; B overrides with
`@pytest.mark.timeout(360)`). The do-testing explicit-timeout rule is met.
Phase D / tech-debt sync creates or closes Jira issues; this step only records
candidates.

## Summary Table

| ID | Priority | Item | Follow-up |
| --- | --- | --- | --- |
| TD-1 | Low | Product suite still repeats `dispose_collections_export_fixture` in ~19 `finally` blocks beside registry autouse | [PYPOST-1482](https://pypost.atlassian.net/browse/PYPOST-1482) (retargeted) |
| TD-2 | Low | Registry / `_make_presenter` / autouse duplicated across product suite and teardown repro | Jira: [PYPOST-1498](https://pypost.atlassian.net/browse/PYPOST-1498) |
| TD-3 | Low | Leftover audit only matches panel identity + top-level `QTreeView` (no dialog / delegate scan) | Jira: [PYPOST-1499](https://pypost.atlassian.net/browse/PYPOST-1499) |
| TD-4 | Low | `dispose_collections_export_fixture(presenter: Any, …)` still duck-typed | no new — existing [PYPOST-1483](https://pypost.atlassian.net/browse/PYPOST-1483) |
| TD-5 | Lowest | Hardcoded `teardown(timeout_ms=50)` in collections dispose wrapper | no new — existing [PYPOST-1486](https://pypost.atlassian.net/browse/PYPOST-1486) |
| TD-6 | Low | `doc/dev/export_ui_qt_dispose.md` still describes collections as finally-only; no repro / R-autouse note | **addressed in Step 8** |
| TD-7 | Lowest | B zero-crash matrix on restored host; original affected wheel mix never captured | no (accepted DoD diagnostic) |
| TD-8 | Low | Module/session `topLevelWidgets` purge in `conftest` still out of scope | no new — existing [PYPOST-1485](https://pypost.atlassian.net/browse/PYPOST-1485) |
| TD-9 | Medium | Pre-existing: `make lint` does not flake8 `tests/` | no new — existing [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) |
| — | — | PYPOST-1315 TD-2 collections dispose contract | **addressed here** — close [PYPOST-1479](https://pypost.atlassian.net/browse/PYPOST-1479) in Phase D |
| — | — | PYPOST-1315 TD-5 autouse for collections dispose | **addressed here** (autouse landed); refine/close [PYPOST-1482](https://pypost.atlassian.net/browse/PYPOST-1482) vs TD-1 residual |

## Shortcuts Taken

- **Finally + autouse retained (belt and suspenders).** Step 4 added
  `_created_presenters` + autouse dispose (R-autouse / PYPOST-1315 TD-5) but kept
  every product-suite `finally` call so existing tests still dispose eagerly.
  Idempotent and correct for the missed-finally guard; leaves ~19 redundant
  dispose sites (TD-1), same class as env-export TD-4 / PYPOST-1481.
- **Per-module registry copy.** Product suite and
  `test_collection_export_ui_teardown_repro.py` each own a module-level list and
  autouse fixture rather than a shared helper (mirrors env `_created_widgets`
  locality). Faster to land R-autouse; duplicates construction and cleanup
  (TD-2).
- **Narrow leftover predicate.** Desired-end-state checks only panel validity
  and top-level `QTreeView` / panel leftovers. Enough for green A-complete /
  R-autouse on the restored host; architecture’s optional stronger audit
  (delegates, stray `QDialog`) was not required for the R-autouse cause fork
  (TD-3).
- **Diagnostic B, not live SIGSEGV.** Bounded subprocess matrix recorded
  zero-crash exits under PySide6 / shiboken6 / pydantic on the restored host.
  DoD explicitly allows this artifact; original affected versions remain
  uncaptured (TD-7).
- **No production DeferredDelete.** Production
  `collections_presenter_lifecycle.teardown` still close-only; test helper
  remains the DeferredDelete drain. Matches architecture default (fix locus =
  harness). Not new debt beyond already-known production vs test ownership
  split.

## Code Quality Issues

- **TD-1 (Low) — redundant finally dispose.**
  `tests/test_collection_export_ui.py` still wraps every test in
  `try` / `finally: dispose_collections_export_fixture(...)`. Autouse already
  drains `_created_presenters`. Follow-up: drop the repeated finally blocks
  (keep registry registration in `_make_presenter`) once R-autouse remains the
  durable missed-finally guard. Prefer updating [PYPOST-1482](https://pypost.atlassian.net/browse/PYPOST-1482)
  rather than filing a duplicate “add autouse” ticket.
- **TD-2 (Low) — duplicated harness scaffolding.**
  `_created_presenters`, `_make_presenter` registration, and
  `_cleanup_collections_export_presenters` are copy-pasted between the product
  suite and the teardown repro (repro also adds
  `_collections_export_end_state_checks` for post-autouse asserts). Follow-up:
  extract a small shared collections-export dispose registry fixture (or helper
  module) used by both files.
- **TD-3 (Low) — incomplete leftover taxonomy.**
  `_leftover_collections_export_roots` treats any top-level `QTreeView` as a
  collections leftover and does not scan mocked-dialog tops or delegates.
  Acceptable while A-complete is green; tighten if a future residual crash
  shows survivors outside that predicate.
- **TD-4 / TD-5** — helper typing and magic `timeout_ms=50` unchanged in
  `qt_widget_dispose.py`; already ticketed as PYPOST-1483 / PYPOST-1486.

No unexplained architecture deviations: cause fork **R-autouse**; A-complete /
A-incomplete polarities preserved; production export behavior untouched.

## Missing Tests

- **Timeouts:** not missing.

  | Module | Marker |
  | --- | --- |
  | `tests/test_collection_export_ui.py` | `pytestmark = timeout(60)` |
  | `tests/test_collection_export_ui_teardown_repro.py` | `pytestmark = timeout(60)`; B `@pytest.mark.timeout(360)` |
  | `tests/helpers/qt_widget_dispose.py` | N/A (helper) |

- **Collections dispose contract (former PYPOST-1315 TD-2 / PYPOST-1479):**
  **covered** by A-complete, A-incomplete (residual-liveness negative control),
  and R-autouse in `tests/test_collection_export_ui_teardown_repro.py`. Phase D
  should close PYPOST-1479 as done by this ticket — do not re-file.
- **No additional product-assertion coverage gaps** for the nineteen non-slow
  collection export UI nodes; assertions and timeouts were preserved by design.
- **Optional (not required):** stress B under a pinned historical wheel mix if
  those versions are ever recovered — only if maintainers want live `-11`
  evidence beyond the diagnostic matrix (TD-7 accepted without a ticket).

## Performance Concerns

- Autouse dispose adds an idempotent event-loop drain after each test that
  already disposed in `finally` (double dispose). Negligible vs GUI body cost;
  removing finally (TD-1) would also remove the double drain.
- B runs the nineteen-node file up to three times (≤120s child budget, parent
  timeout 360s). Acceptable for the evidence module; not a default CI path
  beyond collecting that file.

## Architecture / harness remainder

- **TD-8 — session purge** still out of scope; tracked by PYPOST-1485.
- **TD-6 — docs drift:** **addressed in Step 8** —
  `doc/dev/export_ui_qt_dispose.md` now documents collections registry +
  autouse, teardown repro A / R-autouse / B, and LIFO end-state fixture
  teardown after autouse dispose.

## Follow-up Tasks

Specific tasks for Phase D / tech-debt Jira sync (do **not** create issues in
Step 7):

1. **TD-1 — Drop redundant collections `finally` dispose** (Low)  
   Jira: [PYPOST-1482](https://pypost.atlassian.net/browse/PYPOST-1482)
   (retargeted). Rely on `_created_presenters` + autouse; keep explicit dispose
   only where polarity tests require it (A-complete / A-incomplete).

2. **TD-2 — Share collections dispose registry between suite and repro** (Low)  
   Jira: [PYPOST-1498](https://pypost.atlassian.net/browse/PYPOST-1498).
   Extract common `_make_presenter` registration + autouse cleanup so product
   and teardown-repro modules do not diverge.

3. **TD-3 — Broaden collections leftover audit if needed** (Low)  
   Jira: [PYPOST-1499](https://pypost.atlassian.net/browse/PYPOST-1499).
   Extend `_leftover_collections_export_roots` (dialogs / delegates) only if a
   residual crash or A-complete failure shows survivors outside panel /
   `QTreeView`.

4. **Close addressed upstream debt**  
   - [PYPOST-1479](https://pypost.atlassian.net/browse/PYPOST-1479) — **Done**
     (collections dispose contract landed in PYPOST-1357).  
   - [PYPOST-1482](https://pypost.atlassian.net/browse/PYPOST-1482) — retargeted
     to TD-1 residual (drop redundant finally).

5. **Do not re-file (existing):**  
   - [PYPOST-1483](https://pypost.atlassian.net/browse/PYPOST-1483) (TD-4 typing)  
   - [PYPOST-1486](https://pypost.atlassian.net/browse/PYPOST-1486) (TD-5 timeout)  
   - [PYPOST-1485](https://pypost.atlassian.net/browse/PYPOST-1485) (TD-8 purge)  
   - [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) (TD-9 test lint)

**Accepted / no new ticket:** TD-7 (zero-crash B diagnostic; DoD satisfied).

**Step 8:** TD-6 doc updates landed in `doc/dev/export_ui_qt_dispose.md`.

## User documentation

N/A — no user-facing product change. Dev docs for collections autouse / contract
are in `doc/dev/export_ui_qt_dispose.md` (TD-6 / Step 8).

## Independent Closure Review

Left for the gate owner / review subagent. This execution leaves STEP 7 `[/]`
and does not create Jira issues.

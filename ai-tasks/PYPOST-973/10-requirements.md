# PYPOST-973: Adopt qt_item_view teardown in collections_tree

## Goals

Isolated collections-tree test harnesses create model-backed `QTreeView`
instances. Without detaching the model before the view is destroyed, Qt can
emit teardown warnings and destabilize later offscreen Qt sessions (including
agent e2e). PYPOST-940 introduced a shared teardown helper for item views;
collections-tree fixtures still grow without using it.

The business goal is reliable, quiet Qt test teardown for collections-tree
unit and e2e-style harnesses so maintainers and CI keep a stable offscreen
suite. This is the Low-priority Debt follow-up recorded as TD-1 in PYPOST-940.
Labels: `tech-debt`, `testing`, `ui`.

## Programming Language

Python with PySide6. Task artifacts and developer documentation use English
Markdown.

## User Stories

- As a **maintainer**, I want collections-tree isolated harnesses to tear down
  model-backed views through the shared item-view helper, so Qt destructor
  noise does not appear when those fixtures grow.
- As a **CI owner**, I want collections-tree Qt tests to finish without
  teardown warnings, so suite stability does not depend on accidental GC
  ordering.
- As a **test author**, I want a clear, shared way to close an isolated tree
  harness, so I do not re-invent `setModel(None)` in each module.
- As a **debt owner**, I want PYPOST-940 TD-1 closed with proof that the shared
  helper is used where isolated tree views are created.

## Definition of Done

- Shared `qt_item_view` teardown is used by collections-tree isolated harness
  teardown where model-backed views are created.
- Isolated tree harness consumers close views through that shared path (or an
  equivalent harness wrapper that calls it).
- Focused collections-tree / teardown tests stay green under explicit timeouts.
- No Qt teardown warnings attributable to those harnesses in the focused run.
- No production UI, public API, logging, or metric behavior changes.
- Unticketed follow-ups, if any, live only in this task’s `60-tech-debt.md`.

## Task Description

### Problem

`tests/helpers/collections_tree.py` builds isolated `QTreeView` + model
harnesses used by many collection-tree tests. Those harnesses do not yet call
the shared `detach_item_view_model` / related teardown from
`tests/helpers/qt_item_view.py`. As isolated views grow across modules,
duplicate or missing detach logic risks Qt teardown warnings.

### Business Reason

Quiet, consistent fixture teardown reduces flaky Qt sessions and keeps
collections-tree tests maintainable as coverage expands. Reusing the shared
helper avoids diverging local `setModel(None)` copies.

### In Scope

- Adopt shared `qt_item_view` teardown in collections-tree harness lifecycle.
- Update isolated-tree harness consumers so teardown runs where applicable.
- Add or extend automated proof that harness close detaches the model via the
  shared helper.
- Keep existing collections-tree behavioral tests green.

### Exclusions

- Changing production widgets, presenters, or product UI.
- Redesigning all Qt fixture patterns outside collections-tree harnesses.
- Changing `close_item_view_fixture` widget-id discovery for ui_select fixtures
  (already covered by PYPOST-940) except reuse of the shared detach primitive.
- Broad suite redesign or unrelated cleanup.

## Functional Requirements

- **FR-1:** Closing an isolated collections-tree harness must detach the view’s
  model through the shared item-view teardown helper before the view is closed
  or abandoned.
- **FR-2:** Isolated tree harness builders must expose a supported close path
  that callers can use (direct close helper and/or context manager).
- **FR-3:** Existing collections-tree tests that create isolated harnesses must
  use that close path where they own the harness lifecycle.
- **FR-4:** Automated proof must show that harness close leaves the view with
  no model attached.
- **FR-5:** Existing collections-tree behavioral coverage remains green and
  unchanged in meaning.
- **FR-6:** Developer testing guidance must mention collections-tree adoption of
  the shared teardown.

## Non-Functional Requirements

- **NFR-1 — Compatibility:** Test-helper only; no new production public API.
- **NFR-2 — Stability:** Offscreen, deterministic Qt fixture execution with
  explicit pytest timeouts; no live network.
- **NFR-3 — Maintainability:** Prefer reuse of `detach_item_view_model` over a
  second local `setModel(None)` helper.
- **NFR-4 — Observability:** No new log or metric requirements.
- **NFR-5 — Scope control:** Test-debt only; keep call-site churn limited to
  isolated-tree harness consumers.

## Acceptance Criteria

- **AC-1:** Shared `qt_item_view` teardown is used by collections-tree harness
  close.
- **AC-2:** Isolated harness call sites that create model-backed tree views use
  the harness close path.
- **AC-3:** Automated proof asserts model is detached after harness close.
- **AC-4:** Focused collections-tree / teardown tests are green under explicit
  timeout protection with no Qt teardown warnings from those harnesses.
- **AC-5:** No user-visible product behavior, public interface, logging schema,
  or metric changes.
- **AC-6:** `doc/dev/testing.md` (or equivalent) documents collections-tree
  adoption.

## Constraints and Assumptions

- Source debt: PYPOST-940 TD-1 — “Adopt qt_item_view teardown in collections_tree
  if isolated views grow.”
- Isolated views already exist across multiple test modules; adoption is needed
  now rather than deferred.
- `detach_item_view_model` and `close_item_view_fixture` already exist; this
  task consumes them (especially detach) rather than reinventing them.
- Step 1 is documentation-only; autonomous sprint-task-runner pre-approves
  progression.

## Main Entities and Interactions

| Entity | Business role | Required outcome |
| --- | --- | --- |
| Isolated tree harness | Creates model-backed tree for unit tests | Closes safely |
| Shared item-view teardown | Detaches model before view destruction | Used by harness close |
| Collections-tree tests | Own harness lifecycle | Call close path |
| CI / maintainers | Rely on quiet Qt teardown | No destructor warnings |
| Testing docs | Guide fixture authors | Document adoption |

Interaction overview:

1. A test builds an isolated collections-tree harness with a model-backed view.
2. The test exercises collection-tree behavior.
3. Harness close detaches the model via the shared helper, then closes the view.
4. CI proves detach and keeps sibling collections-tree tests green.

## Evidence and Traceability

| Evidence | Current observation | Requirement impact |
| --- | --- | --- |
| PYPOST-940 TD-1 | Records Low debt for collections_tree adoption | Goals, AC-1 |
| Jira PYPOST-973 | Acceptance: shared teardown; no Qt teardown warnings | AC-1–AC-4 |
| `tests/helpers/qt_item_view.py` | Shared detach/close helpers exist | FR-1, NFR-3 |
| `tests/helpers/collections_tree.py` | Builds views; no shared teardown yet | FR-2, FR-3 |
| Call sites | ~27 `build_isolated_tree_actions` uses across 4 modules | FR-3, AC-2 |
| `doc/dev/testing.md` | Documents qt_item_view for ui_select fixtures | FR-6, AC-6 |

## Risks

| Risk | Consequence | Requirement guard |
| --- | --- | --- |
| Local `setModel(None)` copy | Diverges from shared helper | NFR-3, FR-1 |
| Call sites left without close | Warnings persist | FR-3, AC-2 |
| Over-broad fixture rewrite | Dilutes 1-SP focus | Exclusions, NFR-5 |
| Behavioral test churn | False failures | FR-5, AC-4 |

## Q&A

- **Q: Why adopt now if TD said “if views grow”?**
  **A:** Isolated tree harnesses already span multiple modules; growth has
  happened. Adoption closes the recorded debt against current reality.
- **Q: Must every Qt test in the repo change?**
  **A:** No. Only collections-tree isolated harness builders and their
  consumers that own those views.
- **Q: Does this change product UI?**
  **A:** No. Test helpers and docs only.
- **Q: Is `close_item_view_fixture` required verbatim?**
  **A:** The shared detach primitive must be used. A harness-specific close
  that calls `detach_item_view_model` satisfies acceptance; widget-id lookup
  is for ui_select-style roots.

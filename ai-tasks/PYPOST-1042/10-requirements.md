# PYPOST-1042: Dedicated contract test for a tree with no model

## Goals

The agent UI primitive `ui_select` is the only way an automated agent picks a row in the
application's collection tree. When a caller targets a tree that has no data attached, the
primitive must fail loudly, immediately, and with a message that says *which* control shape was
wrong — a tree, not a flat item view. That distinction is what tells an agent (or a developer
reading a CI log) whether the target was resolved to the wrong widget kind or whether the right
widget simply has not been populated yet.

Today that behaviour is **implemented but unguarded**. `_select_tree` in
`pypost/agent/ui_actions.py` raises `UiTargetNotInteractableError` with the reason
`tree has no model`, and `doc/dev/ui_actions.md` documents that reason as part of the public
error vocabulary — but no test in the suite asserts it. The sibling case for flat model-backed
views *is* guarded: PYPOST-972 added `test_select_list_view_no_model_raises`, and its own
tech-debt review closed with TD-1 explicitly saying the tree half was left uncovered.

The business value of closing that gap:

- **A documented promise stays a promise.** The two reason strings are a published contract
  (`doc/dev/ui_actions.md` troubleshooting table). An undertested contract string can be reworded
  or deleted in a refactor with a fully green suite, silently breaking every agent script and
  runbook that reads it.
- **Symmetry of the failure vocabulary.** `item view has no model` and `tree has no model` are
  deliberately different so the two dispatch branches are distinguishable. Only one side of that
  pair is currently proven, so the *distinctness* itself is only half-proven.
- **Closing a tracked debt item.** This ticket is the ticketed form of PYPOST-972 TD-1; leaving it
  open keeps a known coverage hole in the agent error-path suite.

## Programming Language

Python (PySide6 widgets, pytest). Task artifacts and developer documentation are English Markdown.

## Task Description

### Established facts (verified against the code, not assumed)

| # | Fact | Evidence |
| --- | --- | --- |
| F-1 | `_select_tree` **already raises** `UiTargetNotInteractableError` with reason `tree has no model` when `model()` is `None`. | `pypost/agent/ui_actions.py:243-246` |
| F-2 | That check is the **first statement** of `_select_tree` — it runs before the event-loop pump and before the option is inspected, so a text option and an integer option fail identically. | `pypost/agent/ui_actions.py:243-250`; confirmed at runtime with a throwaway offscreen Qt probe (no repo file written) |
| F-3 | `ui_select` dispatches `QTreeView` **before** the generic `QAbstractItemView` branch, so a tree never produces the item-view reason. | `pypost/agent/ui_actions.py:287-294` |
| F-4 | The flat-view twin is covered; the tree is not. `tree has no model` appears in `tests/` exactly once — as a *negative* assertion inside the item-view test. | `tests/test_ui_actions.py:314-330` (assertion at line 328) |
| F-5 | The reason string is already published to developers, but its row is the only one in the troubleshooting table with no fixture proof named. | `doc/dev/ui_actions.md:196`, `doc/dev/ui_actions.md:364-366` |
| F-6 | `ui_select` runs a visibility/enabled precheck before dispatch, so an unshown fixture would fail with `not visible` and never reach the model check. | `pypost/agent/ui_actions.py:89-93, 286` |

**The consequence that shapes this task:** the required production behaviour **already exists and
is correct**. This is a *coverage* task, not a *behaviour* task. The expected outcome is a new
test that is green the first time it runs. A classic red-then-green repro is therefore not
available, and the guard's genuineness must be demonstrated another way (see FR-6).

### Scope

**In scope**

- One dedicated automated contract test for the "tree target, no model attached" scenario.
- Making the published error vocabulary in developer documentation point at that proof.
- Evidence that the new test actually guards the behaviour rather than passing vacuously.

**Out of scope (non-goals)**

- Changing any production behaviour, error wording, or dispatch order in `pypost/agent/`. The
  wording of both reason strings is a locked public contract (PYPOST-972 explicitly refused to
  change it).
- Extending coverage to missing-option or out-of-range index cases — owned by PYPOST-942 and
  already covered.
- Any live product `COLLECTION_TREE` end-to-end variant; the scenario is an isolated-fixture
  contract, and the product tree always has a model.
- Any change to the DisplayRole ownership rules, their AST guard, or its repro (PYPOST-971 /
  PYPOST-1041). The no-model failure short-circuits before any display-text matching, so this task
  neither adds nor moves a reader of the display role.

## Main Entities

| Entity | Business meaning | Attributes that matter here |
| --- | --- | --- |
| **UI target** | A control an agent addresses by its stable widget id. | Widget id; resolved widget kind (tree vs flat item view); visible; enabled |
| **Tree target** | A hierarchical selection control (the collection tree family). | Whether data is attached at all |
| **Selection request** | "Select this option in this target", by display text or by position. | Option value (text or index) |
| **Not-interactable failure** | The refusal an agent receives when the target exists but cannot serve the request. | Widget id; **reason** — the human- and machine-readable phrase |
| **Reason vocabulary** | The published set of refusal phrases developers and agents key on. | `tree has no model` vs `item view has no model` must stay distinguishable |

## User Stories

- **As an agent author**, when I ask a tree to select a row before its data is loaded, I want a
  refusal that names the tree case specifically, so I can tell "not populated yet" apart from
  "I resolved the wrong kind of control" without reading the source.
- **As a maintainer of `ui_select`**, I want the tree no-model refusal locked by a test, so a
  refactor that drops the check or reuses the flat-view wording fails in CI instead of in an
  agent run.
- **As a developer reading the troubleshooting table**, I want the `tree has no model` entry to
  name its proof, exactly as the `item view has no model` entry already does, so I can trust the
  documented vocabulary and find the example that demonstrates it.
- **As the tech-debt owner of PYPOST-972**, I want TD-1 closed with evidence, so the agent
  error-path coverage matrix has no remaining "Not covered" row for the tree missing-model case.

## Functional Requirements

- **FR-1** — A dedicated automated check must exist for the scenario "a selection is requested on
  a tree target that has no data attached", separate from the existing flat-view check.
- **FR-2** — The scenario must be observed to produce a *not interactable* refusal — not a
  *target not found* refusal, not a crash, and not a silent no-op.
- **FR-3** — The refusal must be observed to carry the tree-specific reason `tree has no model`.
- **FR-4** — The refusal must be observed **not** to carry the flat-view reason
  `item view has no model`, so the distinctness of the two branches is proven from the tree side
  as well as from the flat-view side (which asserts the mirror image today).
- **FR-5** — Both request forms must be covered: selecting by display text and selecting by
  position. Fact F-2 says the refusal precedes any inspection of the request form; the coverage
  must state that, so a future change that moves the check after option handling is caught.
- **FR-6** — Because the behaviour already exists (F-1), the delivery must include recorded
  evidence that the new check is a real guard: removing or reversing the production refusal must
  make it fail. A plain "it passed" is not sufficient evidence for this task.
- **FR-7** — The published error vocabulary in the developer documentation must name the new proof
  for `tree has no model`, matching how the `item view has no model` entry names its own, and must
  stay consistent with the DisplayRole ownership section added by PYPOST-1041 (the no-model path
  never reaches display-text matching, so nothing there changes).

## Non-Functional Requirements

- **NFR-1 (bounded execution)** — The new check must run under an explicit time bound and must not
  wait on any unbounded condition; it must not be able to hang CI or an agent run.
- **NFR-2 (isolation and cleanliness)** — It must exercise an isolated throwaway UI fixture, leave
  no window or UI resource behind, and must not depend on, or perturb, any other check in the
  module or on the running product.
- **NFR-3 (no regression)** — The existing flat-view check, the rest of the agent UI action
  checks, and the PYPOST-971/1041 ownership checks must remain green.
- **NFR-4 (repository conventions)** — Work goes through the repository's `make` entry points; the
  full suite is known-red for unrelated, already-ticketed reasons (PYPOST-1241, PYPOST-1231..1234,
  PYPOST-1111, PYPOST-1117) and those failures are not this task's blockers.

## Constraints and Assumptions

- **C-1** — No production source under `pypost/` is expected to change. If any change there is
  proposed, it needs an explicit written justification, because the current behaviour is already
  correct (F-1).
- **C-2** — The two reason phrases are a locked public contract; rewording either is forbidden by
  this task's scope.
- **C-3** — The scenario must be set up so the target is visible and enabled, otherwise the
  refusal observed would be the visibility/enabled one and the check would prove nothing (F-6 in
  the facts table).
- **C-4** — Anything created must be reachable in the fast (non-slow) test selection, so the guard
  actually runs in the routine gate rather than only in a nightly run.
- **A-1** — A tree with no data attached reports no data attached (`model()` is `None`) in the Qt
  binding in use; verified for `QTreeView` at the pinned PySide6 version.
- **A-2** — The scenario is reproducible headlessly (offscreen), like the existing flat-view check.

## Definition of Done

- **AC-1** — A dedicated, independently named automated check exists for "tree target with no data
  attached", distinct from `test_select_list_view_no_model_raises` and traceable to PYPOST-1042.
- **AC-2** — It asserts the refusal is the *not interactable* failure and that its message contains
  `tree has no model`.
- **AC-3** — It asserts the message does **not** contain `item view has no model`, mirroring the
  flat-view check's negative assertion and proving branch distinctness from both sides.
- **AC-4** — Both request forms (by display text and by position) are shown to produce the same
  refusal, pinning that the check precedes option handling.
- **AC-5** — No production behaviour, wording, or dispatch order changed; the diff outside tests
  and documentation is empty, or carries a written justification (C-1).
- **AC-6** — The new check runs under an explicit time bound, uses an isolated fixture, and tears
  that fixture down (NFR-1, NFR-2).
- **AC-7** — Evidence is recorded that the check fails when the production refusal is removed or
  reworded (FR-6), since it is green on its first run and cannot show a classic red-to-green
  transition.
- **AC-8** — `doc/dev/ui_actions.md` names the new proof on the `tree has no model` entry, the
  agent error-path coverage matrix no longer lists the tree missing-model case as uncovered, and
  PYPOST-972 TD-1 can be closed by reference; targeted runs of the affected modules are green and
  the repository lint gate passes (NFR-3, NFR-4).

## Q&A

- **Q: Does `_select_tree` currently raise anything when the model is `None`, or does it fall
  through?**
  A: It raises. `pypost/agent/ui_actions.py:243-246` begins with `model = widget.model()` and
  `if model is None: raise UiTargetNotInteractableError(widget_id, "tree has no model")`. A
  runtime probe on a visible, enabled, model-less `QTreeView` returned
  `UI target not interactable: widget_id='probe_tree' reason=tree has no model` for a text option
  and for an integer option. There is no fall-through, no `None` return, and no crash.

- **Q: Then what is actually missing?**
  A: Only the test. The string `tree has no model` occurs in `tests/` exactly once, at
  `tests/test_ui_actions.py:328`, and there it is asserted to be **absent** from the *item-view*
  message. Nothing asserts it is ever *present*.

- **Q: Why is a green-on-first-run test worth writing?**
  A: The reason string is published in `doc/dev/ui_actions.md` as part of the agent-facing error
  vocabulary and is relied on to distinguish two dispatch branches. Unasserted, it can be reworded
  or the whole guard removed with a green suite. This is exactly the argument PYPOST-972 accepted
  for the flat-view twin.

- **Q: Why does this need a "prove the guard is real" step rather than the usual red repro?**
  A: The Top-Down workflow's Step 3 expects a failing test first. Here the production behaviour
  already exists, so a correct new test is green immediately (the same situation PYPOST-972
  recorded as "green-on-first-run contract test — classic red-before-green N/A"). To keep the same
  assurance, FR-6/AC-7 require showing the check goes red against a mutated production guard.

- **Q: Should the live product collection tree be covered too?**
  A: No. The product tree always has a model, so the scenario is unreachable there; PYPOST-972
  recorded the equivalent live variant as out of scope for the same reason.

- **Q: Does this interact with the DisplayRole ownership boundary documented for PYPOST-1041?**
  A: Only as a constraint to respect. The no-model refusal happens before any display-text match,
  so no display-role reader is added, moved, or removed and the AST ownership guard plus its repro
  stay untouched and green. The documentation update in FR-7 sits in the same file and must not
  contradict that section.

- **Q: Why can't we just extend the existing flat-view test?**
  A: The ticket and PYPOST-972 TD-1 both call for a *dedicated* check. One test asserting two
  widget kinds would fail as a unit and hide which branch broke, and it would lose the symmetric
  "reason A present, reason B absent" pairing that makes the distinctness provable from each side.

## References

- Origin of the follow-up: [`ai-tasks/PYPOST-972/60-tech-debt.md`](../PYPOST-972/60-tech-debt.md)
  (TD-1, and the "Tree missing model — **Not covered**" row of its Missing Tests matrix).
- Mirror to follow: `test_select_list_view_no_model_raises`, `tests/test_ui_actions.py:314`.
- Production behaviour under test: `_select_tree` / `_select_item_view` / `ui_select`,
  `pypost/agent/ui_actions.py:211-296`.
- Published error vocabulary and DisplayRole ownership boundary: `doc/dev/ui_actions.md`.
- Jira: [PYPOST-1042](https://pypost.atlassian.net/browse/PYPOST-1042).

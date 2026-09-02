# PYPOST-1240: Architecture

## Architectural intent

Improve the two existing ownership-validation diagnostics that currently report only a bare
missing responsibility. The diagnostic producer remains in the validation boundary; it adds the
already-established owner and a repair direction to the message. Ownership decisions, lookup
algorithms, selection behavior, and application-facing contracts remain unchanged.

## Named architectural decision

**Localized diagnostic decoration at the existing validation boundary.** Existing ownership
checks remain authoritative; only failure-message construction gains owner and remedy context at
the validation boundary that already produces these diagnostics. This avoids introducing a new
diagnostic service or API, minimizes coupling and behavior risk, and keeps ownership decisions,
lookup algorithms, selection behavior, and application-facing contracts unchanged.

## Affected components

- `tests/test_display_role_scan_ownership.py`: existing ownership-validation assertions and their
  failure diagnostics. The test-side validation remains the consumer of the diagnostic contract.
- `pypost/agent/tree_index.py`: authoritative owner of shared DisplayRole matching and flat/tree
  lookup responsibilities. The recursive/tree lookup diagnostic names the Tree Index module and
  directs restoration of recursive lookup there.
- `pypost/agent/ui_actions.py`: owner of item-view selection orchestration. The item-view selection
  diagnostic names the UI Actions module and directs restoration of item-view selection there.
- `doc/dev/ui_actions.md`: developer-facing ownership and troubleshooting documentation, updated
  only if the implemented wording or remediation guidance needs to be recorded.

The implementation should be limited to the smallest existing assertion or diagnostic-message
sites. No new module, public API, ownership rule, runtime metric, or application log is required.

## Dependencies and main interfaces

The existing dependency direction is:

```text
tests/test_display_role_scan_ownership.py
    -- existing AST/source inspection --> pypost/agent/tree_index.py
    -- existing AST/source inspection --> pypost/agent/ui_actions.py

pypost/agent/ui_actions.py
    -- existing import and delegation --> pypost/agent/tree_index.py
```

The test-side validator reads bounded Python source through `Path` and `ast`; it does not import
or execute the Qt implementation. Its existing assertion and diagnostic boundary is:

- `_collect_display_role_violations(paths: tuple[Path, ...]) -> list[_OwnershipViolation]`
  produces deterministic violation records.
- `_validate_display_role_ownership(paths: tuple[Path, ...]) -> None` aggregates those records,
  preserves source order, and raises one `AssertionError` for the quality-gate diagnostic.
- `_assert_tree_shared_ownership(tree_defs: dict[str, ast.AST] | None) -> None` and the existing
  `_select_item_view` assertion cluster in `test_flat_and_tree_share_display_role_match_helper`
  provide the focused recursive/tree and item-view responsibility checks.

The production vocabulary being described comes from these existing interfaces:

| Module | Existing function/API | Responsibility vocabulary |
| --- | --- | --- |
| `pypost.agent.tree_index` | `display_role_equals(index, text)` | Shared exact `DisplayRole` matching |
| `pypost.agent.tree_index` | `find_child_index_by_display_text(...)` | Flat child lookup |
| `pypost.agent.tree_index` | `find_tree_index_by_display_text(...)` | Recursive/tree lookup owned by Tree Index |
| `pypost.agent.ui_actions` | `_select_item_view(...)` | Item-view selection owned by UI Actions |
| `pypost.agent.ui_actions` | `ui_select(...)` | Existing caller-facing selection entry point |

`tree_index.__all__` and the `ui_select` contract remain unchanged. The wording names these
existing modules and functions only; no new public API, inter-module protocol, runtime dependency,
or service dependency is introduced.

## Diagnostic flow

1. The existing ownership validation evaluates the expected responsibility using its current
   source/ownership checks.
2. If recursive/tree lookup is absent, the existing failure path emits one readable diagnostic
   containing: the missing responsibility, `Tree Index` as owner, and the instruction to restore
   recursive/tree lookup there.
3. If item-view selection is absent, the existing failure path emits one readable diagnostic
   containing: the missing responsibility, `UI Actions` as owner, and the instruction to restore
   item-view selection there.
4. Other ownership failures retain their current diagnostics and ordering. Successful validation
   produces the same result as before.

The message is a presentation change at the failure boundary. It must not change which condition
fails, how source ownership is determined, or how multiple failures are aggregated.

## Implementation plan

### Step 3 failing-repro plan

The focused red repro lives in `tests/test_display_role_scan_ownership_repro.py` beside the
existing `_parse_file(Path)`/AST repro helpers. It parses the ownership test's own source, locates
the main ownership test's two missing-responsibility assertions, and checks their literal messages
without importing or executing the Qt implementation. The repro is hermetic and does not require a
live Qt application, synthetic mutant, or external service.

- **Recursive/tree lookup case:** inspect the main test's assertion for
  `find_tree_index_by_display_text` and require the symbol, owner `Tree Index`, remedy to restore
  recursive lookup, and a one-line message. The repro fails before the message edit because the
  original message contains only the missing symbol.
- **Item-view selection case:** inspect the main test's assertion for `_select_item_view` and
  require the symbol, owner `UI Actions`, remedy to restore item-view selection, and a one-line
  message. The repro fails before the message edit because the original message contains only the
  missing symbol.
- **Preserved behavior:** keep the existing ownership and repro tests intact. No aggregate
  coverage harness or new mutant is required for this two-message fail-fast contract.

Step 3 creates and independently reviews this red repro before any Step 4 production change is
started. Step 4 may then make only the minimal diagnostic-wording change needed to turn the
reviewed repro green.

## Responsibility boundaries

`tree_index` remains the single owner of shared DisplayRole matching and recursive/tree lookup.
`ui_actions` remains the owner of item-view selection orchestration and its delegation to the
shared lookup behavior. The diagnostics describe these boundaries; they do not move code or make
the modules depend on a new diagnostic service.

## Testing strategy

- Preserve the existing ownership checks and their current passing behavior.
- In `tests/test_display_role_scan_ownership_repro.py`, use the existing `_parse_file`/AST pattern
  to inspect the main ownership test's two assertion messages. Each repro asserts the symbol,
  correct owner module, actionable remedy, and one-line message.
- Keep the existing repro tests intact and do not add a synthetic mutant or aggregate harness; the
  two source-inspection repros are the focused coverage for this two-message fail-fast contract.
- Use the repository Makefile targets for focused and full validation; do not make the architecture
  depend on a new test framework or runtime fixture.

## Observability

No production logging, metrics, tracing, or telemetry is needed. The improved failure text is the
existing quality-gate diagnostic surface. Existing logging and reporting behavior outside these two
messages remains unchanged.

## Risks and mitigations

- **Risk: wording omits the actual repair destination.** Mitigation: review both owner and remedy
  as separate acceptance points and keep them on the same line as the missing responsibility.
- **Risk: a message-only change alters validation behavior.** Mitigation: keep condition detection,
  ownership assignments, result types, and aggregation logic untouched; cover success and unrelated
  failure paths.
- **Risk: documentation and diagnostics drift.** Mitigation: use the same Tree Index/UI Actions
  vocabulary in the focused tests and developer documentation.
- **Risk: unrelated baseline failures obscure the focused result.** Mitigation: run the focused
  checks separately and record any pre-existing full-suite failures in the cleanup/technical-debt
  artifacts rather than broadening this issue.

## Compatibility and rollout

This is backward-compatible for successful callers and for validation semantics. Consumers that
display or search failure text will see more descriptive messages for exactly two existing failure
conditions; the missing responsibility remains present in each message. Rollout is the normal
commit and CI path, with no migration, configuration, or deployment sequencing required.

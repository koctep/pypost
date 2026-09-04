# PYPOST-1230: Extract a shared presenter import lifecycle wait helper

## Research

The accepted requirements define this as a test-maintainability change. The current source of
truth is `tests/test_collections_import_ui.py`:

- `_wait_import()` receives a caller-owned outcome predicate, an optional
  `CollectionsPresenter`, and a configurable timeout.
- Its combined predicate first evaluates the expected outcome and then requires
  `presenter._import_actions.is_busy()` to be false when a presenter is supplied.
- It delegates event-loop pumping and timeout enforcement to
  `tests.helpers.process_until.process_until`.
- The existing collection-import cases use the helper for successful imports, invalid files,
  conflicts, emitted signals, logging, and persistence failures.

The presenter already owns the import lifecycle, while `process_until` owns the Qt event-loop and
wall-clock deadline mechanics. The extraction should therefore move only the composition of those
two conditions into test support. It must not add a production dependency on a test helper.

`QEventLoop.exec()` starts a local event loop and returns when the loop is quit, which matches the
existing `process_until` design for allowing queued Qt signals and worker completion callbacks to
run during a bounded wait. See the [PySide6 QEventLoop documentation](
https://doc.qt.io/qtforpython-6/PySide6/QtCore/QEventLoop.html).

## Implementation Plan

1. Add `tests/helpers/collection_import_wait.py` with a public `wait_import()` test-support
   function. Keep its call shape aligned with the current `_wait_import()` function so the existing
   collection-import tests require only an import change and removal of local duplicate code.
2. Keep the helper test-only and delegate all event-loop work to `process_until()`.
3. Preserve one combined predicate: evaluate the caller's expected-outcome predicate first, then
   require the supplied presenter import lifecycle to be idle. A presenter-less call continues to
   wait only for the caller's predicate, matching the current optional argument behavior.
4. Preserve the caller-selectable default timeout and let `process_until()` raise its bounded,
   diagnostic `AssertionError` when the combined condition is not reached.
5. Update `tests/test_collections_import_ui.py` to import `wait_import` from the shared helper and
   replace its `_wait_import` call sites without changing assertions or scenario setup.
6. Add focused helper coverage in Step 3 before making the extraction green. The red repro will
   exercise a fake outcome predicate and fake presenter lifecycle that become complete on separate
   event-loop turns, and will assert that the helper returns only after both conditions are true.
   A second case will verify that an unmet condition fails with the configured timeout. The test
   module will declare an explicit pytest timeout and use bounded internal waits.
7. Run the repository's relevant Make targets after implementation; no production module or public
   presenter API is part of this plan.

**Mandatory — Failing Repro (next Step 3):** Add a red automated test under `tests/` for the
shared helper contract before creating the helper implementation. The test should prove that an
outcome becoming visible before the presenter is idle does not release the wait, and that a stalled
combined condition produces a bounded timeout failure. It should use deterministic fakes or mocks,
not live external services, and carry an explicit `pytest.mark.timeout` marker. Step 4 may then add
the helper and migrate the existing collection-import UI tests until the repro and the preserved
scenario suite pass. This task has no production behavioral change, but it does have test-support
behavior that requires a red repro for the reusable completion contract.

## Architecture

### Component diagram

```text
presenter test scenario
        |
        | expected outcome: Callable[[], bool]
        v
tests.helpers.collection_import_wait.wait_import()
        |
        | combined condition: outcome is true AND import lifecycle is idle
        v
tests.helpers.process_until.process_until()
        |
        +--> nested QEventLoop / Qt event processing
        +--> bounded polling and wall-clock watchdog
        +--> AssertionError with timeout detail
        |
        v
CollectionsPresenter -> CollectionImportActions -> async import signals/state
```

### Components and responsibilities

| Component | Responsibility | Boundary |
| --- | --- | --- |
| Presenter test scenario | Starts an import, supplies an outcome predicate, and performs assertions after the wait. | Owns scenario-specific success, error, conflict, signal, and logging expectations. |
| `wait_import()` | Provides the shared import-completion contract and combines the two required conditions. | Test-only; must not be imported by application code. |
| Presenter lifecycle adapter | Exposes the import action's busy/idle observation to the helper. | Keeps the existing presenter lifecycle knowledge inside the test-support boundary. |
| `process_until()` | Pumps Qt events and enforces a wall-clock timeout while evaluating a predicate. | Generic test infrastructure; owns timeout mechanics, not import semantics. |
| `CollectionsPresenter` and `CollectionImportActions` | Produce the outcome and transition the import interaction to idle. | Production code remains unchanged by this task. |

### Boundaries and dependency direction

- Test cases depend on `tests.helpers.collection_import_wait`; the helper depends on the existing
  `tests.helpers.process_until` primitive.
- The helper may observe the presenter import lifecycle through the existing test-visible presenter
  object, but it must not add methods, state, or imports to production modules.
- `process_until` remains the only component responsible for nested event-loop execution,
  cross-thread watchdog wake-up, and timeout error formatting.
- The outcome callback is supplied by the test and must be a side-effect-free observation. The
  helper must not interpret result payloads, dialogs, persistence state, or log messages.
- The helper returns no business result. Completion is represented by normal return; failure is an
  `AssertionError` identifying the configured bound, preserving the existing test contract.

### Main interface

The planned test-only interface is:

```python
def wait_import(
    done: Callable[[], bool],
    presenter: CollectionsPresenter | None = None,
    timeout_ms: int = DEFAULT_IMPORT_WAIT_MS,
) -> None:
    """Wait for an import outcome and the associated presenter lifecycle to become idle."""
```

The concrete type annotation may use a narrow structural protocol if that avoids coupling the
helper to one presenter class. The required protocol surface is only the ability to observe whether
the associated import action is busy. The default timeout remains 5,000 milliseconds, and callers
may override it for deliberately slower test scenarios. No production caller adopts this
interface.

### Data and control flow

1. A test starts an import and registers its result, signal, or log observation.
2. The test calls `wait_import(done, presenter)`.
3. `wait_import()` evaluates `done()`. If it is false, the combined condition remains false and
   the event loop continues to pump queued callbacks.
4. Once `done()` is true, the helper checks the import lifecycle. If the presenter is supplied, the
   condition remains false while its import actions are busy; this covers the final apply,
   refresh, signal delivery, and return-to-idle transitions.
5. When both conditions are true, `process_until()` returns and the test performs its existing
   assertions.
6. If the deadline expires first, `process_until()` raises a bounded `AssertionError`. The helper
   must not convert a timeout into a successful return or wait indefinitely.

The order of the checks is intentional: an outcome predicate may be true while queued import
cleanup is still pending, and an idle presenter without the expected outcome is also incomplete.

### Architectural patterns and rationale

- **Composition over duplication:** the helper composes a scenario predicate with the existing
  generic event-loop primitive instead of creating another polling implementation.
- **Dependency injection:** the scenario supplies `done`, and the presenter/lifecycle observation
  is passed into the helper, keeping scenario details out of shared infrastructure.
- **Structural typing at the test boundary:** if used, a narrow protocol avoids requiring future
  presenter suites to inherit from or modify a concrete presenter solely for test coordination.
- **Single-responsibility test support:** import semantics stay in the presenter and test; event-loop
  mechanics stay in `process_until`; the new helper owns only the import completion contract.

### Testing strategy

- The new helper test verifies the AND contract with outcome and idle state completing at different
  times.
- The helper timeout test uses a short explicit bound and verifies a clear failure rather than a
  hang. It must obey the repository's per-test timeout and bounded-wait rules.
- The migrated `test_collections_import_ui.py` remains the integration-level coverage for successful
  imports, invalid input, conflicts, completion signals, logging, and partial persistence failure.
- The migration must preserve all existing assertions, fixtures, patches, teardown behavior, and
  the module timeout marker.
- No production tests or runtime behavior are needed because the application implementation is out
  of scope.

### Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| A result callback fires before final presenter cleanup. | Require both `done()` and idle in one bounded predicate. |
| A stalled worker or signal causes an indefinite test hang. | Reuse `process_until()` and retain its wall-clock watchdog and explicit timeout. |
| The helper becomes coupled to a private presenter detail. | Contain the adapter in one test-support module and keep its required interface narrow; do not spread private access across suites. |
| Future suites use a predicate with side effects. | Document `done` as an observation callback and test only state checks in the shared helper. |
| Extraction changes scenario timing or assertions. | Keep the default timeout, predicate order, and call shape identical; run the existing collection-import suite. |
| Test helper is accidentally imported by production code. | Place it under `tests/helpers/`, add no application imports pointing to it, and verify the staged dependency direction during review. |

## Q&A

- **Q: Does this architecture change application behavior?**

  A: No. The new component is test-only, and production presenter, import, persistence, dialog,
  and signal behavior remain outside the change boundary.

- **Q: Why reuse `process_until()` instead of adding a new Qt wait loop?**

  A: It already provides the repository's bounded nested-event-loop and watchdog behavior. A second
  loop would duplicate timeout policy and increase the chance of inconsistent test behavior.

- **Q: What does “complete” mean for this helper?**

  A: The caller's expected outcome is observable and the associated presenter import interaction is
  idle. Either condition alone is insufficient.

- **Q: Can another presenter suite reuse this helper?**

  A: Yes, when it can supply the same narrow lifecycle observation and an outcome predicate. The
  helper does not depend on collection names, result payloads, persistence assertions, or dialogs.

- **Q: What is deliberately deferred?**

  A: The red helper test belongs to Step 3, and the helper implementation plus test migration belong
  to Step 4. This Step 2 artifact makes no code or test changes.

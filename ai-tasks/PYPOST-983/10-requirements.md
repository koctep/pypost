# PYPOST-983: Centralize the forced-settle timeout contract

## Goals

The golden, dialog, and mapping asynchronous UI timeout companions currently
carry the same near-zero forced-settle budget independently. Maintaining the
same policy in several places creates a risk that one companion drifts from the
others, making CI timing less predictable and future maintenance needlessly
repetitive.

The business goal is to give maintainers and CI one authoritative timeout
contract for these companion scenarios. The existing forced-timeout behavior
must remain unchanged: the contract represents a 0.05-second budget, causes the
failure path to finish promptly, and does not change the meaning of any
existing success or diagnostic assertion.

## User Stories

- As an asynchronous UI test maintainer, I want the golden, dialog, and mapping
  timeout companions to share one timeout policy, so updating that policy does
  not require synchronizing multiple independent values.
- As a CI runner, I want forced-timeout companions to use the same bounded
  near-zero budget, so a timeout regression is quick and deterministic rather
  than dependent on ambient timing.
- As a failure investigator, I want this maintenance change to preserve the
  existing timeout diagnostics and scenario identity, so a failed companion
  remains actionable and comparable with earlier runs.
- As a test author, I want the normal asynchronous settle budget to remain
  distinct from the forced-timeout budget, so this cleanup does not weaken
  legitimate happy-path waits.

## Definition of Done

- A single authoritative test-level timeout contract represents the existing
  0.05-second forced-settle budget.
- The golden, dialog, and mapping timeout companions all use that contract.
- No companion in the named scope retains a conflicting independent forced
  timeout value.
- Existing timeout diagnostics, scenario-specific identifiers, and assertion
  meaning remain unchanged.
- Existing happy-path coverage for the three scenario families remains valid;
  the cleanup does not replace or weaken it.
- The forced-timeout companions complete within their existing bounded test
  limits and do not introduce a hanging CI path.
- Standard Make-based lint, artifact verification, and focused/full relevant
  test validation pass for the completed change.
- No production behavior, user-facing behavior, network behavior, or unrelated
  test policy changes are introduced.

## Task Description

### Problem and desired outcome

The three named timeout companions need the same short forced-settle budget to
exercise failure diagnostics consistently. Because the value is currently
maintained separately, a future update could change only some companions and
make their determinism or runtime characteristics diverge.

The desired outcome is one shared contract consumed by all three companions,
with the current value and observable behavior preserved. This is test-harness
maintenance; it is not a change to application timing or user-visible
functionality.

### In scope

- The forced-settle timeout contract used by the golden timeout companion.
- The forced-settle timeout contract used by the dialog timeout companion.
- The forced-settle timeout contract used by the mapping timeout companion.
- Preservation of the current 0.05-second budget, bounded execution, existing
  diagnostics, and existing assertions.
- Focused regression validation for all affected companion scenarios and the
  relevant repository quality gates.

### Out of scope

- Changing the 0.05-second value or introducing a new timeout policy.
- Changing the normal happy-path asynchronous settle budget.
- Changing application, presenter, dialog, mapping, HTTP, or network behavior.
- Changing timeout exception formats, diagnostic fields, step identifiers, or
  response/modal context assertions.
- Adding new golden, dialog, or mapping scenarios, or broadening the test
  matrix.
- Refactoring unrelated test helpers or timeout constants.
- User-facing documentation, production observability, dependency changes, or
  Jira follow-up creation.
- Commit, Jira status transition, or worklog operations by this step.

### Current ambiguity resolved

- **Which consumers are covered?** Only the existing golden, dialog, and
  mapping forced-timeout companions named by the Jira issue. Other timeout
  values and unrelated tests are not implicitly included.
- **Should the budget change?** No. The existing 0.05-second intent is the
  compatibility baseline and must remain exact.
- **Does this include normal settle waits?** No. Normal happy-path waits have a
  separate purpose and remain outside this contract.
- **Does this alter failure evidence?** No. Existing scenario-specific step
  identifiers and contextual diagnostics must remain equivalent in meaning.

### Programming language

Python 3.10+ is the implementation language. The affected coverage belongs to
the repository's asynchronous UI test harness and is maintained as English
test documentation and artifacts.

### Deterministic behavior

Each named companion must continue to force its timeout path using the same
near-zero 0.05-second budget. The timeout must be bounded and repeatable under
the standard offscreen CI environment. The cleanup must neither wait for
ambient external activity nor rely on timing that varies between the three
scenario families.

### Compatibility

This is a test-only compatibility-preserving change. The following remain
stable:

- application and user-visible behavior;
- happy-path scenario outcomes;
- forced-timeout failure outcomes;
- diagnostic step identity and contextual evidence;
- the distinction between forced-timeout and normal settle budgets; and
- test selection and discoverability for the existing companions.

### Validation expectations

- Run the focused companion coverage through the repository's Make targets,
  including golden, dialog, and mapping timeout scenarios.
- Run `make lint` and `make verify-ai-tasks`.
- Run the relevant broader test or quality gate through Make when the completed
  workflow reaches its validation stage.
- Confirm that the protected baseline, sprint registry, `AGENTS.md`, and
  unrelated files are unchanged.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Forced-settle timeout contract | Defines the shared bounded budget for timeout companions |
| Golden timeout companion | Verifies timeout diagnostics for the golden UI flow |
| Dialog timeout companion | Verifies timeout diagnostics while a product dialog is settling |
| Mapping timeout companion | Verifies timeout diagnostics for the mapping UI flow |
| Normal settle budget | Supports successful asynchronous flows and remains separate |
| CI runner | Executes the companions and requires bounded, repeatable completion |
| Maintainer | Updates and reviews the shared testing policy |

The timeout contract is consumed by each of the three existing companions. The
companions exercise their own scenario-specific failure paths and continue to
report their existing diagnostics to the CI runner. The normal settle budget is
not changed by this interaction.

## User Scenarios

1. A maintainer reviews the three timeout companions and finds one authoritative
   forced-settle policy rather than three values that can drift.
2. CI runs the golden companion's forced timeout. It completes within the
   bounded budget and preserves the existing step and response-context evidence.
3. CI runs the dialog companion's forced timeout. It completes within the
   bounded budget and preserves the existing step and modal-context evidence.
4. CI runs the mapping companion's forced timeout. It completes within the
   bounded budget and preserves the existing step and response-context evidence.
5. CI runs the corresponding happy-path scenarios. Their successful outcomes
   remain unchanged because the normal settle budget is not part of this task.

## Q&A

**Why is this needed?**

To prevent timeout-policy drift across asynchronous UI companion tests and keep
their CI runtime and failure behavior deterministic.

**What exact policy is being preserved?**

The existing `FORCED_SETTLE_TIMEOUT_S` intent and its 0.05-second value. The
task centralizes ownership of that contract; it does not revise the value.

**Why not centralize every timeout?**

Normal settle waits serve a different purpose and require a larger budget. They
are deliberately outside this task's scope.

**What happens to production behavior?**

Nothing. The change is limited to test-harness organization and must preserve
all existing product and test acceptance meaning.

**How is completion validated?**

Through the repository's Make-based focused tests and quality gates, including
`make lint` and `make verify-ai-tasks`, with the relevant companion and broader
test validation performed later in the workflow.

**What is the source of the requirements?**

Jira [PYPOST-983](https://pypost.atlassian.net/browse/PYPOST-983), whose
acceptance is a single shared constant used by the golden, dialog, and mapping
companions with unchanged behavior.

# PYPOST-1153: Parallel test runner maintainability follow-ups

## Goals

The parallel test runner should remain predictable and trustworthy as the project evolves.
Developers and CI operators need to run the normal test targets with confidence that:

- the requested test mode, worker count, and additional test arguments are honored;
- invalid configuration is reported clearly before it can produce unsafe or confusing runs;
- coverage enforcement follows the project policy consistently; and
- the behavior is protected by durable automated checks.

The business reason for this work is to reduce maintenance risk around the parallel test
workflow. A reliable workflow shortens feedback cycles, makes failures easier to act on,
and prevents changes to commands or coverage policy from silently weakening validation.

## User Stories

- As a developer, I want the standard test commands to use the documented parallel-runner
  contract so that local results match the intended project workflow.
- As a CI operator, I want worker and coverage settings to be validated consistently so that
  a run cannot appear successful because of an invalid or ignored setting.
- As a maintainer, I want test-runner behavior to be covered by focused automated checks so
  that future changes reveal contract regressions close to their cause.
- As a maintainer, I want an optional limit for an individual test-file run so that a stuck
  file cannot consume the whole test-run budget when a limit is requested.

## Business and Functional Requirements

### 1. Standard test-command contract

The standard test and coverage commands must have an observable, documented contract for:

- selecting the parallel test runner;
- selecting the requested number of workers;
- forwarding additional test arguments; and
- enabling coverage behavior for the coverage command.

Automated checks must detect if either command stops honoring any part of this contract.

### 2. Test-runner argument handling

The runner must distinguish its own supported options from additional options intended for
the test framework without silently dropping or reinterpreting valid test arguments. Invalid
runner options must produce a clear, actionable error and a non-successful result.

### 3. Single, consistent coverage setup

Coverage behavior must have one consistent source of truth for worker runs. Unused or
conflicting coverage setup behavior must not remain part of the supported maintenance
surface. A maintainer should be able to understand and change coverage setup without
needing to reconcile duplicate behavior.

### 4. Configurable coverage policy

The minimum coverage policy defined by the project must be applied consistently to the
combined result of a coverage run. Changing that policy in the project configuration must
change the enforced result without requiring a second, disconnected value to be updated.

### 5. Optional per-file execution limit

Users may request a wall-clock limit for each individual test-file execution. When a limit
is requested and exceeded, that file must be reported as unsuccessful and the overall run
must communicate the timeout clearly. When no limit is requested, existing test execution
behavior must remain available.

### 6. Real coverage-threshold verification

The automated suite must exercise the coverage workflow end to end with a deliberately
insufficient result and verify that the run is unsuccessful. It must also demonstrate that
an adequate result is accepted. This check must validate actual coverage enforcement rather
than only a simulated or mocked outcome.

### 7. Invalid worker-value verification

The automated suite must cover invalid worker values, including zero, negative, and
non-numeric input. Each invalid value must be rejected clearly and must not start a test
run with an unusable worker configuration. Valid worker values must remain accepted.

## Scope

### In scope

- The seven requirements above for the parallel test runner and its standard test targets.
- The user-visible contract for worker selection, argument forwarding, coverage enforcement,
  and optional per-file limits.
- Automated checks for command wiring, argument validation, coverage enforcement, and
  invalid worker values.
- Removal or consolidation of inactive coverage behavior where it affects maintainability.
- Documentation and task artifacts needed to describe the resulting supported behavior.

### Out of scope

- Changing the functional behavior of the product under test.
- Reworking unrelated test infrastructure, test selection policy, or CI services.
- Making slow or agent end-to-end test targets parallel unless a separate requirement is
  approved.
- Fixing pre-existing test failures that are unrelated to these seven follow-ups.
- Introducing new coverage goals beyond the project’s agreed policy.

## Constraints and Assumptions

- The repository uses Python for the parallel test runner and its supporting checks.
- Existing standard test commands and valid test-framework arguments are compatibility
  constraints unless a deliberate user-facing change is documented.
- The default behavior must remain usable for callers that do not request an optional
  per-file execution limit.
- Coverage policy changes must be controlled by project configuration rather than duplicated
  undocumented settings.
- Parallel execution can expose resource pressure; the work must preserve clear failure
  reporting and must not treat an invalid worker count as a usable configuration.
- The repository’s Make-only validation policy applies to all verification of these changes.
- This requirements step changes documentation artifacts only; production code and tests are
  not modified as part of this step.

## Main Business Entities

- **Test command**: A standard developer or CI entry point that selects a test mode and
  exposes worker, argument, and coverage options.
- **Test run**: One invocation of the project’s test workflow, with a requested mode,
  arguments, worker configuration, and final success or failure outcome.
- **Worker configuration**: The user’s requested parallel capacity, which must be valid
  before a run begins.
- **Test-file execution**: The independently observable processing of one test file, with a
  result, duration, and optional timeout outcome.
- **Coverage policy**: The project-defined minimum acceptable coverage level applied to the
  combined coverage result.
- **Coverage result**: The measured outcome of a coverage-enabled test run, including whether
  it satisfies the coverage policy.
- **Runner report**: The information presented to a developer or CI operator about selected
  settings, file outcomes, validation errors, timeouts, and the overall result.

## User Scenarios

### Standard parallel test run

1. A developer invokes the standard test command with a chosen worker count and additional
   test arguments.
2. The runner uses the requested settings and forwards the additional arguments.
3. The developer receives a clear overall result and enough information to act on failures.

### Invalid worker configuration

1. An operator supplies zero, a negative number, or a non-numeric worker value.
2. The runner rejects the configuration before starting test work.
3. The operator receives an actionable error and a failure status.

### Coverage policy change

1. A maintainer changes the project’s configured minimum coverage policy.
2. A coverage-enabled run applies the changed policy to its combined result.
3. The result reflects the configured policy without requiring a duplicate setting.

### Per-file timeout

1. An operator requests an individual test-file wall-clock limit.
2. A file exceeds that limit.
3. The runner identifies the file as timed out, reports the outcome clearly, and returns an
   unsuccessful overall result.

### Coverage threshold regression check

1. Automated validation runs a coverage scenario below the configured policy.
2. The run is rejected with a coverage-related failure.
3. An adequate coverage scenario is accepted, proving both sides of the policy boundary.

## Non-Functional Requirements

- **Reliability**: Results must be deterministic enough for developers and CI to trust the
  command contract and coverage outcome.
- **Maintainability**: There must be no avoidable duplicate or inactive coverage behavior
  that can drift from the supported workflow.
- **Usability**: Validation errors and per-file timeout outcomes must identify the corrective
  action or affected file without requiring source-code inspection.
- **Compatibility**: Existing valid test invocations must continue to work unless a changed
  behavior is explicitly documented and accepted.
- **Performance**: Optional per-file limits must prevent an individual stuck file from
  delaying the run beyond the requested bound, subject to normal process-cleanup overhead.
- **Verifiability**: The seven follow-ups must be covered by automated checks that exercise
  their user-visible outcomes.

## Definition of Done

The requirements are complete when the following acceptance criteria are met:

- The standard test and coverage command contracts are covered by automated checks for runner
  selection, worker forwarding, argument forwarding, and coverage mode.
- Valid test-framework arguments continue to reach the test framework, while unsupported
  runner options fail clearly.
- Coverage setup has no unused or conflicting supported path, and its behavior is consistent
  across worker executions.
- The enforced minimum coverage level is read from the project policy and is applied to the
  combined coverage result.
- The optional per-file wall-clock limit is accepted, produces a clear failure for an
  over-limit file, and does not alter behavior when omitted.
- Automated validation demonstrates both rejection below the coverage policy and acceptance
  at or above the policy using a genuine coverage run.
- Automated validation rejects zero, negative, and non-numeric worker values before work
  begins, while accepting valid positive values.
- Documentation identifies supported usage and the observable failure outcomes.
- No production code or tests are changed during this requirements-only step.

## Q&A

### Why is this work needed?

The parallel runner is valuable only when its commands, worker settings, and coverage results
are dependable. The seven follow-ups address gaps that could cause silent argument drift,
invalid runs, inconsistent coverage enforcement, or unbounded waits, increasing maintenance
risk for both developers and CI operators.

### What is the implementation language?

Python, matching the existing parallel test runner and repository tooling.

### Which follow-ups are included?

The scope is limited to the seven follow-ups named in PYPOST-1153: standard command contract
checks, argument handling, coverage setup consolidation, configurable coverage policy,
optional per-file timeout, real coverage-threshold verification, and invalid worker-value
verification.

### Does this step implement the follow-ups?

No. This step defines the expected business and user outcomes. Production changes and test
changes belong to later workflow steps after requirements acceptance.

### What happens to unrelated existing failures?

They remain outside this task unless they directly prevent verification of one of these seven
requirements. Any such baseline condition must be identified and tracked separately.

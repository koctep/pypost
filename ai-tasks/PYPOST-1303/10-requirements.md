# PYPOST-1303: Test source quality feedback through normal Make gates

## Goals

Developers and CI maintainers need routine quality checks to detect defects in test sources
as well as application sources. Catch unused imports and other maintainability regressions
before they accumulate, while retaining current production checks and automated coverage.

## User Stories

- As a developer, I receive actionable test-source quality feedback from the normal Make
  quality workflow without remembering an additional manual command.
- As a reviewer, I can identify new test quality regressions before accepting a change.
- As a CI maintainer, I can adopt the expanded quality scope without hiding production
  regressions or reducing the tests that verify application behavior.
- As a test maintainer, I can understand any permitted legacy exceptions and distinguish
  accepted existing debt from new failures.

## Definition of Done

1. The normal Make lint workflow checks Python test sources in addition to its existing
   production scope; the combined Make quality gate includes that test-source check.
2. A representative unused import in test sources is detected and causes a failing quality
   result with an actionable file location. Clean test sources pass that check.
3. Existing test findings are corrected or covered by explicitly documented, justified legacy
   exceptions. New findings outside those exceptions continue to fail the gate.
4. Exceptions for test-specific behavior do not weaken existing production lint protection.
   They remain narrow enough to retain meaningful test-source quality feedback.
5. Existing production lint checks, documentation checks, automated test assertions, timeout
   protections, and test inclusion remain supported without reduction in coverage.
6. The normal Make quality gate completes successfully, or unrelated baseline failures are
   identified with reproducible evidence under the sprint's failure-triage procedure.
7. Developers can discover the expanded quality scope and the reason for each retained legacy
   exception in the project's developer documentation.

## Task Description

### Problem and business reason

The current Make lint scope checks application Python sources but omits test Python sources.
Unused test imports therefore escape the workflow developers and CI already use. Other
existing test findings, including long lines and intentional print output, need a deliberate
adoption policy so the new scope delivers useful feedback rather than hiding fresh defects.

The issue's business reason is to catch test quality regressions through normal Make gates
while preserving existing production lint and automated test coverage. This debt issue is
limited to that quality feedback gap.

### Implementation language

Python.

### Scope

- Quality feedback for Python test sources through the repository's normal Make workflow.
- Resolution or justified treatment of legacy test quality findings encountered during adoption.
- Regression verification of detection, clean-source success, and production protection.
- Developer documentation of the expanded scope and retained exceptions.

### Out of scope

- Application feature changes or broad test behavior rewrites.
- Reducing production checks, removing tests, or relaxing existing test deadlines.
- Unrelated refactoring, dependency upgrades, or repository-wide quality policy redesign.

### Functional requirements

- Routine lint and combined quality runs include test-source quality feedback automatically.
- A newly introduced unused test import produces a failing, actionable result.
- Test-source feedback identifies the affected file and finding clearly enough to fix it.
- Any legacy exception has a recorded reason and a limited scope; findings outside that scope
  remain visible and enforceable.
- Production quality protection and automated behavioral verification remain effective.

### Non-functional requirements and constraints

- Checks remain repeatable and suitable for developer and CI use.
- The adoption policy preserves meaningful detection rather than masking all test findings.
- Every build, lint, test, dependency, and artifact-verification operation uses Make targets.
- Changes remain within PYPOST-1303 scope and preserve unrelated files and completed task records.
- Existing tests retain their assertions, inclusion rules, coverage expectations, and deadlines.

### Main entities

- **Test source**: Python files supporting automated behavioral verification and maintenance.
- **Quality finding**: an actionable source location and category requiring correction or an
  explicitly justified exception.
- **Legacy exception**: a limited, documented allowance for accepted existing test-source debt
  or intentional test behavior.
- **Quality gate run**: the routine developer or CI workflow that reports success or failures
  across existing production checks and the expanded test-source scope.

## Q&A

- **Why expand quality checks?** Unused imports and other test quality regressions currently
  escape the normal workflow, increasing maintenance burden and reducing reviewer confidence.
- **Must every historical finding be fixed immediately?** No. The issue permits corrections
  or justified legacy exceptions, provided the resulting gate continues detecting new defects.
- **May test-specific allowances weaken production checks?** No. Existing production lint
  protection and automated coverage must remain effective.
- **Who accepts these requirements?** The autonomous sprint orchestrator after independent review.

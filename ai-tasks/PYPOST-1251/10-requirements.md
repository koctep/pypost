# PYPOST-1251: Resolve MainWindow alert-reload test SIGSEGV

## Goals

Determine and address the pre-existing native crash that can terminate the alert-reload test
process with `SIGSEGV` instead of producing a reliable test result. The business goal is to make
the test signal trustworthy and to reduce the risk that alert configuration changes or application
shutdown can expose an equivalent stability problem in the desktop application.

The work must distinguish a defect owned by PyPost from a limitation in the Qt/PySide runtime or
test environment. The outcome must be supported by reproducible evidence and must not hide a crash
behind a weaker test or an ignored failure.

## User Stories

- As a maintainer, I want the alert-reload test to complete with a reliable result so that I can
  tell whether alert configuration behavior is healthy.
- As a CI owner, I want native process crashes to be detected and classified so that a passing or
  failing build accurately represents repository health.
- As a desktop-app user, I want changing alert settings and continuing to use the application to
  remain stable, including after alert activity is written to its configured destination.
- As a release manager, I want environment-specific limitations documented clearly so that native
  crash risk is understood before shipping or changing supported runtime combinations.

## Functional Requirements

1. The task must establish whether the reported crash can be reproduced in the available supported
   execution environment and whether it is associated with PyPost behavior or an external runtime
   boundary.
2. The alert-reload scenario must preserve its observable behavior when alert settings change:
   the previous alert service is retired, the replacement uses the saved settings, and active UI
   consumers receive the replacement.
3. When alert-related settings do not change, the scenario must not report an unnecessary reload
   and the existing alert service must remain usable.
4. Alert records created before and after a settings change must remain attributable to the correct
   configured destination; changing destinations must not lose or misroute records.
5. A crash classification must identify the affected lifecycle boundary, the environments tested,
   and the evidence supporting the conclusion.
6. If the issue is PyPost-owned, the completed work must provide deterministic regression coverage
   for the identified failure condition. If it is environment-specific, the limitation and clear
   guidance for supported environments must be recorded.

## Definition of Done

- [ ] The reported process crash is reproduced, ruled out under bounded supported-environment
  attempts, or otherwise classified with explicit evidence.
- [ ] The classification states whether PyPost behavior or an external runtime/environment is the
  responsible boundary, without treating an unverified suspicion as the conclusion.
- [ ] The alert-reload behavior remains covered for changed settings, unchanged settings, consumer
  propagation, and records written before and after a destination change.
- [ ] A deterministic regression or an evidence-backed environment limitation is documented,
  including what future maintainers should do if the crash appears in supported CI.
- [ ] No unrelated alert behavior, user settings, or test scenarios are weakened or removed.
- [ ] The required repository quality checks pass, or any pre-existing unrelated failures are
  recorded separately with their scope and evidence.

## Scope and Boundaries

### In Scope

- The native process crash reported for the alert-reload test scenario.
- The lifecycle exercised when alert settings are saved, the alert service changes, UI consumers
  are updated, and alert records are emitted.
- Reproduction, ownership classification, regression protection, and developer-facing evidence.
- Supported runtime and operating-system combinations available for verification.

### Out of Scope

- Redesigning alert delivery, webhook authentication, logging formats, or settings unrelated to
  the crash.
- Changing the user-visible meaning of alert settings.
- Reopening unrelated historical Qt crash investigations.
- Provisioning an unavailable operating system or runtime solely to manufacture a reproduction.
- Broad refactoring or changes outside the Jira issue's crash and alert-reload scope.

## Constraints and Assumptions

- The issue is a pre-existing Debt item in sprint 1983 and is not assumed to be caused by the
  current work until evidence establishes that relationship.
- The repository's supported CI environment is the reference point for deciding whether the crash
  threatens normal project verification.
- Native process termination must be treated as a reliability failure even when preceding test
  assertions appear to pass.
- Evidence must remain reproducible and must identify limits such as platform, interpreter, and
  GUI-runtime availability.
- Existing successful alert-reload behavior is a compatibility constraint.

## Main Entities

- **Alert Settings** — the user's saved alert destination and related configuration values.
- **Alert Service** — the active component responsible for accepting and routing alert records.
- **Alert Record** — a structured event emitted by the application and written to the configured
  destination.
- **Main Application Window** — the user-facing owner of settings changes and active UI services.
- **UI Consumer** — an open application area that must continue using the active alert service.
- **Reload Lifecycle** — the observable sequence from saving changed alert settings through service
  replacement and continued alert use.
- **Execution Environment** — the operating-system, interpreter, GUI runtime, and test-process
  combination in which behavior and crashes are observed.
- **Crash Evidence Record** — the reproducible observations, environment details, and ownership
  conclusion maintained for future diagnosis.

## Non-Functional Requirements

- **Reliability:** The affected test process must not terminate unexpectedly during the covered
  lifecycle on supported environments.
- **Diagnosability:** A failure must leave enough evidence to distinguish an assertion failure,
  process crash, and environment-specific native-runtime failure.
- **Determinism:** Regression coverage must produce repeatable results and avoid dependence on
  timing races wherever the behavior can be controlled.
- **Compatibility:** Existing alert settings and alert-record semantics must remain unchanged.
- **Maintainability:** The final evidence and guidance must be understandable to maintainers who
  did not observe the original crash.
- **Scope control:** Changes must remain limited to PYPOST-1251's alert-reload crash boundary.

## Q&A

- **Q: Why is this a separate task from ordinary alert-reload behavior?**
  **A:** The Jira issue concerns a native `SIGSEGV` that can end the test process after or during
  the alert-reload lifecycle. A native crash is a reliability and verification concern even when
  individual behavioral assertions are otherwise meaningful.
- **Q: What must happen if the crash cannot be reproduced here?**
  **A:** Record the bounded attempts, exact environment, relevant prior evidence, and the resulting
  limitation. Do not claim the defect is fixed solely because one run completes successfully.
- **Q: Is a behavior change to alert settings required?**
  **A:** No. The existing observable settings, reload, propagation, and record-routing behavior is
  the compatibility baseline; this task addresses stability and trustworthy verification.

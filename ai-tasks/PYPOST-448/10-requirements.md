# PYPOST-448: Make hidden-key name logging configurable

## Goals

Close the observability gap introduced after `PYPOST-437`: hidden-flag toggle events
currently write variable key names to application logs. Some organizations prohibit logging
identifying variable names even when values are masked.

This task must let users choose whether key names appear in those logs, while preserving
useful diagnostics for teams that rely on key-name visibility.

## Programming Language

Python 3.10+

## User Stories

- As a security-conscious user, I want to suppress or anonymize variable key names in
  hidden-flag toggle logs so the application complies with my organization's logging policy.
- As a developer or support engineer, I want the option to keep key names in toggle logs so
  I can diagnose environment configuration issues.
- As an application user, I want hidden-flag behavior in the UI to work the same regardless
  of how logging is configured.

## Definition of Done

- A user-configurable setting controls whether variable key names appear in hidden-flag
  toggle logs.
- At least two logging modes are supported: full key-name visibility and
  suppression/anonymization of key names.
- The default mode is suppression/anonymization of key names (option b); users may opt in to
  full key-name visibility.
- Hidden-flag UI behavior and persistence are unchanged.
- Variable values are never written to logs (inherited constraint from `PYPOST-437`).
- Acceptance tests cover both logging modes.
- User-facing documentation of expected logging behavior is updated before the task is
  closed.

## Task Description

This task is a follow-up to `PYPOST-437`, which introduced the hidden flag for environment
variables and added observability logging when the flag is toggled. That logging includes
the variable key name, environment name, and hidden state. Values are not logged.

`PYPOST-446` addressed masking of hidden-derived values in history and related log surfaces.
`PYPOST-447` addressed encryption of sensitive values at rest. Neither task covers
configurable treatment of key names in hidden-flag toggle observability logs.

### In Scope

- Requirements for a user setting that controls key-name visibility in hidden-flag toggle
  logs.
- Requirements for at least two distinct logging modes (visible key names vs
  suppressed/anonymized key names).
- Requirements for a safe default: key names suppressed/anonymized unless the user enables
  full visibility.
- Requirements for tests that verify both modes.
- Requirements ensuring UI hidden-flag behavior is unaffected.

### Out of Scope

- Masking of hidden-derived values in history or request logs (`PYPOST-446`).
- Encryption of environment values at rest (`PYPOST-447`).
- Changes to hidden-flag UI, preview masking, or variable list display.
- Logging policy for events other than hidden-flag toggles.
- Architectural or implementation choices for how anonymization is performed.

## Functional Requirements

- The system must allow the user to choose a logging policy for variable key names when a
  hidden flag is toggled.
- By default, key names must not appear in toggle logs in readable form (safe default for
  org-policy alignment).
- Users who need diagnostics may enable full key-name visibility explicitly.
- In suppression/anonymization mode, the variable key name must not appear in the log in a
  readable form.
- In full-observability mode, toggle logs must retain current informativeness: environment
  name, key name, and hidden state, without variable values.
- Changing the setting must affect only subsequent toggle log events.
- Hidden-flag toggle behavior, variable persistence, and UI display must not depend on the
  logging setting.

## Non-functional Requirements

- Security: reduce the risk of leaking identifying metadata (variable key names) through
  logs.
- Compliance: support organization policies that prohibit logging names of sensitive
  variables.
- Backward compatibility: the default changes from current behavior (key names visible) to
  suppressed/anonymized key names; this intentional security-first default must be documented
  so existing users can enable full visibility if needed.
- Usability: the setting must be understandable without knowledge of internal implementation.
- Maintainability: both logging modes must be verifiable through automated tests.

## Constraints and Assumptions

- PyPost is a desktop Python application.
- Hidden-flag toggle logging already exists from `PYPOST-437`.
- Variable values must not be logged and must not start being logged as part of this task.
- Step 1 defines requirements only; the specific anonymization mechanism is decided in
  Step 2.
- Project-wide markdown and line-length rules apply to all generated artifacts.

## Main Entities and Interactions (Business View)

- Hidden variable: a user-managed environment variable marked as sensitive.
- Hidden-flag toggle event: the user action of checking or unchecking the hidden flag.
- App settings: user-configurable application preferences, including the logging policy.
- Log entry: diagnostic output produced when a hidden flag is toggled.
- Environment: the named context in which the variable belongs.

Interactions:

1. The user toggles the hidden flag on a variable.
2. The application records a diagnostic log entry for the event.
3. The logging policy setting determines whether the variable key name is visible in that
   entry.
4. UI and data persistence proceed independently of the logging policy.

## Q&A

- Q: Why is this task needed if `PYPOST-446` already addressed hidden-variable logging?
  A: `PYPOST-446` defined masking for values derived from hidden variables in history and
  related surfaces. This task addresses **key names** in observability logs emitted when the
  hidden flag itself is toggled.
- Q: What is the safe default?
  A: **(b) Suppress key names by default** (approved at Step 1 review). Rationale: the task
  addresses org policies that prohibit logging identifying variable names; security-first
  out-of-box behavior takes priority over preserving current log verbosity. Users who need
  key names for diagnostics can enable full visibility in app settings.
  - (a) Rejected: preserve current behavior (key names visible) — weaker default for
    compliance-sensitive deployments.
- Q: What is the difference between "suppress" and "anonymize"?
  A: At Step 1, both are acceptable as modes where the key name is not revealed in readable
  form. The concrete mechanism is an architecture decision for Step 2.
- Q: Does this task change what users see in the UI?
  A: No. Only diagnostic log output for hidden-flag toggle events is in scope.
- Q: Source ticket?
  A: [PYPOST-448](https://pypost.atlassian.net/browse/PYPOST-448)

# PYPOST-1039: Optional secret-gated live Jira MCP smoke

## Goals

PyPost maintainers need a small, trustworthy live check for the Jira MCP
example so that authentication, request-template, and Jira-addressing
regressions are found before users encounter them.  The check must be optional:
contributors and ordinary pull-request validation must continue to succeed when
Jira credentials are unavailable.

**Programming language:** Python

## User Stories

- As a **maintainer with authorized Jira test credentials**, I want to run a
  small live smoke against the Jira MCP example so that I can detect whether
  its core read-only operations work with a real Jira site.
- As a **contributor without Jira credentials**, I want normal local and
  pull-request validation to remain successful, so I can contribute without
  access to a shared external service.
- As a **repository administrator**, I want to enable the live smoke with
  protected configuration, so credentials are never exposed in source code,
  examples, logs, or developer documentation.
- As an **MCP user**, I want maintainers to catch live authentication and
  request-argument regressions early, so the documented Jira MCP example
  remains dependable in real use.

## Definition of Done

- [ ] Authorized maintainers have a clearly documented opt-in way to run the
      live smoke locally and, where enabled, in protected CI.
- [ ] The smoke verifies only a small read-only Jira MCP subset: current-user
      lookup, issue search, issue retrieval, and board listing.
- [ ] Default local tests and ordinary PR CI do not require Jira access and do
      not fail merely because live-smoke configuration is absent.
- [ ] All committed example and configuration values remain placeholders; no
      real Jira URL, email address, token, credential pair, or other secret is
      added to the repository.
- [ ] The live smoke's outcome clearly distinguishes an intentionally skipped
      run (configuration absent) from a failed authorized run.
- [ ] Documentation explains the needed configuration by name and the
      read-only nature of the smoke without revealing credential values.

## Task Description

**Problem:** Offline fixture checks did not expose the prior MCP request
substitution defect (PYPOST-1033) until manual testing against a real Jira
service.  Consequently, maintainers have no small automated signal for whether
the Jira MCP example can authenticate and perform its core read-only operations
against an authorized real service.

**Business outcome:** Maintainers can deliberately validate the real Jira MCP
example when protected credentials are available, while routine development and
CI remain independent of those credentials.  This makes regressions visible
earlier without widening access to sensitive data or risking changes to Jira.

### In Scope

- An opt-in, secret-gated live smoke that an authorized maintainer can invoke
  locally and/or from protected CI.
- A small read-only verification of the Jira MCP example: current user, search,
  issue retrieval, and board listing.
- Clear documentation for enabling the protected configuration locally and in
  CI, including behavior when it is absent.
- Preservation of committed placeholder values and protection of sensitive
  configuration from repository history and observable test output.

### Out of Scope

- A live test of every Jira MCP tool on every pull request.
- Any Jira operation that creates, updates, transitions, assigns, comments on,
  logs work against, or otherwise changes Jira data.
- Changes to Jira project access policy, credentials, or the Atlassian MCP
  service itself.
- Unrelated project-lock, type-conversion, or schema work.

## Functional Requirements

- The opt-in smoke must be executable only when an authorized maintainer has
  supplied the required protected configuration.
- When authorized configuration is supplied, the smoke must confirm that the
  Jira MCP example can complete the defined read-only operations against the
  configured Jira site.
- When that configuration is not supplied, normal test and PR workflows must
  complete successfully and identify the live smoke as intentionally skipped
  rather than report a false failure.
- The smoke must not perform operations that modify Jira data.
- Setup guidance must state which configuration inputs are required, using
  names such as `JIRA_BASE_URL` and `JIRA_CREDENTIALS` only as non-secret
  labels, never values.

## Non-functional Requirements

- **Security:** No credential, account identifier, token, authorization value,
  or real service configuration may be committed or deliberately emitted in
  logs, failures, test reports, or documentation.
- **Safety:** The smoke is strictly read-only and safe to rerun against the
  authorized Jira site.
- **Reliability:** An authorized execution must produce a clear pass or fail
  result for the defined subset; missing authorization produces a clear skip.
- **Compatibility:** Existing default local validation and PR CI remain usable
  without Jira secrets.
- **Maintainability:** The scope stays deliberately small and the enabling
  instructions are understandable to a maintainer setting up a new environment.

## Constraints and Assumptions

- Jira credentials and service settings are managed as protected local or CI
  configuration, not versioned repository content.
- Authorized maintainers have access to a Jira site and an account permitted to
  perform the read-only operations named above.
- Existing offline fixtures remain valuable and continue to cover behavior that
  does not require a live Jira service.
- The task is a Story (priority Medium; labels `ci`, `examples`, `mcp`, and
  `testing`; story points 5) in the active MCP Jira Server Hardening sprint.
- Python is the repository's implementation and test language.

## Main Entities

| Entity | Description |
| --- | --- |
| Authorized maintainer | Person permitted to use protected Jira configuration for an opt-in validation run. |
| Contributor | Person who runs normal development checks without access to Jira secrets. |
| Repository administrator | Person who configures protected CI variables and decides where the opt-in smoke is enabled. |
| Jira MCP example | The documented PyPost example whose live read-only behavior is being validated. |
| Protected configuration | Non-versioned service address and credentials required for an authorized live run. |
| Live smoke result | A clear pass, failure, or intentional skip outcome for the restricted read-only check. |
| Jira service | The authorized external service queried by the read-only smoke. |

## Q&A

| Question | Answer |
| --- | --- |
| Why is a live smoke needed when offline checks exist? | Offline fixtures missed the PYPOST-1033 request-substitution regression. A small authorized live check provides complementary evidence for authentication, request handling, and service addressing. |
| Why is this optional? | Routine contributors and PR checks must not depend on confidential Jira access or an external service. |
| What operations may the smoke perform? | Only current-user lookup, issue search, issue retrieval, and board listing. They are read-only. |
| Can the smoke alter Jira data? | No. Creating, modifying, transitioning, assigning, commenting, work logging, and other write actions are expressly excluded. |
| How are secrets represented in the repository? | Only descriptive configuration names and committed placeholders may appear. Real values must remain protected and outside version control. |
| Does this require a complete live matrix? | No. The task intentionally limits coverage to a small, representative read-only subset. |

## STEP 1 Approval Basis

The applicable `sprint-runner` workflow explicitly runs autonomously and
preauthorizes progression without a separate user gate.  STEP 1 is complete
only after an independent review confirms that these requirements describe the
business contract without embedding architecture or secret values.

# PYPOST-1032: Soft-scope jira-mcp examples to one project

## Programming Language

English Markdown for reader guidance; structured example data may use JSON if
later design confirms it is needed. No application feature implementation is
in scope.

## Goals

The importable Jira MCP example pair is intended to help people and agents
work productively in a chosen Jira project. Today, a broadly configured
example can leave agents without a clear default project, increasing the risk
of searching or creating work in the wrong project.

**Business goal:** give an example user a clear, project-specific default that
guides normal agent and MCP activity toward their chosen Jira project, while
retaining the Jira account's existing permissions and the ability to work
outside that project when the user deliberately chooses to do so.

This is guidance, not access control. It must never be represented as a Jira
security boundary or as a replacement for permission management.

## User Stories

- As an **example user**, I want to set one obvious project value when I
  import the Jira MCP examples, so common agent actions begin in the project I
  intend to use.
- As an **agent operator**, I want search, issue creation, and supported list
  actions to favor the selected project, so the agent has a safer default
  without losing authorized cross-project work.
- As a **reader of the examples documentation**, I want to understand that
  the project default is soft guidance rather than a permission lock, so I do
  not rely on it for security or isolation.

## Definition of Done

- [x] Users can choose one clear project default when they import the Jira
      examples.
- [x] Normal issue search and issue creation begin from that selected project.
- [x] Supported list workflows begin from the selected project; workflows
      that Jira does not support for project scoping remain usable and clearly
      communicate that they are not project-scoped by this guidance.
- [x] Agent-facing descriptions, input guidance, and examples documentation
      state that the project setting is soft guidance, not a hard Jira
      permission restriction or security boundary.
- [x] The examples contain placeholders only, with no real Jira credentials,
      project data, or personal secrets committed to the repository.
- [x] Existing users can still intentionally work in another Jira project if
      their Jira permissions allow it.
- [x] No hard Jira permission model, dedicated bot-account policy,
      Atlassian MCP server configuration, or full collection expansion is
      introduced by this task.

## Task Description

**Problem:** The Jira MCP example collection offers a useful importable
starting point, but it does not give agents a consistent default project for
their day-to-day Jira actions. In a multi-project Jira account, this can
produce ambiguous searches and incorrectly targeted new issues.

**Requested outcome:** The Jira examples should give users one configurable
project default. The key everyday actions should begin from that preference
where Jira supports it. Documentation and agent-facing guidance must make the
limit explicit: the setting helps choose the likely project; it does not
enforce authorization or prevent a permitted user from accessing another
project.

**Scope (in):**

- A user-selectable project default in the existing Jira examples.
- Project-default guidance for the existing Jira MCP collection's high-value
  search, create, and supported list workflows, as defined below.
- Clear user and agent documentation for the distinction between a project
  default and a hard permission lock.

**Scope (out):**

- Enforcing project isolation with Jira permissions, a dedicated account, or
  another security control.
- Changing the configured external Atlassian MCP server.
- Expanding the collection to every Jira capability.
- Redesigning native example import formats or building a new product
  capability.

## Business Boundary and Decision Rules

- **High-value actions** are the routine work actions that can otherwise be
  sent to the wrong project: issue search, issue creation, and the existing
  board or issue-list retrieval workflows. Administration, authentication,
  permission management, server configuration, and project-management actions
  are not high-value actions for this task and remain out of scope.
- **Supported list workflows** are existing board or issue-list retrieval
  workflows for which Jira can meaningfully apply the selected project without
  changing the user's requested type of information. A workflow that cannot
  be project-scoped remains available without that default and must be
  described as such; it must not be represented as project-scoped.
- **Jira support** means the relevant Jira capability permits the selected
  project to guide the action while preserving its normal purpose. Where Jira
  does not provide that capability, the project default must not be presented
  as applying, simulated as a security control, or used to restrict otherwise
  authorized cross-project work.

## Main Entities and Interactions

- **Example user** — imports the Jira examples and selects the project that
  represents their normal work area.
- **Project default** — the user-supplied value that expresses the preferred
  Jira project.
- **jira-mcp example collection** — the importable agent-facing Jira actions
  that use the preferred project for applicable everyday work.
- **Companion Jira examples** — the importable settings and actions through
  which the user selects and uses the project default.
- **Agent or MCP client** — consumes the examples and follows the guidance
  when searching, creating, or listing Jira information.
- **Examples documentation** — tells readers how to choose the project and
  explains the setting's non-security nature.
Interaction: an example user selects a normal Jira project → the imported
examples guide the agent's applicable actions to that project → the agent can
still perform deliberately requested, authorized work elsewhere → the
documentation prevents the default from being mistaken for access control.

## Non-Functional Requirements

- **Security clarity:** language must consistently distinguish soft guidance
  from access control; the project default is not a security feature.
- **Secret safety:** committed example values must be obvious placeholders;
  no real tokens, passwords, account details, or customer project data.
- **Importability:** users can continue to use the existing companion
  examples through their normal import experience.
- **Discoverability:** users can find how to select a project and understand
  its limitations from the examples guidance.
- **Compatibility:** the change preserves the existing collection's purpose
  and does not prohibit authorized multi-project use.

## Constraints and Assumptions

- The existing importable Jira examples are the baseline for this work.
- The selected project is example configuration rather than a committed
  customer project identifier.
- The project default applies only where the relevant Jira capability supports
  it, as defined in the business decision rules above.
- Jira itself remains the authority for authentication and authorization.

## STEP 1 Approval Basis

The applicable `sprint-runner` workflow explicitly runs its phases in
autonomous mode and preauthorizes continuing without a separate confirmation
between phases. That explicit autonomous preapproval is the approval basis for
this completed requirements step.

## Q&A

**Q: Why is this needed if Jira already has permissions?**

**A:** Permissions determine what an account may access; they do not tell an
agent which of several permitted projects is the normal intended destination.
The default reduces accidental ambiguity in routine work.

**Q: Is the selected project a security lock?**

**A:** No. It is a convenience and agent-guidance default only. Jira
permissions remain the sole authorization mechanism, and authorized users can
intentionally work in other projects.

**Q: Which actions should be guided?**

**A:** Everyday actions where a preferred project is meaningful: issue search,
issue creation, and supported board or list actions. Actions that Jira cannot
filter by project keep their normal behavior.

**Q: Does this replace or reconfigure the external Atlassian MCP server?**

**A:** No. The task only improves the importable PyPost examples; external
Atlassian MCP configuration remains out of scope.

**Q: What must never appear in the examples?**

**A:** Real credentials, private account information, or a customer's actual
project key.

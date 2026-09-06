# PYPOST-1283: Unify jira-create-issue collection item and add MCP environment variable override policy

## Goals

pypost lets users build HTTP request collections either by hand in the GUI or by exposing a
request as a tool an AI agent can call over MCP. Two separate gaps currently force users into
awkward or unsafe workarounds:

1. **The bundled "Jira Create Issue" example is unusable from the GUI.** It was written only for
   MCP/agent use: to create an issue, the caller must hand-assemble a complete, pre-serialized
   Jira issue body, including a rich-text description already encoded in Atlassian Document
   Format (ADF) — a nested JSON structure most human users don't know and shouldn't need to
   learn. A regular GUI user opening this example and trying to fill in a title and description
   by hand cannot do so; the example collection is effectively agent-only, which defeats the
   purpose of shipping it as a general-purpose, dual-use example.
2. **There is no permission model for which environment variables an MCP agent may override at
   call time.** Today the choice is all-or-nothing: either every environment variable an agent
   references becomes overridable, or none can be. All-or-nothing is unsafe in one direction
   (an agent could override `jira_base_url` and redirect a request to an attacker-controlled
   host — a server-side request forgery risk) and unworkable in the other (a legitimate,
   low-risk case like letting an agent target a different `jira_project_key` per call is blocked
   along with everything else). Users need a way to say, per environment variable, "an agent
   may override this at call time" without opening the door to overriding sensitive values such
   as base URLs or credentials.

Fixing both closes the gap between "works for a human in the GUI" and "works for an agent over
MCP" for the bundled Jira example, and gives users explicit, auditable control over what an agent
is allowed to change about a request's execution environment.

## Programming Language

- **Implementation language**: Python (per `ai-tasks/PYPOST-1283/00-roadmap.md`), as required by
  the existing PyPost product — this is a PyQt-based desktop app; GUI widgets are Python/Qt, not a
  separate language.

## User Stories

- As a GUI user filling in the bundled Jira Create Issue request by hand, I want to type a plain
  project key, issue type, summary, and description, so that I can create a Jira issue without
  knowing Atlassian Document Format or hand-writing JSON.
- As an agent operator using the same Jira Create Issue tool over MCP, I want the tool to keep
  accepting a fully custom issue payload for cases the structured fields don't cover, so that
  advanced or unusual issue creation is not blocked by the new GUI-friendly path.
- As a collection author, I want a way to convert a plain-text description into Jira's expected
  rich-text document format from within a request definition, so that a human's plain-text input
  can still be sent to Jira Cloud correctly regardless of whether the request came from the GUI
  or from an agent.
- As an environment author, I want to mark specific environment variables as overridable by MCP
  tool callers, so that an agent can, for example, target a different project key per call.
- As an environment author, I want variables I have not marked overridable to be rejected if an
  agent tries to override them, so that an agent cannot silently redirect requests to a different
  host, credential, or other sensitive destination.
- As an environment author, I want a variable marked "Hidden" to never be overridable by an
  agent, even if I also try to mark it overridable, so that secrets can't leak through an
  override path regardless of how the two settings are combined.
- As an environment author, I want to see and control, at a glance, which of my environment's
  variables an agent is allowed to override, so that I don't have to guess or read code to know
  the current permission state.
- As an agent operator, I want a clear, actionable error when my tool call attempts to override a
  variable that is not permitted, so that I understand why the call was rejected and what is
  allowed instead.
- As the maintainer of the bundled Jira example, I want the shipped example environment to reflect
  sane overridable/non-overridable defaults out of the box, so that a new user gets safe behavior
  without having to configure the permission model themselves first.

## Definition of Done

- A GUI user can open the bundled Jira Create Issue example, fill in ordinary fields (e.g.
  project, issue type, summary, plain-text description) without writing any JSON or ADF by hand,
  and successfully create a Jira issue.
- The same Jira Create Issue tool, called over MCP, still supports providing a complete custom
  issue payload as a fallback for cases not covered by the structured fields, without loss of
  existing agent capability.
- A plain-text description entered by a GUI user or supplied by an agent is delivered to Jira
  Cloud correctly rendered as rich text (not as raw literal text and not causing an API error due
  to malformed document structure).
- Environment variables have a per-variable setting controlling whether an MCP agent may override
  their value at call time; this setting is visible and editable wherever environment variables
  are currently viewed and edited in the GUI.
- A variable marked "Hidden" can never be marked overridable by an agent at the same time — this
  is enforced by the interface (making one setting exclude the other cannot be bypassed by the
  user) and is also true at execution time regardless of how the variable's flags are set.
- An MCP tool call that attempts to override an environment variable not permitted for override
  is rejected with a clear, descriptive error, and the request is not executed with the
  attempted override applied.
- An MCP tool call that overrides a variable that *is* permitted for override succeeds and the
  request executes using the overridden value.
- The bundled example environment for the Jira Cloud collection ships with reasonable default
  override permissions (e.g. project key overridable, base URL and credentials not overridable).
- No existing GUI or MCP behavior for requests/environments unrelated to this change regresses.

## Task Description

**Scope — in:**

- Redesigning the bundled `jira-create-issue` request (in the example Jira MCP collection) so it
  works both as an ordinary GUI-editable request (plain fields, no hand-written ADF/JSON) and as
  an MCP tool an agent can call — including retaining a way for an agent to supply a fully custom
  issue payload when the structured fields aren't sufficient.
- Providing a way for plain text to be converted into Jira's expected rich-text document format,
  so both the GUI path and the agent path can turn a human-readable description into a
  Jira-Cloud-compatible one, without requiring anyone to write ADF JSON by hand.
- Introducing a per-environment-variable permission (override allowed / not allowed) governing
  whether an MCP tool call may override that variable's value at call time.
- Making that permission visible and settable in the environment-variable editing UI, alongside
  the existing per-variable settings (e.g. "Hidden").
- Guaranteeing, both in the UI and at execution time, that a variable marked "Hidden" cannot also
  be marked overridable by an agent.
- Rejecting, with a clear error, any MCP call that attempts to override a variable not permitted
  for override.
- Updating the bundled Jira Cloud example environment to reflect sensible default override
  permissions consistent with the new permission model.

**Scope — out:**

- Any change to Jira's own API, authentication scheme, or the set of Jira operations already
  exposed as MCP tools (only `jira-create-issue` is being reworked for dual use; other Jira
  requests in the collection are unaffected).
- General rework of the environment or MCP permission/config system beyond the single new
  per-variable override permission described here.
- Any change to how collections/environments are stored, synced, imported, or exported, beyond
  what is needed to carry the new per-variable setting.

**Constraints and assumptions:**

- The bundled example must remain usable by a first-time user with no prior Jira ADF knowledge.
- The solution must not weaken the existing protection that already prevents "Hidden" variables
  and other environment-derived values from being exposed to an agent as tool inputs; overridable
  variables are additive to that existing protection, not a replacement for it.
- Default behavior for existing environments that have not been updated with the new setting must
  be safe (i.e. not silently overridable) rather than defaulting open.
- This task covers pypost's own example collection/environment and the underlying permission
  model; it does not cover customer- or user-authored collections, though the same mechanism must
  be usable by them.

## Main Entities

- **Environment** — a named set of variables (base URL, project key, credentials, etc.) selected
  when running a request or collection; each variable already carries a "Hidden" flag and now
  also carries an override permission for MCP tool calls.
- **Collection Request** — a reusable, named HTTP request definition (e.g. "Jira Create Issue")
  that can be run directly from the GUI and/or exposed as a callable MCP tool.
- **MCP Tool Call** — an invocation of a collection request by an AI agent over MCP, which may
  supply values for the request's declared tool inputs and, subject to the new permission model,
  override specific environment variables for that call.
- **Environment Variable Override Permission** — the new per-variable setting describing whether
  an MCP tool call is allowed to override that variable's value; mutually exclusive with the
  variable being marked "Hidden".
- **Jira Issue (rich-text description)** — the business content a user or agent wants to create
  in Jira, including a plain-text description that must be represented as Jira's rich-text
  document format before being sent to Jira Cloud.

## Non-Functional Requirements

- **Security — SSRF avoidance:** The override permission model exists specifically to prevent an
  MCP agent from redirecting a request to an attacker-controlled host or credential. Variables
  such as base URLs and credentials must remain non-overridable unless an environment author
  explicitly opts them in; unrestricted, all-or-nothing overridability is the SSRF risk this task
  closes.
- **Security — secure-by-default override policy:** Existing environments, and any variable that
  has not been explicitly marked overridable, must default to non-overridable. The permission
  model must never default open; safety takes precedence over convenience for unmodified
  environments.
- **Security — Hidden/Override exclusivity:** A variable marked "Hidden" must never be
  simultaneously overridable by an MCP agent. This mutual exclusivity must be enforced both in the
  UI (selecting one setting must exclude the other) and at execution time, independent of how the
  variable's flags were set or stored, so secrets cannot leak through the override path.
- **Performance:** No specific performance requirement applies to this task. The changes (adding
  structured/rich-text fields to one bundled example request and a per-variable permission check
  during MCP override handling) are not expected to introduce a measurable performance concern;
  performance is explicitly out of scope for review purposes.

## Q&A

- Q: Is this a request from a real end user, or a technical/internal improvement?
  A: It originates as a technical request (a specific example collection and a specific env-var
  permission mechanism), but the underlying business reasons are explicit in the Jira
  description and were used directly here: (1) the current example locks out ordinary GUI users
  because it demands hand-authored ADF/JSON, so GUI users cannot use the bundled Jira example at
  all; (2) environment variables have no permission model for MCP overrides today, which is
  simultaneously an SSRF risk (unrestricted override) and a usability blocker (no override at
  all prevents legitimate per-call customization like project key). Both reasons are captured
  above in Goals and Definition of Done.
- Q: Should the fallback path (a fully custom, pre-serialized issue payload) be removed once
  structured fields exist?
  A: No — the Jira summary explicitly calls for "structured fields + fallback to
  issue_payload," so both paths must coexist; removing the fallback would reduce agent
  capability, which is out of scope.
- Q: Should newly created / unmodified existing environments default to overridable or
  non-overridable for variables that don't yet have the new setting?
  A: Non-overridable (secure-by-default), consistent with the stated goal of preventing
  indiscriminate overrides; this is documented under Definition of Done and Constraints above.

# PYPOST-685: Audit — security and secrets handling

## Goals

PyPost stores credentials, resolves them during HTTP and MCP execution, and exposes collection
data to both human operators and external AI agents. Without a structured review of how secrets
and sensitive data are protected across storage, UI, logs, history, and MCP surfaces, the team
risks undetected exposure paths — especially as MCP integration and encryption features evolve.

This audit establishes a shared, evidence-based picture of current secrets and sensitive-data
handling so maintainers can verify documented policies match runtime behavior, prioritize
remediation, and guard new work against regressions.

## Programming Language

Python (audit and analysis task; deliverables are markdown reports and follow-up Jira issues).

## User Stories

- As a **PyPost user**, I want assurance that credentials I mark hidden or encrypt are not
  exposed in places I do not expect (UI, history, logs, agent-visible MCP contracts), so I can
  use the product during screen sharing and with local AI agents without leaking secrets.
- As an **AI agent operator**, I want a clear boundary between data agents may see and data
  reserved for operators, so MCP tool use does not require pasting secrets into agent arguments.
- As a **maintainer**, I want an inventory of secret-handling surfaces and documented policy
  gaps, so security-relevant changes can be reviewed against a known baseline.
- As a **reviewer**, I want audit findings with concrete examples and severity, so pull
  requests that weaken masking, encryption, or MCP filtering are easier to spot.
- As a **tech-debt owner**, I want prioritized follow-up Jira issues for security and secrets
  gaps so remediation can be scheduled alongside feature work.
- As a **product owner**, I want confidence that transport assumptions, collection exposure
  rules, and PII handling are understood and documented, so risk decisions are explicit rather
  than assumed.

## Definition of Done

- [ ] An audit report is stored under `ai-tasks/PYPOST-685/` and is readable without local
  checkout context (summary, scope, methodology note, findings, recommendations).
- [ ] Findings cover environment variable and secret storage (local persistence, UI display,
  agent visibility) as scoped below.
- [ ] Findings cover auth token and credential handling across request execution, persisted
  history, and operational logs.
- [ ] Findings cover MCP tool safety: agent-visible contracts vs operator-only execution data.
- [ ] Findings cover transport security assumptions for outbound HTTP and inbound MCP
  connections.
- [ ] Findings cover PII and sensitive data in logs, persisted history, and on-disk storage.
- [ ] Findings cover the access and exposure model for collections (what may be shared with
  agents vs kept operator-only).
- [ ] Documented security and secrets policies under `doc/dev/` are compared against observed
  behavior; gaps and stale documentation are called out.
- [ ] Each significant finding includes impact (why it matters for user trust or exposure risk)
  and a recommended remediation direction at a high level (not implementation design).
- [ ] Findings are prioritized (e.g. by severity or exposure likelihood) so follow-up work can
  be ordered.
- [ ] Actionable follow-up Jira issues are created for remediation items that should not be
  deferred without explicit decision.
- [ ] Out-of-scope areas are explicitly listed in the audit report so readers know what was not
  reviewed.

## Task Description

**Problem:** PyPost handles secrets at multiple layers — environment variables (including hidden
keys and optional encryption at rest), request templating, history recording, diagnostic logging,
GUI presentation, and network MCP tool exposure. Prior feature work addressed specific surfaces
(e.g. hidden-variable UI masking, history sanitization, MCP schema filtering, encryption at
rest), but there is no consolidated audit verifying end-to-end consistency, documenting
residual risks, or assessing collection-level exposure rules.

**Business intent:** Make secret and sensitive-data handling visible, traceable, and schedulable
as debt — reducing the chance that credentials leak through an unreviewed path during normal
use, MCP agent integration, or support diagnostics.

### In Scope

- **Environment variable and secret storage**
  - How secrets are persisted locally (plain text, encrypted envelopes, key sources).
  - How hidden keys and values are presented in the UI and operator-facing dialogs.
  - What environment data is visible to external MCP clients vs used only at execution time.
- **Auth token and credential handling**
  - How credentials in headers, bodies, and URL templates flow through HTTP execution.
  - Whether resolved secrets can appear in request/response history.
  - Whether operational logs, metrics, activity records, or alerts may contain tokens,
    authorization headers, or hidden key values/names.
- **MCP tool safety**
  - Agent-visible surfaces: `list_tools` schemas, tool descriptions, structured tool results,
    MCP activity logs visible to operators.
  - Operator-only surfaces: execution-time variable merge, hidden env keys, diagnostics with
    richer detail.
  - Alignment with documented MCP secrets policy and operator-vs-agent principle.
- **Transport security assumptions**
  - Documented and de-facto assumptions for outbound HTTP (TLS verification, cleartext use).
  - Inbound MCP server exposure (bind address, local vs network reachability, transport modes).
- **PII and sensitive data in logs, history, and storage**
  - Request history contents after masking policies are applied.
  - Log and metric fields that may carry user or third-party data.
  - On-disk collection and environment files beyond encrypted hidden values.
- **Collection access and exposure model**
  - Which requests are exposed as MCP tools and how collection boundaries apply.
  - Whether agents can reach requests or data the operator did not intend to expose.
- Written audit deliverables and follow-up Jira issues for remediation.

### Out of Scope

- Implementing security fixes or refactors (audit only).
- Full penetration testing, formal threat modeling workshops, or compliance certification
  (e.g. SOC 2, GDPR assessment).
- Re-auditing package boundaries or SOLID maintainability except where they directly affect
  secrets handling (see PYPOST-684 and PYPOST-40).
- Performance profiling, UI/UX review unrelated to sensitive-data display, or dependency
  version upgrades.
- Defining the target future security architecture (reserved for Step 2+ if remediation tasks
  require it).

## Functional Requirements

- The audit must produce a structured written report suitable for developers, reviewers, and
  product stakeholders.
- The audit must state the reviewed scope (capability areas, persistence surfaces, integration
  paths, and reference documents).
- The audit must document secret and sensitive-data findings with enough context to locate them
  in the repository.
- The audit must assess whether documented policies in `doc/dev/` match observed behavior for
  hidden variables, history masking, environment encryption, MCP secrets filtering, and
  related logging policies.
- The audit must trace credential and token handling from storage through execution to history,
  logs, and MCP responses.
- The audit must assess the operator-vs-agent visibility model for MCP tools and whether
  execution-only data can leak via schemas, results, or diagnostics.
- The audit must state transport security assumptions and note where the product relies on
  operator-controlled network posture.
- The audit must assess collection exposure rules (`expose_as_mcp` and related controls) for
  unintended agent access to sensitive requests.
- The audit must include prioritized recommendations and create Jira follow-ups for items
  warranting tracked remediation.

## Non-Functional Requirements

- **Clarity:** Findings must be understandable to a developer new to PyPost's secrets policies.
- **Actionability:** Recommendations must be specific enough to become tickets; avoid vague
  "improve security" statements.
- **Traceability:** Report and follow-up issues link back to PYPOST-685 and reference relevant
  `doc/dev/` material and prior feature tasks where applicable.
- **Proportionality:** Depth should match exposure risk — prioritize paths that reach external
  agents, persisted storage, or support diagnostics.

## Constraints and Assumptions

- PyPost is a Python desktop application with optional local network MCP server; audit artifacts
  are markdown under `ai-tasks/`.
- Documented policies under `doc/dev/` (e.g. sensitive data masking, MCP secrets policy,
  environment encryption, hidden variables) are the baseline for alignment checks unless the
  report notes undocumented behavior.
- "Hidden" environment variables and encryption at rest are product features aimed at reducing
  accidental exposure; the audit evaluates whether protections hold across all surfaces.
- MCP clients are treated as less trusted than the operator UI unless the report documents an
  explicit exception.
- Step 1 captures business requirements only; audit methodology and technical analysis belong in
  later steps.
- Follow-up Jira issues are created in the project Debt or equivalent backlog per team practice
  (priority assigned when tickets are created in Step 6).

## Main Entities and Interactions (Business View)

| Entity | Description |
| --- | --- |
| Secret / credential | API keys, tokens, passwords, and other sensitive environment values. |
| Environment | Named set of variables; may include hidden keys and encrypted-at-rest values. |
| Hidden variable | Variable marked to mask display; execution may still use real values. |
| Operator | Human user of the PyPost GUI with full intended visibility. |
| External MCP agent | Local or network client invoking exposed collection tools. |
| HTTP request execution | Sending templated requests and receiving responses (GUI or MCP). |
| Request history | Persisted record of past request/response activity. |
| Operational log / metric | Diagnostic output for support, observability, or activity review. |
| MCP tool contract | Agent-visible tool name, description, and input schema from `list_tools`. |
| MCP tool result | Structured response returned to the agent after `call_tool`. |
| Collection | Group of saved requests; subset may be exposed as MCP tools. |
| Documented security policy | Dev docs describing intended masking, encryption, and visibility rules. |
| Audit finding | Documented gap, inconsistency, or risk with impact and priority. |
| Remediation follow-up | Jira issue tracking a specific security or secrets-handling fix. |

**Interaction overview (business):**

1. Operators define environments and collections; some variables are hidden or encrypted at
   rest.
2. Operators or MCP agents trigger request execution; real secret values are needed at
   execution time.
3. History, logs, and agent-visible MCP surfaces should receive only policy-allowed data;
   operators may see additional diagnostic detail.
4. Documented policies describe intended boundaries; the audit verifies reality against that
   baseline across storage, UI, execution, history, logs, and MCP.
5. Significant gaps become prioritized findings and Jira follow-ups for remediation.

## Acceptance Criteria (Audit Deliverables)

| ID | Criterion |
| --- | --- |
| AC-1 | Report exists under `ai-tasks/PYPOST-685/` with executive summary and detailed findings. |
| AC-2 | Storage and UI section addresses environment persistence, hidden keys, and encryption. |
| AC-3 | Execution and history section addresses credential flow and history/log sanitization. |
| AC-4 | MCP section addresses agent-visible vs operator-only data and policy alignment. |
| AC-5 | Transport section states assumptions for outbound HTTP and inbound MCP exposure. |
| AC-6 | Collection exposure section addresses which requests agents can invoke and related risks. |
| AC-7 | Documentation alignment section references `doc/dev/` security and secrets policies. |
| AC-8 | Recommendations are prioritized; each major finding has a clear impact statement. |
| AC-9 | Follow-up Jira issues exist for remediation items agreed during audit closeout. |

## Q&A

| Question | Answer |
| --- | --- |
| Why audit secrets handling now? | Multiple security features shipped independently; a consolidated audit verifies end-to-end consistency and surfaces residual exposure paths before wider MCP adoption. |
| How is this different from PYPOST-554? | PYPOST-554 implemented MCP secrets policy; this audit assesses the full secrets surface (storage, UI, history, logs, transport, collections) and whether policies are complete and consistently applied. |
| How is this different from PYPOST-684? | PYPOST-684 focused on package boundaries and architecture; this task focuses on security, credentials, and sensitive-data handling regardless of layer. |
| What is the primary deliverable? | A written audit report plus follow-up Jira issues — not code changes. |
| Who consumes the report? | Developers, reviewers, operators evaluating MCP risk, and tech-debt owners planning security remediation. |
| Does "ACL model for collections" imply role-based access control? | The audit assesses the product's effective exposure rules (e.g. which collections/requests are MCP-visible) and documents gaps; formal multi-user RBAC is out of scope unless already present. |

# Roadmap: PYPOST-1206

## Task Metadata

- **Implementation language**: English Markdown (developer docs); Python is
  the product language of related agent-UI MCP / desktop code only — this
  task is docs-only (no product code change)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1206/10-requirements.md` drafted
  - ATTACH-1 / PYPOST-991 attach path, trust, lifecycle, and spawn-session
    limitation wording scoped as docs-only outcomes
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1206/20-architecture.md` drafted
  - Doc-surface plan: primary `agent_ui_actions_mcp.md`; satellites
    `mcp_trust_model.md`, `agent_lifecycle.md`, `ui_actions.md`
  - Soft-contract lifecycle outcomes defined (success/fail/detach/host exit/
    sidecar exit); trust-surface separation preserved
  - Step 3 failing-repro designed as **N/A — no behavioral change**
    (docs-only; no product attach capability in this story)
- [x] **STEP 3: Failing Repro Test**
  - **N/A — no behavioral change.** Per
    `ai-tasks/PYPOST-1206/20-architecture.md` (§ Mandatory — Failing Repro /
    Q&A): docs-only ATTACH-1; no product runtime, UI, IPC, MCP catalog, or
    attach capability change. No red behavioral pytest is appropriate.
    Attach capability/tests remain PYPOST-1207 / PYPOST-1208. No red test
    written; no product or `doc/dev` edits in this step.
- [x] **STEP 4: Development**
  - [x] Iteration 1: Primary `doc/dev/agent_ui_actions_mcp.md` — spawn vs
    attach, operator procedure, trust summary, lifecycle outcomes table,
    revised Limitations + FR12 capability note (FR1–FR12 primary surface)
  - [x] Iteration 2: Satellites — `mcp_trust_model.md` (attach/local-host),
    `agent_lifecycle.md` (bind/unbind + exits), `ui_actions.md` (packaging
    pointer)
  - [x] Iteration 3: `make lint` — flake8 + Markdown lint OK + relative
    link check OK (NFR-5)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1206/40-code-cleanup.md` drafted
  - `make lint` PASS (flake8 + default Markdown / link checks)
  - Fixed: `mcp_trust_model.md` attach heading `###` → `##` (hierarchy)
  - Fixed: Step 4 multiline attach tables → single-line GFM rows
    (`agent_ui_actions_mcp.md`, `agent_lifecycle.md`, `mcp_trust_model.md`)
  - Docs-only; no product code cleanup
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1206/50-observability.md` drafted
  - **N/A — docs-only ATTACH-1**; no new product logging/metrics;
    process observability via Jira worklogs; runtime telemetry deferred
    to PYPOST-1207 / PYPOST-1208
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1206/60-tech-debt.md` drafted
  - Docs-only ATTACH-1: no blockers; no new unticketed debt
  - Deferred capability/tests linked to existing PYPOST-1207 / PYPOST-1208
    (no duplicate follow-ups)
- [x] **STEP 8: Dev Docs**
  - Verified FR1–FR12 + architecture surface plan against Step 4 `doc/dev`
  - Polish: `agent_ui_actions_mcp.md` Troubleshooting (spawn vs attach /
    soft contract / packaging)
  - Satellites unchanged (already complete from Step 4)
  - Artifact: `ai-tasks/PYPOST-1206/70-dev-docs.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1206/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1206/20-architecture.md`

### STEP 3: Failing Repro

- **N/A** — no red test (see Step 3 status note; architecture
  `20-architecture.md` Mandatory — Failing Repro)

### STEP 4: Development

- `doc/dev/agent_ui_actions_mcp.md` — primary ATTACH-1 contract
- `doc/dev/mcp_trust_model.md` — attach / agent-UI trust
- `doc/dev/agent_lifecycle.md` — attach bind/unbind + exits
- `doc/dev/ui_actions.md` — packaging pointer
- Docs-only (no product code / attach capability)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1206/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1206/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1206/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-1206/70-dev-docs.md`
- `doc/dev/agent_ui_actions_mcp.md` — Troubleshooting polish (Step 8)
- Confirmed (no further edit): `mcp_trust_model.md`, `agent_lifecycle.md`,
  `ui_actions.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit
  hash are reported in chat only, never written to this file.

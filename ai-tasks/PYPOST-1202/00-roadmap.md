# Roadmap: PYPOST-1202

## Task Metadata

- **Implementation language**: Markdown (planning artifacts) + Jira process;
  child implementation stories under PYPOST-991 use Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1202/10-requirements.md` drafted
  - Epic PYPOST-991 inventoried; three proposed child slices (ATTACH-1..3)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1202/20-architecture.md` drafted
  - Decomposition workflow: ATTACH-1→2→3 under PYPOST-991; create
    contract (Story, labels `agent`/`mcp`/`attach-sidecar`); per-child
    artifact ownership; Step 3 N/A for this task
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change
  - Reason: PYPOST-1202 is decomposition / Jira planning only (Markdown
    artifacts + child issue creation under PYPOST-991). Architecture
    (`20-architecture.md` § Mandatory — Failing Repro) states no product
    runtime change; no red automated test belongs on this ticket.
  - Red tests deferred to child Top-Down cycles (ATTACH-2 attach capability;
    ATTACH-3 verification / CI vs manual gaps; ATTACH-1 docs-verifiable or
    N/A in that child’s own Step 3).
  - No test file written; no production code changed.
- [x] **STEP 4: Development**
  - [x] Created child Stories under epic PYPOST-991 (labels
    `agent`/`mcp`/`attach-sidecar`; SP set on create)
  - [x] ATTACH-1 → [PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206)
    (SP 2) — Document attach path, trust boundary, and lifecycle
  - [x] ATTACH-2 → [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207)
    (SP 5) — Attach agent-UI MCP to already-running desktop PyPost
  - [x] ATTACH-3 → [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208)
    (SP 3) — Verify attach path with tests as feasible
  - [x] Verified `parent = PYPOST-991 AND statusCategory != Done` includes
    PYPOST-1202, PYPOST-1206, PYPOST-1207, PYPOST-1208
  - [x] Mapped provisional IDs → keys in `10-requirements.md`,
    `20-architecture.md`, and this roadmap
  - Estimation: self-estimate (Task nesting unavailable); preferred SP
    matched (2/5/3); no estimation worklog on children (no separate
    estimation `tokens_used`)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1202/40-code-cleanup.md` drafted
  - Markdown/DECOMPOSE only — no product lint/test; artifact style cleanup
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1202/50-observability.md` drafted
  - Runtime telemetry N/A — DECOMPOSE / Jira-only; no product code
  - Process observability: Top-Down worklogs + ATTACH-N → Jira keys
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1202/60-tech-debt.md` drafted
  - No blockers; follow-ups are existing children PYPOST-1206/1207/1208
  - Process residuals (self-estimate, optional Jira blocks links) NON-BLOCKER
- [x] **STEP 8: Dev Docs**
  - Pointer only in `doc/dev/agent_ui_actions_mcp.md` Limitations: attach
    follow-up ticketed as PYPOST-1206 / 1207 / 1208 under PYPOST-991
  - No attach path / trust / lifecycle prose (owned by ATTACH-1 /
    PYPOST-1206); no new `doc/dev/` file; no `doc/user/` changes
  - Decision note: `ai-tasks/PYPOST-1202/70-dev-docs.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1202/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1202/20-architecture.md`

### STEP 3: Failing Repro

- N/A — documented under Step Status (no red test; no behavioral change)

### STEP 4: Development

- Child Stories under PYPOST-991:
  - [PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206) (ATTACH-1, SP 2)
  - [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) (ATTACH-2, SP 5)
  - [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208) (ATTACH-3, SP 3)
- Mapping updates: `10-requirements.md`, `20-architecture.md`, this roadmap
- No product code changes

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1202/40-code-cleanup.md` (drafted; gate pending)
- Style/stale-narrative fixes in `10-requirements.md`, `20-architecture.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1202/50-observability.md` (drafted; gate pending)
- Runtime product logging/metrics: N/A (no `pypost/` change)
- Process trail: Jira worklogs (`tokens_used` / step metadata); child
  keys PYPOST-1206 / 1207 / 1208 under PYPOST-991

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1202/60-tech-debt.md` (drafted; gate pending)
- No blockers invented; epic work continues on PYPOST-1206 / 1207 / 1208

### STEP 8: Dev Docs

- `doc/dev/agent_ui_actions_mcp.md` — Limitations pointer to PYPOST-1206 /
  1207 / 1208 (epic PYPOST-991); attach contract docs deferred to ATTACH-1
- `ai-tasks/PYPOST-1202/70-dev-docs.md` — Step 8 decision / completion note
- No Overview/Architecture/Usage rewrite for attach (child owns that)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit
  hash are reported in chat only, never written to this file.

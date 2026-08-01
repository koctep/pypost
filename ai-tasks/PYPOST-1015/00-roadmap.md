# Roadmap: PYPOST-1015

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A — no behavioral change
  - Rationale: Architecture (`20-architecture.md`) and requirements
    (`10-requirements.md`) are docs-only — ship structured User Guide under
    `doc/user/`, wire `doc/README.md` + root README; no application packages,
    APIs, UI, Makefile targets, or runtime acceptance behavior to assert with
    a red pytest. Requirements explicitly decline a docs-contract check. No
    fake red test written; Step 4 ships the Markdown. Awaiting separate
    review subagent to mark STEP 3 `[x]`.
- [x] **STEP 4: Development**
    - [x] Accuracy pass on thin pages: `history-and-curl.md`, `hotkeys.md`,
      `scripts.md`, `templating.md` (aligned with current UI/API behavior)
    - [x] Correct MCP enable label and status text across guide pages; fix
      settings defaults (metrics host `127.0.0.1`); exact HTTP methods list
    - [x] Polish collections/environments/interface/requests for label
      consistency; keep Operator metrics in `workflows.md`
    - [x] Confirm navigation: `doc/user/README.md` TOC, `doc/README.md`, and
      root README Documentation links to User Guide
    - [x] Review FIX: drop non-UI Settings bullets (`max_response_bytes`,
      `log_level`); rename JSON Indent Size; note ~50 MB truncation in
      `requests.md` (not a Settings control)
- [x] **STEP 5: Code Cleanup**
  - [x] Markdown scan: ≤100 cols, no trailing WS, final newlines, ATX headers,
    hyphen lists under `doc/user/`
  - [x] Typographic ASCII normalizations (history-and-curl, requests, task
    artifacts)
  - [x] `40-code-cleanup.md` written; tests/`make check` N/A (docs-only; no
    docs lint target)
- [x] **STEP 6: Observability**
  - [x] N/A — docs-only User Guide; no runtime logging/metrics added
  - [x] `50-observability.md` documents N/A with justification; existing
    Prometheus/MCP surfaces stay linked from the guide (no fake metrics)
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` written; meaningful docs-maintenance debt listed
    (no screenshots, no docs lint/link CI, accuracy drift risk); five
    follow-ups without Jira links; SAFE TO CLOSE for this story's DoD
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/user_guide.md` — User Guide location, docs hub layout,
    maintenance conventions for `doc/user/`
  - [x] `doc/dev/README.md` — intro pointer + TOC link
  - [x] `70-dev-docs.md` close-out artifact

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

- **Primary**: English Markdown for end-user documentation
  (`.cursor/lsr/do-markdown.md`)
- **Application code**: none in scope (docs-only story)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1015/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1015/20-architecture.md`

### STEP 3: Failing Repro

- N/A — no behavioral change (docs-only User Guide; no red product test;
  execution justified; pending review PASS)

### STEP 4: Development

- User guide under `doc/user/`
- Docs index `doc/README.md`
- Root `README.md` Documentation links

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1015/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1015/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1015/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/user_guide.md`
- `doc/dev/README.md` (pointer + TOC)
- `ai-tasks/PYPOST-1015/70-dev-docs.md`

## Suggested branch name

`docs/PYPOST-1015-user-guide`

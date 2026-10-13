# PYPOST-1368: Technical Debt Analysis

DECOMPOSE / planning task — Markdown artifacts and Jira children under
[PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284) only. No product
runtime, tests, or make targets changed on this ticket.

**Verdict:** No blockers for closing PYPOST-1368. Implementation and verification
of the variable setup wizard and guidance subsystem remain on the already-created
children ([PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372),
[PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373),
[PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374),
[PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375)).

---

## Shortcuts Taken

- **Create-Time Self-Estimation:** Step 4 could not nest a separate estimation subagent; child tasks were self-estimated following the Fibonacci scale (≤ 5 SP per task) per `_shared/story-points.md` and repository standards (3 / 5 / 5 / 3 SP). No separate estimation `tokens_used` worklogs were posted to the child keys during create.
- **Informal Jira Dependency Links:** Dependency sequence (PYPOST-1372 → PYPOST-1373 → PYPOST-1374, with PYPOST-1375 depending on all three) is comprehensively recorded in planning artifacts (`10-requirements.md`, `20-architecture.md`, and `00-roadmap.md`). Explicit Jira issue links (`blocks` / `is blocked by`) were omitted at create time to prevent API overhead and workflow lockouts, keeping Jira `issuelinks` empty.
- **Provisional Sizing Total (16 SP vs Unestimated Epic):** The decomposition yielded 16 total story points across 4 cohesive, independently executable stories. This represents the necessary scope to deliver the full schema, UI, editor integration, and reference fixtures without creating oversized stories exceeding 5 SP.

---

## Code Quality Issues

- **None on this ticket:** PYPOST-1368 delivered solely Markdown documentation and Jira issue management operations. No `pypost/` Python application code, widgets, or test modules were introduced or refactored.
- **Child Story Ownership:** Full code quality gates (PEP 8 compliance, flake8, mypy typing, docstrings, and architectural separation between UI and data models) are owned by the child stories during their respective implementation cycles.

---

## Missing Tests

- **None for PYPOST-1368:** Step 3 was declared N/A (decomposition and planning task; zero behavioral runtime changes). No product or test files were modified or created.
- **Timeout Markers:** No tests were executed or added on this ticket. Pytest timeout-marker obligations belong to downstream implementation cycles (specifically PYPOST-1372, PYPOST-1373, PYPOST-1374, and PYPOST-1375).
- **Verdict:** **No timeout-marker blockers on this ticket.**

---

## Performance Concerns

- **None:** Zero runtime components shipped by PYPOST-1368.
- **Downstream Considerations for Child Tasks:**
  - Expanding large guidance cards in `VariableGuidanceCard` (PYPOST-1373) should avoid heavy re-layouts or unconstrained scroll areas.
  - Secret masking toggling should not trigger unnecessary redraws or re-evaluations of collection variables.

---

## Follow-up Tasks

### Blockers

None. Deliverables for PYPOST-1368 (requirements, architecture, child ticket creation, sprint assignment, code cleanup, and observability specifications) are complete.

### Non-Blockers (Already Ticketed — Epic Children)

All follow-up implementation work is captured in the four created child stories under parent epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284) and assigned to active Sprint 2029:

| Key | Priority | Story Points | Scope & Deliverable | Suggested Sequence |
| --- | :---: | :---: | --- | :---: |
| [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372) | Medium | 3 | Extend `CollectionVariable` model with `help_text` guidance attribute, serialization, validation, and backward compatibility. | 1 |
| [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373) | Medium | 5 | Implement `VariableSetupWizardDialog` modal and expandable `VariableGuidanceCard` UI components with secret masking and validation. | 2 |
| [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374) | Medium | 5 | Integrate variable setup wizard launch and overlay persistence into `_McpServerEditor` within `mcp_servers_dialog.py`. | 3 |
| [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375) | Medium | 3 | Add reference collection fixtures with OAuth guidance (`google_drive.json`), dev docs, and end-to-end contract test suite. | 4 |

Parent epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284) will be satisfied once all four child stories complete their respective Top-Down cycles and acceptance gates.

### Non-Blockers (Process Residuals — No New Ticket Required)

| Item | Classification | Residual Rationale & Handling |
| --- | --- | --- |
| **Child Story Sequencing** | Low / Process Residual | Implementation sequence (1372 → 1373 → 1374 → 1375) is strictly documented in architecture and roadmap. Formal Jira `blocks` links are omitted; sprint board execution order conveys dependency. |
| **Secret Masking & Sanitization** | Medium / Process Residual | Must ensure downstream child stories (PYPOST-1373, PYPOST-1374) strictly adhere to sensitive field masking rules outlined in `50-observability.md` (no secret values logged or leaked in UI state). |
| **Cross-Platform UI Testing** | Low / Process Residual | Expandable Qt card widgets and markdown guidance labels in `VariableGuidanceCard` must be validated across Linux, macOS, and Windows display scaling during PYPOST-1373 and PYPOST-1375. |
| **Estimation Worklogs on Child Keys** | Low / Process Residual | Create-time estimation was performed directly in Step 4; story points field was set on all child tickets (3/5/5/3). Separate estimation worklog entries on child tickets are omitted as standard for decomposition tasks. |

---

## Deviations from Architecture

None. All child stories were created in Jira under parent epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284), placed in Sprint 2029, and mapped cleanly to provisional designations WIZARD-1 through WIZARD-4 with Story Points ≤ 5 SP exactly as planned in `20-architecture.md`.

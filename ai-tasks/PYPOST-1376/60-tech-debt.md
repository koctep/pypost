# PYPOST-1376: Technical Debt Analysis

DECOMPOSE / planning task — Markdown artifacts and Jira children under parent epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) only. No product runtime, tests, or make targets changed on this ticket.

**Verdict:** Zero blockers for closing PYPOST-1376. Implementation and verification of the hidden response fields masking subsystem remain on the already-created children ([PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377), [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378), [PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379), [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380)).

---

## Shortcuts Taken

- **Create-Time Self-Estimation:** Step 4 could not nest a separate estimation subagent; child tasks were self-estimated following the Fibonacci scale (≤ 5 SP per task) per `_shared/story-points.md` and repository standards (3 / 3 / 5 / 3 SP, totaling 14 SP). No separate estimation subagent was spawned and no separate estimation `tokens_used` worklogs were posted to the child keys during ticket creation.
- **Informal Jira Dependency Links:** The dependency sequence (PYPOST-1377 → PYPOST-1378 and PYPOST-1379 in parallel → PYPOST-1380) is comprehensively recorded in planning artifacts (`10-requirements.md`, `20-architecture.md`, `ai-tasks/PYPOST-1312/decomposition-notes.md`, and `00-roadmap.md`). Explicit Jira issue links (`blocks` / `is blocked by`) were omitted at create time to prevent API overhead and workflow lockouts, keeping Jira `issuelinks` empty.
- **Provisional Sizing Total (14 SP vs Unestimated Epic):** The decomposition yielded 14 total story points across 4 cohesive, independently executable stories. This represents the necessary scope to deliver the full schema model and editor UI (3 SP), MCP permanent redaction (3 SP), GUI interactive click-to-reveal (5 SP), and integration test suite with developer docs (3 SP) without creating oversized stories exceeding 5 SP.

---

## Code Quality Issues

- **None on this ticket:** PYPOST-1376 delivered solely Markdown documentation and Jira issue management operations. No `pypost/` Python application runtime code, Qt GUI widgets, MCP server code, or test modules were introduced or refactored.
- **Child Story Ownership:** Full code quality gates (PEP 8 compliance via flake8, strict mypy type checking, Google-style docstrings, and strict architectural separation between data models, MCP sanitization, and GUI presentation) are owned by the child stories during their respective implementation cycles.

---

## Missing Tests

- **None for PYPOST-1376:** Step 3 was declared N/A (decomposition and planning task; zero behavioral runtime changes). No product runtime code or test files were modified or created.
- **Timeout Markers:** No tests were executed or added on this ticket. Pytest timeout-marker obligations belong to downstream implementation cycles (specifically PYPOST-1377, PYPOST-1378, PYPOST-1379, and PYPOST-1380).
- **Verdict:** **Zero timeout-marker blockers on this ticket.**

---

## Performance Concerns

- **Zero Runtime Impact:** No production code, runtime dependencies, or background tasks were added or modified in PYPOST-1376.
- **Downstream Considerations for Child Tasks (specifically MASK-3 / PYPOST-1379):**
  - **Large Documents:** For response bodies exceeding `LARGE_DOC_CHAR_THRESHOLD` (100 KB), heavy token tracking in `ResponseView` / `FoldableCodeView` could degrade GUI responsiveness. Downstream implementation must ensure a bypass/fallback path is active so large documents render without lag.
  - **QTextEdit Cursor Hit Tests:** In `ResponseView`, hit-testing mouse clicks against token spans must remain lightweight to avoid UI stutter during scrolling or clicking. Toggling a masked token alters character lengths on a single line, requiring efficient offset adjustments or re-scanning without triggering redundant full-document syntax re-highlighting passes.

---

## Follow-up Tasks

### Blockers

None. Zero blockers for closing PYPOST-1376. Deliverables for PYPOST-1376 (requirements, architecture, child ticket creation, sprint assignment, code cleanup, observability specifications, and technical debt analysis) are complete.

### Non-Blockers (Already Ticketed — Epic Children in Sprint 2032)

All follow-up implementation work is captured in the four created child stories under parent epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) and assigned to active Sprint 2032 ("Hide Selected Response Fields"):

| Key | Provisional Key | Summary | Story Points | Priority | Sprint | Dependencies | Description |
| --- | :---: | --- | :---: | :---: | :---: | --- | --- |
| [PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377) | `MASK-1` | `[PYPOST-1312] Request model, persistence, and RequestEditor UI for hidden response fields` | 3 | Medium | Sprint 2032 | None | Request model schema extension (`hidden_response_fields`), serialization, tab isolation/copy, and RequestEditor UI configuration table. |
| [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378) | `MASK-2` | `[PYPOST-1312] Permanent MCP output masking for hidden response fields` | 3 | Medium | Sprint 2032 | PYPOST-1377 | Irreversible permanent masking in `McpResponseSanitizer` and `format_structured_tool_result`, fail-closed redaction boundary. |
| [PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379) | `MASK-3` | `[PYPOST-1312] Interactive click-to-reveal response masking in GUI ResponseView` | 5 | Medium | Sprint 2032 | PYPOST-1377 | Presentation-layer click-to-reveal in `ResponseView`, token span tracking, coexistence with syntax highlighter, find/search, code folding, and large-doc fallback. |
| [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380) | `MASK-4` | `[PYPOST-1312] Integration test suite, edge-case coverage, and developer documentation` | 3 | Medium | Sprint 2032 | PYPOST-1377, 1378, 1379 | End-to-end integration contracts across GUI and MCP boundaries, edge cases (arrays, nested keys, non-JSON, empty body), and developer documentation in `doc/dev/`. |

Parent epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) will be satisfied once all four child stories complete their respective Top-Down cycles and acceptance gates.

### Non-Blockers (Process Residuals — No New Ticket Required)

| Item | Classification | Residual Rationale & Handling |
| --- | --- | --- |
| **Child Story Sequencing** | Low / Process Residual | Implementation sequence (1377 → 1378 & 1379 in parallel → 1380) is documented in architecture and roadmap. Formal Jira `blocks` links are omitted; sprint board execution order conveys dependency. |
| **Fail-Closed MCP Sanitization** | Medium / Process Residual | Downstream child story PYPOST-1378 must ensure strict fail-closed behavior on sanitization errors to eliminate any chance of sensitive field leakage to AI agents. |
| **Large Response Body Performance** | Low / Process Residual | Downstream child story PYPOST-1379 must verify that `LARGE_DOC_CHAR_THRESHOLD` fallback functions correctly without freezing the Qt main loop. |
| **Estimation Worklogs on Child Keys** | Low / Process Residual | Create-time estimation was performed directly in Step 4; story points field was set on all child tickets (3/3/5/3). Separate estimation worklog entries on child tickets are omitted as standard for decomposition tasks. |

---

## Deviations from Architecture

None. All child stories were created in Jira under parent epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312), assigned to Sprint 2032, and mapped cleanly to provisional designations MASK-1 through MASK-4 with Fibonacci Story Points (3, 3, 5, 3 ≤ 5 SP) exactly as planned in `20-architecture.md`.

# PYPOST-1174: Resolve epic placement for MCP Client tab stories

## Goals

People who plan, filter, and report on blank-tab protocol work must see one epic whose
**name and labels match the work it actually holds**. Today
[PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) is titled
"WebSocket tab mode — blank-tab protocol selector" and is labelled `websocket`, while it
already parents both WebSocket tab-mode stories and MCP Client tab-mode stories.

That mismatch hides MCP Client work from anyone who trusts the epic title or the
`websocket` label. It also leaves PYPOST-1164 artifacts saying the placement decision
was never made, even though the stories already live under PYPOST-1155 and sprint 1610
("MCP Client Tab Core UX") shipped several of them there.

The business goal of this debt item is to **close that planning gap**: pick a single
epic placement, apply it in Jira, and make the named planning documents agree with Jira.
No product behavior changes.

**Chosen option: (a)** — keep the existing parent, rename PYPOST-1155 to a
protocol-neutral title, and fix its labels so they are not WebSocket-only.

Option **(b)** (a sibling MCP epic and reparenting PYPOST-1165 … PYPOST-1172) is
rejected because those stories already sit under PYPOST-1155 and sprint 1610 delivered
them under that parent. Splitting now would rewrite the board history for work that is
already Done.

## User Stories

- As a **planner scanning the board**, I want PYPOST-1155's title to name blank-tab
  protocol modes in general, so that I do not miss MCP Client stories that already
  belong to that epic.
- As a **planner filtering by label**, I want the epic's labels to cover every protocol
  family it parents, so that a `websocket`-only filter does not imply MCP work is
  elsewhere.
- As a **developer reading PYPOST-1164 artifacts**, I want those files to state the
  placement decision instead of "either works", so that follow-up work does not reopen
  the same question.
- As a **developer reading `doc/dev/mcp_integration.md`**, I want that page to describe
  PYPOST-1155 as the shared protocol-mode epic, so that Jira and developer docs agree.
- As a **sprint participant**, I want PYPOST-1165 … PYPOST-1172 to stay under the same
  epic they shipped against in sprint 1610, so that Done work does not move to a new
  parent after delivery.
- As a **WebSocket story owner**, I want WS-TM stories to remain children of the same
  epic, so that HTTP / WebSocket / MCP Client blank-tab work stays one planning unit.

## Definition of Done

PYPOST-1174 is done when:

1. Epic [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) has a
   **protocol-neutral title** (the Jira ticket's example is "Tab protocol modes"; the
   exact wording may match that example or an equivalent that does not name only
   WebSocket).
2. Epic PYPOST-1155 **labels** no longer describe the epic as WebSocket-only while MCP
   Client children remain. Labels must be consistent with every protocol family the
   epic parents.
3. MCP Client tab stories **PYPOST-1165 … PYPOST-1172 stay parented** to PYPOST-1155.
   No sibling MCP epic is created for this placement. Other existing children of
   PYPOST-1155 (WebSocket stories, research, later MCP-TM work, related debt) stay
   under PYPOST-1155 unless a later ticket says otherwise.
4. These artifacts **agree with that decision** (they no longer treat rename vs
   sibling epic as open):
   - `ai-tasks/PYPOST-1164/00-roadmap.md`
   - `ai-tasks/PYPOST-1164/10-requirements.md`
   - `ai-tasks/PYPOST-1164/60-tech-debt.md`
   - `doc/dev/mcp_integration.md`
5. **No production application code** changes. This ticket is Jira process plus
   documentation alignment only.
6. PYPOST-1174's own `10-requirements.md` and `00-roadmap.md` exist; Step 1 remains
   `[/]` until the acceptance gate passes.

## Task Description

### Programming Language

Markdown — documentation and Jira process artifacts. No Python product code.

### Problem

Epic PYPOST-1155 was opened for blank-tab **WebSocket** mode. Its title and labels still
say that. After PYPOST-1164, the same epic also parents MCP Client tab-mode stories
(PYPOST-1165 … PYPOST-1172). PYPOST-1164 explicitly deferred whether to rename the epic
or split a sibling. The stories were created under PYPOST-1155 anyway.

Jira at the time of this requirements pass:

| Group | Keys (under PYPOST-1155) | Notes |
| ----- | ------------------------ | ----- |
| WebSocket tab mode | PYPOST-1156 … PYPOST-1163 | Research plus WS-TM-1 … WS-TM-7 |
| MCP research | PYPOST-1164 | Decomposed MCP Client tab mode |
| MCP Client tab mode | PYPOST-1165 … PYPOST-1172 | MCP-TM-1 … MCP-TM-8 |
| Later MCP-TM | PYPOST-1175 | MCP-TM-9 shortcuts |
| Related debt | PYPOST-1180, PYPOST-1183 … PYPOST-1188 | Follow-ups from child stories |

The original ticket counted 15 implementation stories (WS-TM plus MCP-TM) and ~58 story
points, with the epic title describing only the WebSocket slice. MCP stories carry `mcp`
labels inside a `websocket`-labelled epic.

Sprint 1610 ("MCP Client Tab Core UX") already completed several MCP-TM stories
(including PYPOST-1165, PYPOST-1166, PYPOST-1167, PYPOST-1169, PYPOST-1170) while they
were children of PYPOST-1155.

### Business Need

Boards, filters, and reports must not lie. An epic named and labelled only for
WebSocket causes planners to under-count MCP Client work or to look for a second epic
that does not exist. Leaving "rename or split" open in PYPOST-1164 artifacts repeats
the same debate on every follow-up.

Option (a) restores honesty **without** moving shipped stories. Option (b) would create
a new epic and reparent work that sprint 1610 already treated as part of PYPOST-1155.

### Scope (this task)

- Record and apply **option (a)** in Jira for PYPOST-1155 (title and labels).
- Keep PYPOST-1165 … PYPOST-1172 under PYPOST-1155.
- Align the four named documents so they state the decision, not an open choice.

### Out of Scope

- Changing PyPost application behavior, UI, or tests.
- Creating a sibling MCP epic or reparenting PYPOST-1165 … PYPOST-1172.
- Rewriting WebSocket or MCP product requirements (those stay on their own tickets).
- Closing remaining open MCP-TM or WS-TM stories (PYPOST-1168, PYPOST-1171,
  PYPOST-1172, PYPOST-1175, open WS-TM items, and related debt).
- Changing sprint membership of any issue.

### Constraints and Assumptions

- PYPOST-1174 is **Debt**, Medium priority, labels `mcp` and `ux`, 3 story points,
  currently In Progress on sprint 1610.
- PYPOST-1174 itself is **not** a child of PYPOST-1155 (filed outside that epic because
  it is a planning fix, not blocked by MCP Client tab delivery).
- Exact epic title text is a wording choice as long as it is protocol-neutral; the
  ticket example "Tab protocol modes" is acceptable.
- "Fix labels" means the epic must not read as WebSocket-only; it does not require
  copying every child label onto the epic.
- Historical PYPOST-1164 text that deferred the decision will be updated to point at
  this ticket's outcome, not deleted as if the deferral never happened.

### Main Entities (planning domain)

- **Epic (PYPOST-1155)** — planning parent for blank-tab protocol-mode work. Attributes:
  title, labels, child issues.
- **Child story** — a WebSocket or MCP Client tab-mode (or related) issue parented to
  that epic. Attributes: key, summary, status, labels, parent.
- **Label** — board filter token (`websocket`, `mcp`, `ux`, `documentation`, and
  others). Must not imply a narrower epic scope than the children.
- **Sprint 1610** — active sprint that already delivered MCP Client stories under
  PYPOST-1155.
- **Planning artifact** — markdown under `ai-tasks/PYPOST-1164/` and
  `doc/dev/mcp_integration.md` that must match Jira after the decision.

### Interactions

1. Planner reads epic title and labels → must infer both WebSocket and MCP Client
   blank-tab work.
2. MCP Client stories remain children of PYPOST-1155 → sprint history stays coherent.
3. PYPOST-1164 artifacts and `doc/dev/mcp_integration.md` cite PYPOST-1155 as the
   decided parent, with the rename/label fix recorded as PYPOST-1174.

## Q&A

- **Q:** Why not option (b), a sibling MCP epic?
  **A:** MCP stories already sit under PYPOST-1155. Sprint 1610 shipped them there.
  Reparenting Done work would split a history that already treats one epic as the
  protocol-mode bucket. PYPOST-1164 said either option could work; delivery since then
  makes (a) the cheaper honest fix.

- **Q:** Why is this a business/planning need rather than a Jira cleanup whim?
  **A:** Title and labels are how people find work. A WebSocket-named epic that silently
  holds 35 SP of MCP Client stories misleads filters, reports, and new contributors.

- **Q:** Does this change the product?
  **A:** No. Users of PyPost see no change. Only Jira and the named docs change.

- **Q:** What language is used for artifacts?
  **A:** Markdown. No Python product code.

- **Q:** Sources
  - [PYPOST-1174](https://pypost.atlassian.net/browse/PYPOST-1174)
  - [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)
  - [PYPOST-1164](https://pypost.atlassian.net/browse/PYPOST-1164) (deferred placement)
  - Sprint 1610: MCP Client Tab Core UX

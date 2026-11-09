# PYPOST-1390: Responsive masked-token hit-testing under high span counts

## Goals

PyPost’s desktop response viewer masks sensitive JSON fields by default and supports in-place click-to-reveal. While the pointer moves over the response body, the product continuously answers a simple interaction question: *is the caret under a masked (or revealed) token, and if so which one?* That answer drives hover cursor feedback, tooltips, and click-to-reveal targeting.

Today this lookup stays correct for typical payloads (a handful of masked fields). It becomes a responsiveness risk when many fields are masked at once (hundreds of tokens in rich enterprise responses): every pointer move repeats the same search, and cost that grows with the number of masked tokens competes with smooth GUI interaction during demos, screen shares, and dense-payload inspection.

This ticket exists as deferred non-blocker debt from [PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379) (MASK-3 interactive GUI masking). The **business goals** are:

- Keep viewport hover feedback and click targeting **fluid** when masked token counts are high.
- Preserve **exact** current hit-test and toggle semantics — which token is under a position, inclusive coverage, and post-toggle behavior must not change for users.
- Improve only the interaction lookup path; masking rules, visuals, MCP redaction, and selector evaluation remain out of scope.

The Jira summary names a concrete search technique; that is a suggested approach from debt notes. The requirement here is the **outcome** (responsive, correct position→token resolution), not a mandated algorithm.

## Programming Language

Python (desktop GUI response masking presentation in PyPost).

## User Stories

- As an **API developer inspecting dense JSON**, I want hover cursor and tooltip feedback to stay smooth even when dozens or hundreds of fields are masked, so dense payloads do not feel sluggish under the pointer.
- As a **presenter screen-sharing a response**, I want click-to-reveal targeting to remain accurate and snappy under many masked tokens, so demos stay professional without laggy hover or mis-hits.
- As an **end user toggling masked fields**, I want reveal / re-mask clicks to continue resolving the same token at the same character positions as today after each toggle shifts later tokens.
- As a **product maintainer**, I want this debt closed without changing masking visuals, selector matching, MCP sanitization, or large-document bypass policy.
- As a **quality engineer**, I want automated proof that high span-count lookups stay correct and that interaction behavior matches the pre-change baseline.

## Definition of Done

This task is considered done when:

1. **Responsive hit resolution**: Resolving which masked token (if any) contains a document character position no longer scales poorly with masked token count under continuous hover-style querying.
2. **Semantic freeze**: For the same span set and character position, the resolved token (or “none”) matches current behavior, including inclusive start/end coverage and no-match outside all spans.
3. **Interaction continuity**: Hover cursor / tooltip affordances and click-to-reveal / re-mask continue to target the same spans; toggling still keeps later spans’ positions consistent for subsequent lookups.
4. **Ordering invariant**: Spans remain usable for ordered document lookup after load and after toggles that shift later intervals (document order by start position is preserved as the hit-test input assumption).
5. **Automated verification**: Tests cover correctness for sparse and high span-count cases, including miss / hit / boundary positions and post-toggle lookup; required timeout markers apply; `make check` passes.
6. **No scope creep**: Selector engine, MCP redaction, ExtraSelection styling, large-document thresholds, and unrelated span-shifting data-structure redesigns are unchanged by this ticket.

## Task Description

### Problem Statement

Interactive masking tracks each sensitive token as a character interval in the formatted response text. Pointer motion over the response viewport asks, at high frequency, which interval contains the character under the cursor. When few tokens are masked, a full scan of the interval list is imperceptible. When many tokens are masked, repeating that full scan on every move can degrade hover responsiveness even though each individual comparison is cheap.

Users still need:

- Correct “under a masked token?” answers for cursor and tooltip feedback.
- Correct click targeting for reveal / re-mask.
- Unchanged visual and security behavior outside this lookup.

The product therefore needs position→token resolution that stays responsive as masked token counts grow, without changing what those answers are.

### Scope

#### In Scope

- Improving **masked-token hit resolution** used by viewport hover and click handling so cost stays acceptable under high span counts.
- Preserving **identical observable hit and toggle outcomes** versus today’s behavior for the same spans and positions.
- Ensuring span sets loaded for display and updated after toggles remain valid inputs for that improved lookup.
- Automated tests for correctness (including high span counts and boundaries) and for the responsiveness intent of this debt item.

#### Out of Scope

- Changing click-to-reveal UX, underline / background styling, or tooltip copy.
- MCP irreversible redaction or selector evaluation performance ([PYPOST-1388](https://pypost.atlassian.net/browse/PYPOST-1388) and related).
- Medium-document background formatting ([PYPOST-1396](https://pypost.atlassian.net/browse/PYPOST-1396)).
- Replacing linear adjustment of later span offsets after a toggle with a different offset-tracking structure (separate debt from PYPOST-1379).
- Large-document bypass thresholds, folding, search highlighting, or non-JSON response paths.
- Mouse-move throttling / debouncing as a substitute for better hit resolution (not required by this ticket).

### Functional Requirements

- **FR-1 — Position to token**: Given the current masked-token intervals and a character position, the system returns the token whose interval contains that position, or indicates no token.
- **FR-2 — Inclusive coverage**: A position on either endpoint of a token’s interval counts as a hit on that token (same as today).
- **FR-3 — Hover path**: Continuous pointer motion over the response body uses FR-1 so cursor and tooltip feedback remain correct.
- **FR-4 — Click path**: Click-to-reveal / re-mask uses the same FR-1 resolution so the toggled token matches hover targeting.
- **FR-5 — Post-toggle consistency**: After a reveal or re-mask changes text length, later intervals stay correctly shifted and subsequent FR-1 answers remain correct for the updated document.
- **FR-6 — Empty / miss short-circuit**: Empty span sets and positions outside all intervals resolve as no token without incorrect hits.

### Non-Functional Requirements

- **NFR-1 — High-frequency responsiveness**: Under representative high span counts (on the order of hundreds of masked tokens), repeated hit resolution during hover-style querying must improve relative to the current full-list scan baseline so pointer feedback stays fluid.
- **NFR-2 — Correctness over cleverness**: No performance gain is acceptable if hit identity, boundaries, or post-toggle targeting diverge from current behavior.
- **NFR-3 — GUI-thread suitability**: Hit resolution remains appropriate for frequent main-thread pointer events (no blocking remote I/O or heavy allocation on the hot path).
- **NFR-4 — Testability**: Parity and high-count intent are covered by automated tests with required timeout markers; `make check` stays green.

### Constraints and Assumptions

- Masked token intervals for a displayed response are non-overlapping and ordered by ascending start position in the document (established by the existing formatter / controller contract).
- Typical interactive masking still applies within existing GUI size thresholds; this ticket targets span *count*, not document-size policy.
- Raw stored response data remains immutable; only presentation text and tracked intervals change on toggle.
- This item is performance debt from PYPOST-1379; user-visible masking semantics are intentionally frozen.

## Main Entities and Interactions

| Entity | Role | Notes |
| --- | --- | --- |
| **Masked token span** | Presentation interval | Character range for one masked/revealable value, plus reveal state and display strings. |
| **Response mask controller** | Interaction coordinator | Owns spans, hover feedback, and click-to-reveal for the response body view. |
| **Hit resolution** | Lookup capability | Answers which span contains a character position (or none). |
| **Response body view** | User surface | Emits pointer positions; shows cursor, tooltips, and toggled text. |
| **Hover feedback** | UX affordance | Cursor shape and tooltip driven by hit resolution during motion. |
| **Click-to-reveal action** | UX affordance | Uses the same hit resolution to toggle masked ↔ revealed text. |

```
Pointer position (character)
        |
        v
+-------------------+
|  Hit resolution   |  -->  Masked token span | none
+-------------------+
        |
        +--> Hover feedback (cursor / tooltip)
        +--> Click-to-reveal / re-mask
```

## Acceptance Criteria

- **AC-1:** Repeated position→token resolution under a large span set is no longer dominated by scanning every span on each query as the steady-state behavior.
- **AC-2:** For fixed span fixtures, hit results match baseline behavior for hits, misses, and inclusive endpoints.
- **AC-3:** After toggling a span, later positions still resolve to the correct tokens.
- **AC-4:** Hover and click paths continue to share the same resolution rules (no divergent targeting).
- **AC-5:** Automated tests cover high span-count correctness (and demonstrate the responsiveness intent versus the prior linear scan baseline).
- **AC-6:** `make check` passes.

## Q&A

**Q1: The Jira text says to replace the linear scan with bisect over sorted intervals. Is that the requirement?**  
**A**: That phrase is the suggested technical approach from PYPOST-1379 debt notes. The **requirement** is responsive, semantically identical position→token resolution under high span counts. Concrete search structures belong in architecture (Step 2), not as frozen requirements here.

**Q2: Why does this matter to users?**  
**A**: Hover and click targeting run continuously while inspecting masked responses. With few masked fields the cost is invisible; with hundreds of masked fields, poorly scaling lookup makes the UI feel laggy during demos and dense-payload review even though masking itself is correct.

**Q3: What must never change?**  
**A**: Which span is hit for a given position; inclusive endpoints; post-toggle targeting; visual styling; selector/MCP behavior; large-document bypass policy.

**Q4: Is mouse-event throttling in scope?**  
**A**: No. This ticket improves hit resolution itself. Throttling remains optional future debt if profiling still shows event-loop pressure after lookup improves.

**Q5: Implementation language?**  
**A**: Python, within the existing desktop GUI response masking presentation (`ResponseMaskController` and its tests).

**Q6: Related work that is explicitly not this ticket?**  
**A**: Selector evaluation efficiency (PYPOST-1388), medium-document worker formatting (PYPOST-1396), incremental formatter offset counters (PYPOST-1391), reveal-state persistence across reformat (PYPOST-1392), and offset-tree redesign for toggle shifting remain separate.

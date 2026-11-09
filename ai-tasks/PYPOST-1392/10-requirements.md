# PYPOST-1392: State preservation across reformatting and tab switching

## Goals

PyPost’s desktop response viewer masks sensitive JSON fields by default and lets users
click individual masked tokens to reveal (or re-mask) them in place. That reveal choice is
intentional: during demos, pairing, or debugging, a user may uncover one field while leaving
others concealed.

Today, those choices are discarded whenever the response body is re-rendered for
presentation reasons that do **not** change the underlying response payload—most notably
changing JSON indentation size, and other tab/view transitions that re-apply formatting.
After such a re-render, every previously revealed field snaps back to the default masked
`***` state. Users must click again to restore the inspection context they already chose.

This ticket is deferred non-blocker debt from
[PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379) (MASK-3 interactive GUI
masking). The **business goals** are:

- Preserve user-selected reveal / re-mask decisions across presentation re-renders of the
  **same** response content.
- Avoid surprising resets when the user changes indent size or switches among tabs that
  trigger formatting refresh.
- Keep default-masked security posture for **new** responses and explicit clears.
- Do not change masking rules, MCP redaction, selector matching, or click-to-reveal UX
  beyond persistence of the user’s prior choices.

## Programming Language

Python (desktop GUI response masking presentation in PyPost).

## User Stories

- As an **API developer inspecting a masked JSON response**, I want fields I already
  revealed to stay revealed after I change JSON indent size, so I do not lose my
  inspection context when adjusting formatting.
- As an **API developer working across request tabs**, I want each tab’s reveal choices to
  survive presentation refreshes triggered by settings or tab lifecycle that reformat the
  same response, so switching context does not force me to re-click every token.
- As a **presenter screen-sharing a response**, I want revealed demo fields to remain
  revealed after incidental reformat, so the audience does not see secrets flash back to
  `***` and then get re-revealed awkwardly.
- As a **security-conscious user**, I want a brand-new response (or an explicit clear of
  the response body) to start fully masked again, so persistence never carries reveal
  choices onto unrelated payloads.
- As a **product maintainer**, I want automated proof that indent reformat and equivalent
  same-response re-renders restore prior reveal states by field identity, without changing
  MCP redaction or default-masked first paint.

## Definition of Done

This task is considered done when:

1. **Indent reformat persistence**: After the user reveals one or more masked fields and
   then changes JSON indentation size for that response view, those fields remain revealed
   (and still-masked fields remain masked) in the newly formatted document.
2. **Same-response re-render persistence**: Re-applying presentation formatting for the
   same underlying response and hidden-field configuration restores prior reveal / mask
   choices for matching fields.
3. **Tab / view refresh continuity**: Presentation refreshes associated with tab or
   settings-driven reformat of an already-displayed response do not reset all tokens to
   default masked solely because of the refresh.
4. **Fresh response reset**: Displaying a different response, or clearing the response
   body, returns interactive masking to the default fully masked state (no stale reveals
   from a prior payload).
5. **Unchanged first paint**: The first display of a response still shows configured
   hidden fields as masked until the user reveals them.
6. **Automated verification**: Tests cover indent-change persistence and fresh-response
   reset; required timeout markers apply; suite gate passes relative to baseline.
7. **No scope creep**: Selector engine behavior, MCP irreversible redaction, ExtraSelection
   styling copy, large-document bypass, and hit-testing algorithms remain out of scope.

## Task Description

### Problem Statement

Interactive masking tracks each sensitive token and whether the user has revealed it.
Presentation-only operations (indent size change, and other same-response re-renders that
occur when tabs or settings refresh formatting) rebuild the formatted document and recreate
token spans from scratch. Those new spans always start masked, discarding the user’s prior
reveal choices even though the response body and hidden-field rules did not change.

Users still need:

- Default masking on first display and on new responses.
- Persistence of reveal choices when only presentation formatting changes.
- Correct click-to-reveal behavior after those re-renders (positions may shift; identity of
  the field must not).

### Scope

#### In Scope

- Preserving per-field reveal / mask choices across indentation reformatting of the current
  response.
- Preserving those choices across same-response presentation re-renders that tabs or
  settings may trigger.
- Resetting reveal choices when the response body is cleared or a different response is
  shown.
- Automated tests for persistence and reset behaviors.

#### Out of Scope

- Persisting reveal choices across application restarts or collection save/load.
- Changing MCP tool redaction (always irreversible; no reveal).
- Changing which fields are selected for masking.
- Hit-testing performance (PYPOST-1390), formatter offset counters (PYPOST-1391), or
  medium-document background formatting (PYPOST-1396) beyond any minimal hook needed for
  persistence.
- Folding state, search query text, or scroll position persistence (unless incidentally
  unaffected).

### Functional Requirements

- **FR-1 — First display masked**: On first display of a response with hidden fields, all
  matching tokens appear masked.
- **FR-2 — Indent persistence**: After user reveal/re-mask toggles, changing indent size
  and reformatting the same response restores each field’s last reveal state.
- **FR-3 — Same-response re-render**: Re-displaying the same response content with the same
  hidden-field configuration restores prior reveal states for matching fields.
- **FR-4 — New response reset**: Showing a new response starts with all tokens masked,
  ignoring prior reveal choices from a previous response.
- **FR-5 — Clear reset**: Clearing the response body discards stored reveal choices for
  that view.
- **FR-6 — Partial reveal**: Only fields the user revealed stay revealed after reformat;
  other hidden fields stay masked.
- **FR-7 — Re-mask persistence**: If the user revealed then re-masked a field before
  reformat, that field remains masked after reformat.

### Non-Functional Requirements

- **NFR-1 — Security default**: Persistence must never auto-reveal fields the user has not
  explicitly revealed for the current response.
- **NFR-2 — Field identity**: Persistence keys off stable field identity within the
  response (not fragile character offsets that change with indent).
- **NFR-3 — Performance**: Persistence bookkeeping must not noticeably slow typical
  response display for small payloads.
- **NFR-4 — Isolation**: Reveal state for one request tab must not leak into another tab’s
  response view.

### Constraints and Assumptions

- Deferred debt from PYPOST-1379; interactive masking already exists.
- Each request tab owns its own response view instance.
- Indent changes re-apply formatting from the last displayed response and hidden-field
  list.
- Large-document bypass paths that skip interactive spans remain without click-to-reveal
  persistence (no spans to restore).

## Main Entities (Business)

- **Response view**: Presents one tab’s HTTP response body with optional masking.
- **Masked field**: A configured hidden response field shown as a placeholder until
  revealed.
- **Reveal choice**: The user’s current preference for a masked field (revealed or
  masked) for the active response.
- **Presentation reformat**: Rebuild of the visible JSON text (e.g. indent change) without
  changing the underlying response payload.
- **Request tab**: Owns an independent response view and therefore independent reveal
  choices.

## Q&A

**Q**: Why is this framed as business debt rather than a pure UI polish bug?

**A**: Lost reveal state interrupts demos and debugging workflows whenever formatting
refreshes; the debt note from PYPOST-1379 called out retention of user reveal choices
across re-renderings as follow-up work.

**Q**: Should reveal choices survive a new request on the same tab?

**A**: No. A new response (or clear) must default to fully masked. Persistence applies only
to presentation re-renders of the same response content.

**Q**: Does “tab switching” require cross-tab shared state?

**A**: No. Each tab keeps its own choices. The requirement is that tab/settings-driven
reformat of a tab’s already-displayed response must not wipe that tab’s choices.

**Q**: Related tickets?

**A**: Parent MASK-3 work is PYPOST-1379. Sibling debt: PYPOST-1390 (hit-testing),
PYPOST-1391 (formatter offsets), PYPOST-1396 (medium-doc worker). Persistence is this
ticket only.

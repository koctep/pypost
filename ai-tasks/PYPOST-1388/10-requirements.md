# PYPOST-1388: Efficient selector evaluation for high-frequency response masking

## Goals

PyPost masks sensitive response fields for two high-frequency consumers:

1. **Interactive GUI presentation** — reversible masking in the response viewer while users inspect API payloads.
2. **MCP egress redaction** — irreversible replacement of configured sensitive values before tool output leaves the product.

Both consumers rely on the shared selector path evaluation capability introduced by the unified engine work. That capability already supports bare keys, dotted paths, and array wildcards, and it partitions simple keys for fast lookup. What remains costly under realistic enterprise load is repeated evaluation of **hierarchical path selectors** while walking large JSON trees:

- Path rules are still considered one-by-one for each visited key when hierarchical selectors are present.
- During traversal, the current location in the document is repeatedly rebuilt as new path representations for each descent.
- Enterprise configurations (large selector catalogs from virtualized Hidden Fields workflows) and medium/large JSON bodies amplify this cost across many requests, worker-thread formatting passes, and MCP tool calls.

The **business goal** of this task is to keep masking **semantically identical** while making high-frequency evaluation cheaper and lighter on allocations, so:

- Desktop response inspection stays responsive under large selector sets and nested payloads.
- MCP redaction does not add avoidable latency or allocation churn on every tool result.
- Security parity between GUI masking and MCP redaction remains absolute — faster evaluation must never change which fields are masked.

This ticket exists because earlier masking delivery intentionally deferred that optimization (tracked as follow-up debt from MCP hidden-fields work), not because selector syntax or user-facing masking behavior needs to change.

## Programming Language

Python (PyPost core selector evaluation and its existing GUI / MCP consumers).

## User Stories

- As an **API developer**, I want masked responses to appear quickly even when a request has many hierarchical hidden-field selectors and a sizable JSON body, so inspection does not feel sluggish.
- As an **enterprise security engineer**, I want large catalogs of path-based masking rules to remain practical at runtime, not only editable in the Hidden Fields UI.
- As an **MCP / AI-agent user**, I want tool responses that apply the same hidden-field rules without paying avoidable per-call evaluation overhead that slows agent workflows.
- As a **product maintainer**, I want any efficiency improvement to preserve exact existing match semantics (bare key, dotted path, array wildcard, shorthand fallback, header selectors ignored for body evaluation) so GUI and MCP stay in lockstep.
- As a **quality engineer**, I want regression protection proving that optimized evaluation masks the same fields as today across nested objects, arrays, and mixed selector sets.

## Definition of Done

This task is considered done when:

1. Hierarchical path selector evaluation for response masking is materially more efficient under high-frequency use (large selector catalogs and/or deep/wide JSON) without changing observable match outcomes.
2. Document path tracking during masking traversal no longer incurs avoidable per-level path reconstruction cost as the dominant allocation pattern.
3. Existing public behaviors remain unchanged:
   - Bare keys still match at any depth.
   - Dotted paths and array wildcards (`[*]` / `.*`) still match the same nodes.
   - Shorthand compatibility for path variants continues to behave as today.
   - `header:` selectors remain excluded from JSON body evaluation.
   - Raw response data remains unmutated; redaction still returns replaced trees / formatted text with placeholders.
4. GUI mask formatting and MCP redaction continue to agree on which fields are masked for the same selector set and payload.
5. Automated tests cover semantic parity (same mask decisions as baseline) and demonstrate the intended efficiency improvement for representative high-load cases.
6. Repository quality gate `make check` passes.

## Task Description

### Problem Statement

Response masking is invoked often: every interactive display path that applies hidden fields, background formatting for medium documents, and every MCP tool result that sanitizes JSON. The unified engine already compiles selectors once per construction and gives simple keys an efficient membership check. Hierarchical path rules, however, still scale poorly when many path selectors are configured and every dictionary key in a large tree must be tested. At the same time, recursive descent repeatedly materializes new representations of the current path (“breadcrumb”) instead of reusing a single traversal location. Individually small costs compound into measurable CPU and allocation pressure exactly where the product must stay responsive and trustworthy.

### Scope

#### In Scope

- Improving **path-selector lookup efficiency** after a selector set is accepted for masking, so repeated match decisions during one or many traversals are cheaper when many hierarchical rules exist.
- Improving **path-location tracking** during JSON traversal used for masking/redaction so descent and ascent do not repeatedly allocate disposable path structures.
- Preserving **full behavioral compatibility** of selector matching and redaction results for current supported syntax.
- Keeping both primary consumers (GUI presentation masking and MCP JSON redaction) on the improved evaluation path with identical outcomes.
- Adding or extending automated verification for match parity and for the efficiency intent of this debt item.

#### Out of Scope

- New selector syntax (JSONPath filters, slices, recursive descent `..`, negative indices, etc.).
- Changes to Hidden Fields editing UX, virtualization, or inline syntax validation (separate tickets).
- Changes to click-to-reveal interaction model, span hit-testing, or large-document GUI fallback thresholds.
- Streaming / SAX-style JSON sanitizers for multi-megabyte payloads (separate follow-up).
- Header-masking policy changes beyond continuing to ignore `header:` rules in body evaluation.
- Altering placeholder text or making redaction mutate stored raw responses.

### Functional Requirements

- **FR-1 — One-time preparation of a selector set**: Given a configured list of hidden-field expressions, the system prepares that set once into a form suitable for many subsequent match decisions during masking traversals.
- **FR-2 — Efficient hierarchical match decisions**: When hierarchical path selectors are present, deciding whether a field at a document location matches must not require scanning cost that grows poorly with the number of path rules on every visited key.
- **FR-3 — Efficient path location during traversal**: While walking objects and arrays for masking or redaction, the system must track the current document location without repeatedly allocating a fresh full path representation at every descent.
- **FR-4 — Semantic freeze**: For the same selectors and JSON input, masked/redacted outputs and match decisions must remain identical to current behavior (including bare keys, dotted paths, array wildcards, shorthand fallback, empty/invalid selector handling, and ignoring body-irrelevant header selectors).
- **FR-5 — Consumer continuity**: GUI formatting that queries match decisions and MCP redaction that replaces matched values must both benefit from the improved evaluation without divergent rules.
- **FR-6 — Empty / trivial short-circuit**: When no body selectors remain after preparation, consumers can still skip work immediately.

### Non-Functional Requirements

- **NFR-1 — High-frequency performance**: Evaluation cost for representative medium JSON bodies with larger hierarchical selector catalogs must improve relative to the pre-change baseline (less CPU and fewer disposable path allocations during traversal).
- **NFR-2 — Correctness over cleverness**: No performance gain is acceptable if it changes which fields are masked or breaks GUI/MCP parity.
- **NFR-3 — Core-layer suitability**: Selector evaluation remains usable from headless MCP paths and GUI formatters without introducing UI dependencies into the core evaluation capability.
- **NFR-4 — Testability**: Parity and efficiency intent are covered by automated tests with required timeout markers; `make check` stays green.

### Constraints and Assumptions

- Typical interactive masking still applies to payloads within existing GUI size thresholds; efficiency work must still help those paths and MCP redaction of comparable trees.
- Selector catalogs can grow into the hundreds or thousands of entries at the configuration layer; hierarchical path rules are the expensive subset this ticket targets.
- Immutable raw payloads remain a hard constraint for both consumers.
- This item is performance/maintainability debt from earlier masking delivery; user-visible masking semantics are intentionally frozen.

## Main Entities and Interactions

| Entity | Role | Notes |
| --- | --- | --- |
| **Hidden field selector** | User-configured rule | Bare key, dotted path, array wildcard, or header selector expression. |
| **Selector evaluation capability** | Core domain service | Prepares selector sets and answers whether a field at a document location should be masked. |
| **Document location (path)** | Traversal state | The breadcrumb of ancestor keys/array positions from the JSON root to the current field. |
| **GUI mask presentation** | Consumer | Pretty-prints JSON, substitutes placeholders, records revealable spans using match decisions. |
| **MCP redaction** | Consumer | Produces a redacted JSON structure/string for tool egress using the same match decisions. |
| **Masked placeholder** | Presentation / security value | The `***` (or configured) stand-in for sensitive leaf values. |

## Acceptance Criteria

- **AC-1:** Hierarchical selector evaluation is prepared for repeated match use rather than relying on poorly scaling per-key consideration of the full path-rule list as the steady-state behavior.
- **AC-2:** Traversal path tracking for masking/redaction avoids per-level full path reconstruction as the steady-state allocation pattern.
- **AC-3:** Golden/parity tests show identical mask decisions and redaction results versus current semantics for bare keys, nested paths, wildcards, shorthand fallback, headers-ignored-for-body, and empty selector sets.
- **AC-4:** GUI and MCP consumers continue to agree on masked fields for shared fixtures.
- **AC-5:** Tests or measurements demonstrate reduced evaluation/allocation cost for a representative high-selector, nested-payload case relative to baseline.
- **AC-6:** `make check` passes.

## Q&A

**Q1: The Jira summary proposes a lookup structure / prefix trie and stack-based path breadcrumbs. Is that the requirement?**  
**A**: Those phrases describe a suggested technical approach from debt notes. The **requirement** is the business outcome: cheaper, lower-allocation hierarchical matching and path tracking under high-frequency masking, with zero semantic change. Concrete structure choices belong in architecture (Step 2), not as frozen requirements here.

**Q2: Why do this now?**  
**A**: Masking is on the hot path for desktop inspection (including medium-document background formatting) and MCP tool egress. Selector catalogs can already be large at the UI layer. Deferred optimization from PYPOST-1378 becomes valuable once the unified engine and large-catalog workflows are in place.

**Q3: What must never change?**  
**A**: Which fields match; GUI vs MCP agreement; header selectors excluded from body evaluation; non-mutation of raw responses; supported selector vocabulary (no new JSONPath power in this ticket).

**Q4: Implementation language?**  
**A**: Python, within the existing PyPost core masking evaluation used by GUI and MCP consumers.

**Q5: Related work that is explicitly not this ticket?**  
**A**: Hidden Fields virtualization (PYPOST-1386), selector syntax validation (PYPOST-1387), medium-document worker formatting (PYPOST-1396), and streaming sanitizers for extremely large payloads remain separate.

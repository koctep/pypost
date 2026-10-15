# PYPOST-1369: Unify foldable code editor and viewer gutter presentation logic

## Programming Language

Python

## Goals

PyPost provides developers with multiple code display and text authoring surfaces:
- The interactive request body editor (where API requests are constructed and edited).
- The response viewer (where HTTP response payloads are inspected).
- The WebSocket stream viewer (where real-time framed messages are monitored).
- The MCP tool result viewer (where Model Context Protocol responses are displayed).

During the incremental addition of code folding to PyPost (initiated under epic PYPOST-1364 and
PYPOST-1365), gutter presentation, line numbering calculations, fold chevron rendering, and gutter
mouse interaction handling were implemented separately for interactive editors and read-only viewers.
This resulted in duplicated logic and slight behavioral drift across surfaces.

The business reasons for unifying this logic are:

- **Consistent User Experience**: Developers switching between drafting requests and inspecting
  responses expect identical gutter behavior: matching line-number margins, consistent fold chevron
  hitboxes, predictable click/double-click folding response, and synchronized scrolling.
  Inconsistencies between panes create unnecessary cognitive friction.
- **Lower Maintenance Cost**: Currently, any improvement or defect fix applied to gutter rendering
  (such as font metric scaling, high-DPI display adjustments, or margin layout recalculations) must
  be replicated across multiple independent widgets. Unification centralizes these mechanics so fixes
  apply everywhere automatically.
- **Reduced Regression Risk**: Maintaining separate implementations increases the likelihood that
  bug fixes in one widget will miss another, causing subtle regressions and user frustration.
- **Enhanced Development Velocity**: Future editor and viewer enhancements (such as line bookmarking,
  diff indicators, or custom gutter annotations) will build upon a single, reliable presentation
  foundation rather than having to be re-implemented for each view.

## User Stories

- As an **API developer authoring request bodies**, I want the editor gutter (line numbers, fold
  indicators, and margins) to behave consistently with response viewers so that code interaction
  throughout PyPost feels familiar and predictable.
- As an **API developer inspecting API responses or message streams**, I want line numbers and fold
  chevrons to remain accurately aligned with document text during scrolling, window resizing, and
  font size adjustments.
- As an **API developer**, I want existing specialized editing capabilities—including variable
  autocompletion popups, syntax validation banners, bracket pairing, and auto-indentation—to continue
  functioning without any disruption or behavioral regression.
- As an **API developer**, I want existing specialized viewing capabilities—including format
  sniffing (JSON/YAML/XML/Plain), search match reveal, context menu actions, and sensitive field
  masking—to remain completely intact and unaffected.
- As a **PyPost maintainer**, I want gutter presentation, margin calculations, and fold-toggle event
  routing to be defined in a single cohesive place so that future maintenance and enhancements do not
  require duplicate code updates.
- As a **quality engineer**, I want comprehensive automated test coverage for unified gutter
  behaviors across all editor and viewer contexts to ensure long-term stability and regression
  prevention.

## Definition of Done

This task is considered done when:

1. **Gutter Presentation Uniformity**: Line numbers, gutter margins, and fold chevrons (both collapsed
   and expanded states) render with identical alignment, spacing, and styling across all foldable
   code surfaces.
2. **Interactive Uniformity**: Single-click and double-click interactions in the gutter chevron area
   reliably toggle the fold state of the corresponding code block across all surfaces.
3. **Dynamic Layout & Font Responsiveness**: The gutter width automatically recalculates and updates
   when document line counts change (e.g., crossing digit magnitude boundaries like 9 to 10 or 99 to
   100) and when font metrics change.
4. **Scroll & Repaint Synchronization**: Gutter contents remain smoothly synchronized during vertical
   and horizontal scrolling, viewport resizing, and dynamic document updates.
5. **Preservation of Specialized Editor Capabilities (Zero Regressions)**:
   - Variable auto-completion popup and selection.
   - Syntax validation error banners and dynamic banner positioning.
   - Bracket pairing, closing bracket auto-outdent, and newline auto-indentation.
   - Manual reformatting and text replacement workflows.
6. **Preservation of Specialized Viewer Capabilities (Zero Regressions)**:
   - Automatic format detection for JSON, YAML, XML, and plain text.
   - Read-only protection and text selection / clipboard copying.
   - Text search integration (Ctrl+F) and automatic unfolding on match reveal.
   - Sensitive field click-to-reveal masking.
   - Context menu operations (Fold All, Unfold All, Set Variable).
7. **Consolidation of Duplicated Code**: Duplicate implementations of line-number area width
   calculation, gutter painting, and gutter mouse event handling are consolidated into a shared
   component.
8. **Automated Verification**: Automated tests verify gutter layout, chevron painting, interaction
   routing, and font responsiveness, and confirm that all existing test suites for editors and viewers
   pass green.
9. **Quality Gate Compliance**: `make check` (static linting, typechecking, test suites, and
   verification artifacts) passes cleanly.

## Task Description

### Problem Statement

In PyPost, interactive code editing is provided by `CodeEditor` (used in the Request Body tab), while
read-only code viewing is provided by `FoldableCodeView` (used in `ResponseView`, `StreamView`, and
`McpResultView`). Both widgets feature a gutter area that displays line numbers and folding chevrons
to collapse and expand hierarchical blocks (such as JSON objects, YAML maps, or XML tags).

However, `FoldableCodeView` was initially developed independently to avoid destabilizing `CodeEditor`'s
intricate editing machinery. As a result:
- Gutter geometry calculations (`line_number_area_width`, viewport margin adjustments) are duplicated.
- Gutter paint events (`line_number_area_paint_event`), chevron symbol rendering, and line number
  formatting are duplicated.
- Mouse interaction handling (`line_number_area_mouse_press`, coordinate lookup, and fold toggling)
  is duplicated.
- Behavioral differences exist (for example, double-click fold toggling was implemented in
  `FoldableCodeView` but omitted from `CodeEditor`).

This technical debt increases maintenance costs, increases regression risks, and produces subtle
inconsistencies for end users.

### Scope (In-Scope)

- Unifying the gutter geometry and width calculation logic for all foldable code surfaces.
- Unifying line number formatting and fold chevron drawing logic.
- Unifying mouse click and double-click handling within the gutter.
- Unifying font metric change and viewport resize event handling for gutters.
- Ensuring seamless coexistence with specialized editor extensions (autocomplete, validation banner)
  and viewer extensions (masking, search reveal).
- Verifying regression-free operation across all affected views:
  - Request Body Editor (`CodeEditor`).
  - Response Viewer (`ResponseView` / `FoldableCodeView`).
  - WebSocket Stream Viewer (`StreamView`).
  - MCP Tool Result Viewer (`McpResultView`).
- Automated regression and unit test verification.

### Scope (Out-of-Scope)

- Concrete architectural class design and module inheritance hierarchy (strictly deferred to
  Step 2: Architecture).
- Changes to the underlying code folding AST/token parsing algorithms or background scanner logic
  (addressed in separate performance tasks).
- Non-code text fields (such as single-line URL bars, headers tables, or query parameter forms).
- Visual theme redesigns or alterations to syntax highlighter color palettes.

### Functional Requirements

- **FR-1: Gutter Sizing & Line Number Display**:
  - The gutter width must automatically calculate sufficient space for the fold chevron and the
    maximum line number digits in the document, plus standard margin padding.
  - Line numbers must be right-aligned with consistent horizontal margins.
  - The gutter width must dynamically update when line counts change or fonts change.
- **FR-2: Fold Indicator Presentation**:
  - The gutter must display an expanded indicator (`▼`) for expanded foldable blocks and a collapsed
    indicator (`▶`) for collapsed blocks.
  - Indicators must only appear on lines corresponding to valid fold region headers.
  - Lines without fold headers must leave the chevron area blank while displaying line numbers.
- **FR-3: Gutter Mouse Interaction**:
  - Clicking within the chevron zone of a fold header line must toggle that region's fold state.
  - Double-clicking anywhere on a fold header line in the gutter must toggle the fold state.
  - Clicks outside fold header lines or non-left clicks must not trigger fold toggling.
- **FR-4: Document Synchronization**:
  - Gutter content must stay perfectly synchronized with document scrolling (both vertical and
    horizontal).
  - Bulk operations ("Fold All", "Unfold All") must trigger immediate gutter repaint and margin
    recalculation.
- **FR-5: Editor Capabilities Preservation**:
  - Variable autocompletion popup positioning and selection must remain fully functional.
  - In-line syntax validation error banners must position and display accurately.
  - Auto-indentation and bracket outdenting must function without disruption.
- **FR-6: Viewer Capabilities Preservation**:
  - Content-Type format detection (JSON/YAML/XML/Plain) must continue to configure fold controllers.
  - Sensitive field click-to-reveal masking must continue to function alongside gutter indicators.
  - Text search reveal must continue to expand collapsed blocks when matches are found.

### Non-Functional Requirements

- **NFR-1 UX Consistency**: Gutter visual layout, typography, click responsiveness, and folding
  indicators must be completely uniform across all editor and viewer contexts.
- **NFR-2 Performance & Fluidity**: Gutter repainting and width recalculations must be lightweight
  and introduce no noticeable latency or stutter during high-speed typing, scrolling, or document
  loading.
- **NFR-3 Backward Compatibility**: All existing public interfaces, signals, and properties relied
  upon by parent views and tests must be preserved without breaking contracts.
- **NFR-4 Maintainability**: Redundant gutter management and chevron painting logic must be
  consolidated into a single shared mechanism, eliminating duplicate code paths.

### Main System Components (High-Level Domain)

| Component | Domain Responsibility |
| --- | --- |
| **Interactive Code Editor** | User-facing component for editing request text, managing completions, bracket pairing, and validation feedback. |
| **Read-Only Code Viewer** | User-facing component for inspecting structured response bodies, detecting formats, and handling masking. |
| **Foldable Gutter Presentation** | Presentation component responsible for rendering line numbers, drawing fold chevrons, and sizing viewport margins. |
| **Gutter Interaction Coordinator** | Interaction component responsible for mapping gutter mouse clicks to document lines and fold header toggles. |
| **Code Folding Controller** | Core domain component responsible for maintaining fold regions, tracking collapsed states, and altering block visibility. |

## Q&A

- **Q1: Why is this refactoring necessary when both `CodeEditor` and `FoldableCodeView` already work?**
  - **A**: Although both widgets function today, their gutter painting, chevron drawing, margin
    sizing, and click-dispatch logic are duplicated copies. This creates subtle behavioral
    discrepancies (e.g. double-click fold behavior present in one widget but missing in another) and
    doubles the engineering effort required whenever gutter rendering, high-DPI scaling, or font
    handling is enhanced. Consolidating this logic guarantees user-facing consistency and reduces
    long-term maintenance overhead.

- **Q2: Does this task introduce any new user-visible features or alter visual designs?**
  - **A**: No new visual styling is introduced. The focus is purely on achieving 100% behavioral and
    visual consistency across existing editors and viewers, ensuring that features like chevron
    double-click folding and proper margin recalculation work uniformly everywhere.

- **Q3: How do we verify that complex features like variable completion and response masking are not broken?**
  - **A**: Acceptance criteria require complete preservation of all specialized capabilities, validated
    by the existing comprehensive automated test suites for `CodeEditor`, `ResponseView`,
    `FoldableCodeView`, `StreamView`, and `McpResultView`.

- **Q4: Are implementation details (e.g., base class inheritance vs. mixin composition) decided in this document?**
  - **A**: No. Per the Top-Down methodology, architectural and technical implementation decisions
    (such as whether to extract an abstract base class or use a mixin pattern) belong strictly in
    Step 2 (`20-architecture.md`). This document defines the business goals, user stories, functional
    requirements, and acceptance criteria.

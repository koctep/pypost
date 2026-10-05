# PYPOST-1259: Migrate dialog audit report verification to structural markdown AST parsing

## Goals

- **Business Value & Reliability**: Prevent false-positive CI test failures and development
  interruptions caused by cosmetic prose adjustments, whitespace changes, or paragraph line
  wrapping in architectural audit reports.
- **Contract Fidelity**: Ensure that contract verification for architectural audit reports strictly
  validates underlying factual invariants, inventory counts, and domain claims without coupling
  verification to literal text formatting.
- **Maintainability & Documentation Velocity**: Empower maintainers and AI agents to update
  documentation style, fix typographical errors, or reflow markdown paragraphs freely while
  retaining robust automated contract validation.

## User Stories

### Story 1: Documentation Author
As a repository documentation author or auditor,
I want to format, reword, or reflow paragraphs in `30-dialogs-audit-report.md` without breaking CI,
So that documentation maintenance is not blocked by rigid, character-for-character test assertions.

### Story 2: CI / Quality Engineer
As a quality engineer,
I want contract tests to assert structural invariants (headings, table rows, metadata, claims)
reliably,
So that CI regressions are flagged only when actual report facts or architectural contracts drift.

### Story 3: Core Developer
As a core developer modifying dialog components,
I want the verification suite to provide deterministic, actionable validation of dialog inventory,
So that discrepancy failures clearly identify missing dialogs or line-count drift rather than
formatting glitches.

## Definition of Done

- All brittle literal string matching in `tests/test_pypost_1077_verification_artifacts.py` is
  replaced with structural, formatting-resilient verifications.
- Word wrapping, newline insertions/deletions, and whitespace variations across prose paragraphs
  do not break dialog audit report verification.
- The underlying validation contract remains 100% sound:
  - Exact module inventory coverage (9 dialog modules, corresponding line counts).
  - Scope declaration (scope path, 9 modules, 1,790 total LOC).
  - Executive summary key architectural claims (3 MCP dialogs, read-only designation for
    activity/tools, server manager mutation capability).
  - Testability table completeness across all 9 dialog modules.
  - Completion verdict affirmation for all 9 modules.
  - Prohibition of contradictory historical stale claims across the document.
- Scope boundary is strictly maintained: only `tests/test_pypost_1077_verification_artifacts.py`
  is updated; production code in `pypost/` and actual report data in `ai-tasks/PYPOST-374/` remain
  unaltered unless necessary to preserve contract semantics.
- All test runs (`make test`, `make check`) pass cleanly.
- All lines in documentation artifacts are strictly <= 100 characters.

## Task Description

### Problem Statement
In `tests/test_pypost_1077_verification_artifacts.py`, the test
`test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` inspects the markdown report
`ai-tasks/PYPOST-374/30-dialogs-audit-report.md`. However, it relies on brittle string-matching
mechanisms:
1. Hardcoded line breaks in assertions, such as `"The activity and tools dialogs\nare read-only"`.
   Any automated markdown formatter or author reflow immediately breaks this test.
2. Rigid subsection extraction via `str.index(...)` over exact heading string matches that fail if
   surrounding markdown spacing or syntax fluctuates.
3. Multiple brittle alternate literals (e.g. checking whether scope has "nine modules" vs
   "nine dialog modules") instead of extracting structured metadata.
4. Literal punctuation and formatting assertions (e.g. `"Individual audit **complete** for all
   nine modules."`) that tie the test to precise bold markdown tokens and punctuation.

### Programming Language
- **Implementation language**: Python (per repository standards and test harness).

### Functional Requirements
1. **Section and Structural Extraction**:
   - The verification test must identify sections by heading semantics (e.g., Markdown headings at
     level 2 or level 3) rather than raw string index offsets.
   - The test must extract table data (such as the Module Inventory table and the Testability
     summary table) into structured records (module name, metrics, annotations).
2. **Formatting & Prose Decoupling**:
   - Paragraph text matching must normalize whitespace sequences (tabs, spaces, newlines) into
     single spaces to tolerate word-wrapping and line reflows.
   - Punctuation, emphasis markers (e.g., `**`, `*`, `` ` ``), and formatting artifacts must either
     be stripped during text normalization or handled structurally so that semantic assertions
     target content rather than styling syntax.
3. **Core Verification Invariants (Sound Contract)**:
   - *Discovery & Aggregates*: Inventory table must contain exactly the 9 discovered dialog modules
     and their respective line counts totaling 1,790 LOC.
   - *Scope Metadata*: Report header/scope must specify target directory `pypost/ui/dialogs/`,
     module count 9, and 1,790 total LOC.
   - *Executive Summary*: Must affirm 3 MCP dialogs, distinguish read-only status for activity and
     tools, and identify server manager mutation capability.
   - *Testability Completeness*: Testability table must list each of the 9 dialog modules.
   - *Verdict*: Report must affirm audit completion across all 9 modules.
   - *Absence of Stale Claims*: Ensure contradictory historical markers (e.g., 7 or 8 modules,
     previous LOC totals like 923, 1030, 1208, 1747, 446, "Two MCP read-only dialogs") are not
     present.
4. **Resilience to Document Reordering**:
   - Section inspection must locate sections independently of document order where possible, rather
     than relying on consecutive string slicing (`_section(report, start_heading, end_heading)`).

### Non-Functional Requirements
1. **Performance**: Verification execution must complete in < 0.5s per run with no heavyweight
   external parsing dependencies.
2. **Simplicity and Maintainability**: Clear, readable assertion logic adhering to PEP 8.
3. **Test Timeout Compliance**: Preserve module-level `@pytest.mark.timeout(10)` or equivalent.

### Scope Boundaries
- **In Scope**:
  - Refactoring assertion logic and helper utilities in
    `tests/test_pypost_1077_verification_artifacts.py`.
- **Out of Scope**:
  - Modifying application runtime code under `pypost/`.
  - Modifying unrelated contract tests in `tests/test_pypost_1077_verification_artifacts.py`
    (e.g., function catalog, Jira smoke board contract, encrypted startup seam tests).
  - Modifying audit inventory generator `scripts/audit_dialogs_inventory.py`.

## Q&A

### Q1: Why not simply change `\n` to `\s+` in regexes?
A1: While regex whitespace normalization is part of the solution, raw string matching without
structural section extraction still couples assertions to document structure and surrounding text.
Structural extraction isolates tables and sections first, making assertions independent of document
reorganization.

### Q2: Should external heavy markdown libraries (like mistune or markdown-it-py) be introduced?
A2: No new dependencies should be introduced unless already part of the project environment.
Standard library (`re`, custom AST/regex tokens) or already-installed utilities provide sufficient
power without increasing dependency footprint.

### Q3: Does this loosen the contract checks?
A3: No. The semantic verification contracts remain equally strict: every dialog module, line count,
total LOC, and architectural assertion must still hold true. Only the formatting rigidity (word
wraps, newlines, markup styling) is decoupled.

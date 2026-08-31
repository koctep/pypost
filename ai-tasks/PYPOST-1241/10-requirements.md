# PYPOST-1241: Restore make typecheck gate by reconciling mypy baseline and type errors

## Goals

The PyPost codebase relies on an automated type checking quality gate (`make typecheck`) to guarantee static type correctness across its core, model, and UI packages. This gate enforces a strict ratchet mechanism using a baseline manifest:
1. No new, unbaselined type errors may be introduced.
2. Any existing errors that are resolved must be removed from the baseline manifest so that regressions cannot be reintroduced later.

During development and pre-commit checks in PYPOST-1041, the `make typecheck` gate was found to be broken at `HEAD` (reporting 240 current errors against a 201-error baseline, causing exit code 1). This failure is independent of any feature working tree and stems from recent additions across save orchestrators, presenters, and UI widgets that introduced unbaselined type mismatches, as well as several previously baselined errors that have since been resolved.

The primary business and quality goal of this task is to **restore the static type checking quality gate to a green, passing state (`make typecheck`)** by:
- Eliminating newly introduced type mismatches through sound type annotations and contract alignment.
- Retiring resolved entries from the baseline manifest to maintain the ratchet invariant.
- Unblocking developer workflows and continuous integration pipelines that depend on a passing quality gate.

## Programming Language

Python (with PySide6). Workflow and documentation artifacts are written in English Markdown.

## User Stories

- As a **PyPost Developer**, I want `make typecheck` to execute cleanly with an exit status of 0 so that pre-commit workflows and automated quality checks pass without false-positive failures.
- As a **PyPost Software Engineer**, I want save orchestrators and tab presenters for all connection protocols (HTTP, WebSocket, MCP) to have accurate and coherent type contracts, so that type checking catches actual defects and prevents regressions in tab persistence logic.
- As a **Release Engineer / CI Maintainer**, I want the baseline gate ratchet to remain strictly enforced—failing when new type regressions are introduced or when resolved errors are not retired—so that codebase type hygiene continuously improves and never deteriorates.
- As an **Architecture Guardian**, I want genuine type-model mismatches to be addressed through proper typing and interface abstractions rather than by indiscriminately adding defects to the baseline, preserving the integrity of static analysis.

## Definition of Done

The task is considered done when all of the following acceptance criteria are met:

- **AC-1 (Gate Success):** Invoking `make typecheck` completes with exit code 0 and reports that current errors match the baseline.
- **AC-2 (Zero Unbaselined Errors):** There are zero new or unbaselined type check errors across `pypost/core`, `pypost/models`, and `pypost/ui`.
- **AC-3 (Ratchet Maintained):** All resolved baseline errors are retired from `mypy-baseline.json` so that resolved issues cannot regress undetected.
- **AC-4 (Sound Contract Alignment):** Genuine type inconsistencies in protocol save orchestrators and tab presenter components are properly typed and contractually aligned, avoiding blanket or unsafe suppression.
- **AC-5 (Test & Lint Invariance):** The existing fast test suite (`make test`) and lint checks (`make lint`) pass with zero regressions or errors.
- **AC-6 (Quality Gate Verification):** The full quality gate (`make check`) passes cleanly.

## Task Description

### Problem Statement

The repository's type checking gate (`scripts/check_mypy_baseline.py` invoked via `make typecheck`) compares live static type analysis results against `mypy-baseline.json`. The gate currently fails:
- Live analysis reports 240 errors.
- The recorded baseline contains 201 errors.
- 4 previously baselined entries across environment variables, request services, settings dialogs, and request editors have been resolved and must be retired.
- Approximately 33 new errors have appeared across multiple newly added or modified modules (such as `websocket_save_orchestrator`, `mcp_client_save_orchestrator`, `tabs_presenter`, `tabs_presenter_ws_close`, `tabs_presenter_mcp_close`, `library_dialogs`, and related UI components).

As a result, CI and developer quality gates fail on every run, impeding normal task development and risking the accumulation of untracked type regressions.

### Business Reason

Static type checking is PyPost's automated safety net against interface mismatches, broken method signatures, and unexpected `None` values in complex UI orchestration. A red gate destroys trust in CI, forces developers to ignore gate failures, and blocks automated release validation. Restoring the gate to green ensures that developers receive immediate feedback on actual regressions.

### Scope Boundaries

#### In Scope

- Diagnosing and categorizing all errors reported by `make typecheck` that differ from the current baseline.
- Resolving genuine type and interface mismatches in `pypost/` modules (e.g., protocol parameterization between HTTP, WebSocket, and MCP client save flows; close prompt signatures; connection attribute contracts).
- Updating `mypy-baseline.json` to retire resolved errors and, where appropriate, recording known external PySide6 stub limitations that match existing repository baseline patterns.
- Ensuring `make typecheck`, `make lint`, and `make test` all pass cleanly.
- Providing documentation in task artifacts tracking the resolved error clusters and baseline reconciliation.

#### Out of Scope / Exclusions

- Modifying runtime behavior, business logic, or user-visible features of WebSocket or MCP client tabs beyond type signature and contract alignment.
- Weakening global type checker configuration (e.g., disabling mypy error codes or loosening flags in `pyproject.toml`).
- Large-scale refactoring of unrelated subsystems not touched by the type check delta.
- Adding arbitrary `# type: ignore` comments where proper type annotations can be cleanly applied.

## Functional Requirements

- **FR-1 (Clean Quality Gate):** The command `make typecheck` must run static type analysis on `pypost/core`, `pypost/models`, and `pypost/ui` and exit with code 0.
- **FR-2 (Contract Alignment in Protocol Save Orchestrators):** Save result structures and stale-check context representations must cleanly accommodate protocol-specific connection types (HTTP requests, WebSocket connections, MCP client connections) without static type incompatibilities.
- **FR-3 (Consistent Close Dialog Callback Signatures):** Tab close helpers and prompt callback signatures must align with the parameters expected by dialog callers (including keyword argument contracts).
- **FR-4 (Baseline Reconciliation):** The baseline file (`mypy-baseline.json`) must accurately reflect only legitimately baselined errors, removing all entries that have been resolved.
- **FR-5 (Static Gate Ratchet Enforcement):** Future introductions of unbaselined errors or silent resolution of baselined errors must continue to trigger gate failures.

## Non-Functional Requirements

- **NFR-1 — Execution Performance:** Running `make typecheck` must complete within normal developer workflow expectations without hanging or timing out.
- **NFR-2 — Determinism:** Typecheck validation and baseline comparison must be strictly deterministic and independent of local paths or operating system differences.
- **NFR-3 — Backward Compatibility:** All changes to signatures and type annotations must preserve existing runtime behavior and API compatibility.
- **NFR-4 — Tooling Standard Compliance:** All repository operations and verifications must strictly utilize `make` targets (`make typecheck`, `make lint`, `make test`, `make check`).

## Constraints and Assumptions

- Python 3.10+ type annotations are used throughout the repository.
- The baseline gate uses multiset comparison keyed on `(path, code, message)` to remain robust against shifting line numbers.
- PySide6 type stubs have known omissions (e.g. `QToolButton.InstantPopup`), which are established baseline candidates in the repository when stubs cannot be patched upstream.
- All code changes must adhere to repository lint standards (`make lint`).

## Main Entities and Interactions

- **Static Type Checking Gate (`make typecheck`):** The automated pipeline gate that runs static analysis across target packages and verifies results against the baseline.
- **Error Baseline Manifest (`mypy-baseline.json`):** The versioned multiset record of known legacy type errors, serving as the upper bound for acceptable errors.
- **Protocol Save Orchestration Entities:** Components responsible for coordinating dirty checks, stale state detection, and persistence across HTTP requests, WebSocket sessions, and MCP client sessions.
- **Tab Presenter and Dialog Callbacks:** Presentation-tier entities managing tab lifecycles, user prompts upon tab closure, and view-model synchronization.

## Q&A

- **Q: Why did `make typecheck` fail when the prior ticket (PYPOST-1041) only touched tests?**
  - **A:** The failure was pre-existing at `HEAD`. Several feature branches merged significant additions (~14k lines across 104 modules) since the baseline was last updated at commit `f6c1124`, introducing new type errors and resolving several old ones without updating the baseline or aligning type models.
- **Q: Should all new errors simply be added to `mypy-baseline.json`?**
  - **A:** No. A significant portion of the new errors (e.g. save orchestrator protocol assumptions, callback argument mismatches) are genuine type model defects that should be resolved in the code. Only unfixable external stub limitations (like PySide6 stub defects) should be baselined, following project norms.
- **Q: Does this task introduce any changes to the UI or runtime functionality?**
  - **A:** No. The objective is purely static typing contract alignment and quality gate restoration. Runtime behavior must remain unchanged and verified by the existing test suite.

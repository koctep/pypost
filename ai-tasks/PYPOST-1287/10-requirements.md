# PYPOST-1287: Restore an accurate, drift-proof dialog audit inventory

**Implementation language:** Python

## Goals

The PYPOST-374 dialog audit report
(`ai-tasks/PYPOST-374/30-dialogs-audit-report.md`) is a documentation-as-contract artifact. The
developer docs (`doc/dev/verification_artifact_contracts.md`) promise that the report matches the
dialog modules that actually exist in `pypost/ui/dialogs/`. Maintainers, reviewers, and AI agents
use it to decide where SOLID and testability work is needed, so wrong size figures send that work
to the wrong place.

The business goals are:

- **Trustworthy audit data**: the report's module inventory and totals describe the codebase as
  it is today, not a June 2026 snapshot.
- **Early drift detection**: when a dialog module is added, removed, or changes size, the quality
  gate fails and says exactly what is out of date. Drift is not discovered weeks later by chance.
- **Low maintenance cost**: legitimate dialog growth only requires a report refresh. Nobody has to
  edit pinned numbers inside test code.

## Current State (verified at `aef30005`)

- Command: `make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1077_verification_artifacts.py -q'`
- Result: **passed** (1 file, 4 tests passed). The failure that Jira describes (seen at `1b990ba5`)
  no longer reproduces.
- Why it passes: PYPOST-1259 (`23e66c84`, committed) rewrote the test with structural markdown
  parsing. That rewrite dropped the comparison between discovered LOC and report LOC. The test now
  checks only that the report agrees with itself (its rows sum to 1,790 and it lists
  `mcp_servers_dialog.py` at 486), plus filename coverage.
- The data is still stale, but the gate no longer reports it:

| Module | Report LOC | Discovered LOC |
| --- | ---: | ---: |
| `about_dialog.py` | 43 | 43 |
| `env_dialog.py` | 112 | 112 |
| `hotkeys_dialog.py` | 69 | 69 |
| `library_dialogs.py` | 533 | 703 |
| `mcp_activity_dialog.py` | 117 | 117 |
| `mcp_servers_dialog.py` | 486 | 1,031 |
| `mcp_tools_overview_dialog.py` | 74 | 74 |
| `save_dialog.py` | 93 | 93 |
| `settings_dialog.py` | 263 | 263 |
| **Total (9 modules)** | **1,790** | **2,505** |

- Other places that still cite the old figures: the report's Scope line, its Total line, and its
  prose ("The 486-LOC dialog ..." in the `mcp_servers_dialog.py` assessment);
  `doc/dev/verification_artifact_contracts.md` (1,790 / 486). `doc/dev/solid_audit.md:120-121`
  also cites old figures (9 modules / 1,787 LOC, `mcp_servers_dialog.py` growth to 486 LOC), but
  that text is a dated PYPOST-1111 changelog entry, i.e. a historical record, not current contract
  text.

So the defect has changed. It is no longer a red test. It is now a **silent false pass**: the
contract is documented as "matches discovery exactly", but nothing enforces it.

## User Stories

- As a **maintainer reading the dialog audit**, I want the inventory and totals to match the
  current dialog modules, so that I can rank refactoring and test work by real size.
- As a **developer who changes a dialog**, I want the quality gate to tell me which module's
  recorded size is out of date and what the current value is, so that I can refresh the report
  in one pass.
- As a **developer who changes a dialog**, I do not want to edit hard-coded numbers in test code,
  so that normal feature growth does not turn into test maintenance.
- As a **reviewer**, I want the developer docs to describe the contract that is actually enforced,
  so that I don't approve against outdated rules.

## Definition of Done

1. **Report accuracy**: in `ai-tasks/PYPOST-374/30-dialogs-audit-report.md`, the Module Inventory
   lists every discovered dialog module exactly once, with the LOC that discovery reports at the
   time of the change. Today that is nine modules, 2,505 LOC in total, including
   `library_dialogs.py` at 703 and `mcp_servers_dialog.py` at 1,031.
2. **Aggregate coherence**: the report's Scope line, its Total line, and the sum of the inventory
   rows all state the same module count and total LOC, and that total equals the discovered total.
3. **No superseded figures**: the report has no leftover statement of the old totals or sizes
   (1,790 LOC total, `mcp_servers_dialog.py` 486 LOC, `library_dialogs.py` 533 LOC), and no prose
   that contradicts the refreshed inventory.
4. **Drift detection restored**: the verification fails with a clear message when any of the
   following holds:
   - a discovered module is missing from the inventory, or the inventory lists a module that does
     not exist; the message names that module;
   - any module's recorded LOC differs from its discovered LOC; the message names the module and
     both values (recorded and discovered);
   - the declared module count or total LOC differs from the discovered one; the message reports
     both values (declared and discovered).
5. **No pinned snapshot**: the verification contains no literal per-module LOC values, no
   literal total LOC, and no literal module count (today's check pins "nine"). Expected values
   come only from the current dialog modules. A synthetic change to a dialog's size or to the set
   of dialog modules (for example in an isolated test fixture) fails the check, and a matching
   report refresh makes it pass again.
6. **Semantic invariants preserved**: the qualitative contracts from PYPOST-1077 and PYPOST-1259
   still hold. These are: required sections (Module Inventory, Testability summary, Executive
   Summary, Verdict); one testability row per discovered module; three MCP dialogs, of which the
   activity and tools dialogs are read-only and the server manager is mutable; a completion
   verdict that covers every module; and the prohibition of historical stale claims.
7. **Documentation aligned**: the current contract text in
   `doc/dev/verification_artifact_contracts.md` describes the enforced contract ("matches
   discovery") and either drops the 1,790 / 486 snapshot figures or updates them to current values.
   Dated historical or changelog entries (for example the PYPOST-1111 entry in
   `doc/dev/solid_audit.md`, which cites 1,787 / 486) stay as written; they may be annotated as
   superseded, but are not rewritten. Only current contract text must match discovery.
8. **Gates green**: the targeted run
   `make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1077_verification_artifacts.py -q'`
   passes, and `make check` reports no failure outside the documented, filed pre-existing set
   (for example PYPOST-1298, PYPOST-1299). Any other failure is either fixed in this
   task or shown by a baseline run at `aef30005` to fail there with the same error, then filed.

## Task Description

### Problem

The dialog audit report records a size snapshot from mid-2026. Since then the dialogs have grown
by 715 LOC, mostly in the MCP server manager and the library dialogs. The report is now wrong,
and the verification meant to guard it no longer compares it with the real codebase. The original
symptom, a test pinned to 1,790 / 486 that went red when dialogs grew, was the opposite failure
mode. Both come from the same cause: the expected figures were frozen as constants instead of
coming from the codebase.

### Scope

In scope:

- Refreshing the inventory figures, aggregates, and any figure-dependent prose in the PYPOST-374
  dialog audit report.
- Restoring automated detection of drift between the report and the actual dialog modules, with no
  pinned snapshot values.
- Updating the developer documentation that describes this contract.

Out of scope:

- A new SOLID re-audit of the grown dialogs. Ratings and recommendations stay as they are unless
  a sentence directly contradicts the new figures. Any re-audit need becomes a follow-up.
- Refactoring or shrinking any dialog module.
- Changing how a "line of code" is counted. The existing discovery definition (total physical lines
  per module, excluding `__init__.py`) stays.
- The structural markdown parsing introduced by PYPOST-1259. It stays as delivered.
- The other three tests in the same file (function catalog, Jira smoke, encrypted startup seam).

### Business Entities

- **Dialog module**: a UI dialog source file under `pypost/ui/dialogs/` (excluding the package
  marker). Attributes: filename, LOC.
- **Dialog discovery**: the authoritative, current list of dialog modules and their LOC.
- **Dialog audit report**: the PYPOST-374 document. Attributes: scope statement (module count, total
  LOC), module inventory (filename → LOC), testability summary, executive summary, verdict.
- **Audit contract verification**: the automated check that the report agrees with discovery and
  holds its semantic invariants.

### Constraints

- All checks run only through `make` targets (`make test`, `make check`), per `AGENTS.md`.
- The verification must stay offline, deterministic, and inside the existing 10-second per-test
  timeout.
- No new third-party dependencies.

## Q&A

### Q1: The test passes at `aef30005`. Is the ticket obsolete?

A1: No. PYPOST-1259 made the test green by removing the comparison with discovery, not by
refreshing the data. The report is still wrong (1,790 recorded, 2,505 discovered), and
`doc/dev/verification_artifact_contracts.md` still promises an exact match with discovery. The
PYPOST-1259 tech-debt entry (`ai-tasks/PYPOST-1259/60-tech-debt.md`) explicitly hands "refreshing
the report and synchronizing on-disk LOC discovery" to this ticket. Assumption: the goal is to
close that gap, not only to make a red test green.

### Q2: Should the exact-match contract be relaxed (for example, a tolerance band)?

A2: No (assumption). The documented contract is an exact match, and discovery already gives exact
figures. Removing pinned values from the verification handles the maintenance cost. A tolerance
band would let the report drift again without anyone noticing.

### Q3: Is the module count "nine" also a pinned snapshot?

A3: Yes. Like LOC, the expected count must come from discovery (assumption). The refreshed report
states nine modules because nine exist today. Required prose such as "complete for all nine
modules" must state the discovered count, not a fixed word.

### Q4: Does refreshing figures require re-rating SOLID compliance of the grown dialogs?

A4: No (assumption, see Scope). Only figures and sentences that cite figures get updated. If the
growth seems to invalidate a rating, that is recorded as a follow-up in Step 7.

### Q5: Was Jira consulted for clarification?

A5: No. Per the orchestrator's instructions this step does not call Jira or ask the user. The
answers above are documented assumptions for the reviewer to confirm.

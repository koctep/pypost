# Verification-Artifact Contracts (PYPOST-1077)

## Overview

PYPOST-1077 restores four existing verification artifacts that protect established application
contracts. They prevent a release from silently accepting an incomplete dialog audit, an
inaccurate permitted-function catalog, a Jira smoke check with incomplete pagination inputs, or
a startup test double that fails before exercising the encrypted-startup readiness gate.

This work does not introduce a runtime API, configuration setting, environment variable, or new
product capability. It restores documentation and test declarations around existing behavior.

## Contract Architecture

The focused artifact validator in `tests/test_pypost_1077_verification_artifacts.py` validates
the declarations below without contacting Jira or another external service.

- **Dialog audit completeness:** dialog discovery is the source of truth for the
  [PYPOST-374 audit report](../../ai-tasks/PYPOST-374/30-dialogs-audit-report.md).
- **Permitted functions:** `FunctionRegistry.allowed_names()` is locked by
  `tests/test_function_registry.py`.
- **Jira board pagination:** the shipped Jira request fixture is locked by
  `tests/test_jira_mcp_live_smoke.py`.
- **Encrypted-startup restore gate:** the `MainWindow` two-signal readiness barrier is covered
  by `tests/test_main_window_encrypted_startup.py`.

The dialog report is documentation-as-contract. It must match discovery exactly: every expected
module name, per-module LOC, total LOC, and module count is derived from
`discover_dialog_modules()` at test time, so the validator pins no snapshot figures. Its
three-MCP-dialog summary, testability table, and completion verdict must describe that same
inventory.

The other validators parse test artifacts with Python ASTs. They lock the approved four-name
function catalog, the exact `jira-list-boards` pagination inputs and deterministic call values,
and the deferred environment presenter's constructor seam. The existing focused tests retain
runtime, fixture, and two-signal restore-order coverage.

### Structural Markdown AST Verification (PYPOST-1259)

The dialog audit report validator in `tests/test_pypost_1077_verification_artifacts.py`
parses the audit report structurally using lightweight AST helpers:

- `MarkdownSection`: dataclass encapsulating section `title`, heading `level`, and `content`.
- `_parse_markdown_sections`: partitions documents into heading-bound sections, ignoring code
  blocks and providing case-insensitive section lookups.
- `_parse_markdown_table`: parses GitHub-Flavored Markdown tables into row dictionaries mapping
  normalized column headers to cell text values.
- `_normalize_prose`: collapses contiguous whitespace sequences and strips inline markdown
  formatting (links, emphasis, inline code) for reflow-agnostic prose comparisons.

This AST architecture decouples contract validation from formatting churn such as
line-wrapping, table column padding, whitespace variations, and non-breaking heading
reordering. At the same time, it strictly enforces semantic architectural invariants:

1. **Complete inventory coverage:** every discovered dialog module appears exactly once; each
   missing, unknown, or duplicated module is reported by name.
2. **Discovered line counts:** every row LOC is a positive number equal to the module's
   discovered `total_lines`. The row sum and the LOC in the Scope and Total lines equal the
   discovered total.
3. **MCP dialog distinction:** explicit categorization of the 3 MCP dialogs versus
   standard dialogs.
4. **Testability & verdict assertions:** the testability summary lists exactly the discovered
   modules, and the Scope module count and the `Individual audit complete for all <n> modules.`
   verdict state the discovered module count (digits or an English word).

The validator is the pure helper `_dialog_audit_report_errors(report_markdown, modules)`; the
live test is a thin wrapper around it. It reports one message per violation and prints parsed
integers, in the shapes `<module>: recorded LOC <r> != discovered LOC <d>` and
`scope total LOC: declared <x> != discovered <total>`, so one failing run lists every value a
report refresh must change.

Regression coverage for the discovery-driven validator lives in
`tests/test_pypost_1287_failing_repro.py` (PYPOST-1287). Cases 1-4 monkeypatch the module-level
seams (`discover_dialog_modules`, `check_audit_report_covers`, `_DIALOG_AUDIT_REPORT`) to feed
synthetic discovery and a synthetic report to the live test:

1. A coherent report passes.
2. Per-module LOC drift names the module, recorded LOC, and discovered LOC.
3. A missing and an unknown module each appear on some message line; the message shape and
   the R6 testability message are not asserted.
4. Scope count and Scope/Total LOC drift report declared versus discovered integers.

Case 5 (`test_live_report_inventory_loc_matches_discovery`) uses no seam and checks no message:
it compares the real report's inventory LOC with real discovery as dictionaries.

### Known Limitations

- The stale-claim denylist still holds count-specific phrases such as `all eight modules`,
  and prose figures such as the Executive Summary module count and `At 263 LOC` are not
  checked against discovery; a report refresh re-checks them by hand. Count-agnostic
  stale-claim and prose rules are tracked in PYPOST-1308.
- The denylist also holds the bare figures `446` and `1,747`, matched as substrings of the
  whole report, so a refreshed figure containing them (for example `2,446` or `11,747` LOC)
  fails with a false stale-claim error. Word-bounded or removed entries are tracked in
  PYPOST-1308.
- The validator and the PYPOST-1259 Markdown helpers live in the PYPOST-1077 test module, and
  both repro modules import private names from it; several validator branches have no
  synthetic case. Extraction to a shared test helper with direct branch tests is tracked in
  PYPOST-1310.

## Usage

Run the focused offline verification through the Makefile:

```bash
make test PYTEST_ARGS='tests/test_pypost_1077_verification_artifacts.py \
tests/test_function_registry.py tests/test_jira_mcp_live_smoke.py \
tests/test_main_window_encrypted_startup.py -q'
```

To inspect or check the dialog report separately:

```bash
.venv/bin/python scripts/audit_dialogs_inventory.py --markdown
.venv/bin/python scripts/audit_dialogs_inventory.py --check
```

These direct script calls have no make target yet; one is tracked in PYPOST-1307.

The live Jira operation remains separately protected. Do not enable it merely to validate these
contracts; see [Optional Live Jira MCP Smoke](jira_mcp_live_smoke.md) for authorized opt-in use.

## Configuration

PYPOST-1077 adds no configuration. The focused verification is local and does not require Jira
credentials, a Jira URL, or `PYPOST_LIVE_JIRA_SMOKE`. The separate live smoke retains its
existing protected configuration and authorization requirements.

## Troubleshooting

### Dialog artifact test reports missing coverage or inconsistent totals

The report is refreshed by hand. The failure message lists every value to change, one line per
violation, as recorded versus discovered (for example
`<module>: recorded LOC <r> != discovered LOC <d>`). Update each inventory row, the Scope LOC
and module count, the Total line, and the verdict count to the discovered values, then
re-check prose figures by hand.

When a dialog module is added or removed, also:

- Add or remove its row in the Testability summary table. R6 (`_testability_errors`) fails
  until that table lists exactly the discovered modules.
- Add or remove its ``### `<module>.py` — <Class(es)>`` section under SOLID Assessment by
  Dialog. The validator does not check these sections, so the refresh must.

Verify with:

```bash
make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1077_verification_artifacts.py -q'
```

Do not exclude a dialog module from discovery. A make target for refreshing the inventory is
tracked in PYPOST-1307.

### Function catalog assertion fails

Compare the expected immutable set with `FunctionRegistry.allowed_names()`. Keep equality so both
missing and unapproved names fail.

### Jira board contract reports an input mismatch

Keep `maxResults` and `startAt` as the exact inputs, and call the board tool with
`{"maxResults": 50, "startAt": 0}`. Do not broaden the read-only tool allowlist.

### Encrypted-startup test fails before readiness assertions

Ensure the deferred environment presenter double provides
`mcp_controls` with `set_server_controller`. Preserve the assertion that tabs and tree restore only
after both signals.

For broader test-environment and Qt guidance, see [Testing via MCP and Prometheus](testing.md)
and [Unit Testability Patterns](testability.md).

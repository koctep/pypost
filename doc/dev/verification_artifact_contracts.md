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

The dialog report is documentation-as-contract. It must match discovery exactly: nine modules,
1,790 LOC, and one `mcp_servers_dialog.py` entry at 486 LOC. Its three-MCP-dialog summary,
testability table, and completion verdict must describe that same inventory.

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

1. **Complete inventory coverage:** all 9 dialog modules must appear exactly once.
2. **Positive line counts:** valid numeric LOC for all rows, summing to 1,790 total LOC
   and 486 LOC for `mcp_servers_dialog.py`.
3. **MCP dialog distinction:** explicit categorization of the 3 MCP dialogs versus
   standard dialogs.
4. **Testability & verdict assertions:** all 9 modules present in testability summaries with
   required audit verdicts and scope statements intact.

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

The live Jira operation remains separately protected. Do not enable it merely to validate these
contracts; see [Optional Live Jira MCP Smoke](jira_mcp_live_smoke.md) for authorized opt-in use.

## Configuration

PYPOST-1077 adds no configuration. The focused verification is local and does not require Jira
credentials, a Jira URL, or `PYPOST_LIVE_JIRA_SMOKE`. The separate live smoke retains its
existing protected configuration and authorization requirements.

## Troubleshooting

### Dialog artifact test reports missing coverage or inconsistent totals

Regenerate the inventory, then reconcile every report aggregate, table row, and verdict with
discovery. Do not exclude a dialog module from discovery.

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

# PYPOST-1387: Technical Debt Analysis

## Shortcuts Taken

- **`header:` prefix duplication** — Architecture allowed a one-way shared
  constant or a documented duplicate string. The implementation kept a local
  `_HEADER_RE` in `field_selector_syntax.py` while
  `JsonSelectorEngine` uses `_HEADER_PREFIX = "header:"` and the sanitizer
  uses `startswith("header:")`. No sync test locks the three sites together
  (architecture risk #1 / dependency note).
- **Wildcard normalization collapses `..`** — After `[*]` → `.*.`
  replacement, adjacent dots are collapsed and leading/trailing dots stripped
  so forms like `[*].id` validate. The same collapse also accepts drafts such
  as `users..email` as `ok=True` even though the stored cell text still
  contains `..`. UI can show “valid” while the literal selector is not the
  documented vocabulary form (false-green relative to NFR3 strictness).
- **Mostly generic invalid messages** — Non-header failures reuse a single
  `_UNSUPPORTED_MESSAGE` plus the shared `_SUGGESTIONS` block. Header-empty
  gets a specific reason; JSONPath / numeric index / filter cases do not get
  dialect-specific copy (FR3 is met via suggestions, not tailored diagnosis).
- **Live editor styling via inline stylesheet** — `FieldSelectorDelegate`
  applies `VALIDATION_LABEL_*` tokens through a per-keystroke
  `setStyleSheet(...)` string rather than a shared QSS / palette helper used
  elsewhere. Acceptable for advisory feedback; not ideal for theme churn.
- **Observability intentionally thin** — No logs in
  `validate_field_selector` or the delegate live path (avoids DEBUG flood).
  Diagnosis of invalid bulk loads relies on model DEBUG counts only
  (`50-observability.md`).

## Code Quality Issues

- **`_syntax_for` thin wrapper** — One-line alias around
  `validate_field_selector` in the model; harmless but adds an extra hop for
  readers.
- **`HiddenFieldRecord.enabled` / CheckStateRole** — Still present on the
  record and model roles while the table remains a single selector column.
  Pre-existing shape from PYPOST-1386; enable/disable UI is tracked separately
  (PYPOST-1530) and was correctly left out of this ticket.
- **Validator / engine drift surface** — UI vocabulary is intentionally
  stricter than permissive `JsonSelectorEngine._compile`. That split is by
  design, but without a shared fixture of “documented accepted / rejected”
  examples consumed by both unit tests and docs, NFR3 can drift when either
  side changes.
- **Odd surface forms after `[*]` rewrite** — Inputs like `a[*]b` normalize
  into identifier/`*` segments and validate `ok=True`. Unlikely user input,
  but the grammar is surface-form loose after rewrite rather than requiring
  explicit `.` / `[*]` boundaries in the original string.

## Missing Tests

- **No automated coverage for `FieldSelectorDelegate`** — Live `textChanged`
  editor highlight/tooltip and always-commit `setModelData` behavior are
  unwired in tests. Model/table role repros cover committed feedback (FR2/FR3
  after commit) but not as-you-type FR1 editor chrome.
- **No `header:` prefix sync assertion** between
  `field_selector_syntax`, `JsonSelectorEngine`, and
  `sensitive_text_sanitizer` (called out as optional in architecture).
- **Limited negative vocabulary matrix** — Unit suite covers the architecture
  mandatory examples (`$.…`, `users[0].…`, filter, empty `header:`) but not
  trailing/leading dots, empty segments, whitespace-in-token, or the
  false-green `..` collapse case above.
- **Timeout markers** — Focus suites declare module
  `pytestmark` (`timeout(10)` / `timeout(30)`). **No BLOCKER** for missing
  timeouts on PYPOST-1387 tests.

## Performance Concerns

- None material for this change. Validation is cached on
  `HiddenFieldRecord` and re-run on mutation / live editor keystrokes only
  (pure regex/string work). Architecture NFR1 target (~1k rows) is preserved
  by role caching; no new paint-path revalidation.

## Follow-up Tasks

1. Add a focused Qt test for `FieldSelectorDelegate` live invalid/valid
   editor feedback and advisory commit (FR1).
   - Jira: [PYPOST-1537](https://pypost.atlassian.net/browse/PYPOST-1537)
2. Add a sync test (or shared constant) for the `header:` prefix across
   validator, `JsonSelectorEngine`, and sanitizer.
   - Jira: [PYPOST-1538](https://pypost.atlassian.net/browse/PYPOST-1538)
3. Tighten path validation so literal `..` / malformed drafts are not
   accepted as `ok` after normalization side-effects; keep `[*]` surface
   forms valid without false-greening `users..email`.
   - Jira: [PYPOST-1539](https://pypost.atlassian.net/browse/PYPOST-1539)
4. Optionally specialize invalid messages for JSONPath `$`, numeric
   indexes, and filter predicates (still advisory).
   - Jira: [PYPOST-1540](https://pypost.atlassian.net/browse/PYPOST-1540)
5. Related product follow-ups already out of scope for this ticket:
   autocomplete / collection lint (PYPOST-1483), selector dedupe
   (PYPOST-1533), per-row enable checkboxes (PYPOST-1530).

### Pre-existing suite failures (Step 4 `make test`)

Observed at base commit `7b4d31be`. Verdict: **NON-BLOCKER — pre-existing**.
Step 3 repros for this task are green.

| Test / cluster | Verdict | Jira |
| --- | --- | --- |
| `tests/test_http_client.py` (blank path segment / TEMPLATE category) | NON-BLOCKER — pre-existing | [PYPOST-1534](https://pypost.atlassian.net/browse/PYPOST-1534) |
| `tests/test_mcp_server_impl.py` (`assertIs` RequestData identity) | NON-BLOCKER — pre-existing | [PYPOST-1535](https://pypost.atlassian.net/browse/PYPOST-1535) |
| `tests/test_async_manifest_discovery_repro.py::test_dialog_init_does_not_block_on_slow_manifest_discovery` | NON-BLOCKER — pre-existing | [PYPOST-1536](https://pypost.atlassian.net/browse/PYPOST-1536) |
| `tests/test_bundled_examples_packaging.py` + `tests/test_makefile_install_seed_contract.py` (undeclared `pypost.ui.{models,views,workers}`) | NON-BLOCKER — pre-existing | [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) |
| `tests/test_lockfile_verification.py` | NON-BLOCKER — pre-existing | [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397) |
| `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics` | NON-BLOCKER — pre-existing | [PYPOST-1492](https://pypost.atlassian.net/browse/PYPOST-1492) |
| `tests/test_pypost_1077_verification_votes.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` + `tests/test_pypost_1287_failing_repro.py` | NON-BLOCKER — pre-existing | [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475) |

Transient `tests/test_mypy_baseline_live.py` failure during implementation was
caused by this task (delegate override typing) and fixed before Step 4 handoff
— not filed as debt.

# PYPOST-423: Technical Review (STEP 6)

## Delivered scope

- **Parser and validation** (`pypost/models/retry.py`): `parse_retryable_status_codes` returns
  either a `list[int]` of codes in **100–599** or `RetryableCodesValidationFailure` with stable
  `reason` values (`empty_segment`, `invalid_token`, `out_of_range`). Comma-separated tokens;
  empty segments after strip fail validation; empty/whitespace-only raw input yields an empty
  list (valid).
- **Settings save path** (`pypost/ui/dialogs/settings_dialog.py`): `accept()` validates before
  `super().accept()`. On failure: structured WARNING log
  (`retryable_codes_settings_validation_failed` with `reason=` only), `QMessageBox.warning`,
  early `return` (dialog stays open, `new_settings` unchanged). On success: builds `RetryPolicy`
  with parsed list and proceeds as before.
- **Tests** (`tests/test_retryable_status_codes_parse.py`): Unit coverage for valid lists,
  whitespace, empty segments, invalid tokens, out-of-range, unsupported separators, and
  non-empty raw with only invalid tokens.
- **Observability (STEP 5)**: Logging on blocked save documented in `50-observability.md`.

Alignment with `10-requirements.md` FR-1–FR-5 and AC-1–AC-3, and with `20-architecture.md`
(save-time validation, `QMessageBox.warning`, no persistence on failure).

## Technical debt findings

- **No Qt dialog-level test** (`SettingsDialog.accept()`) — **Low.** Architecture allowed unit
  tests and manual QA without dialog harnesses. Parser holds core behavior; optional follow-up:
  offscreen `pytest-qt` if the project adopts it.
- **Return type** (`Union` vs Ok/Err in architecture doc) — **None.** Matches project style;
  `RetryableCodesValidationFailure` is a small frozen dataclass.
- **Duplicate codes** in user input — **Out of scope** per requirements; dedup deferred.

**Explicit statement:** No technical debt items are **release blockers** for PYPOST-423.

## Risk assessment

| Risk | Level | Mitigation in place |
| ---- | ----- | ------------------- |
| Regression in HTTP retry behavior | Low | `tests/test_retry.py` unchanged in intent; 49-test regression run passes. |
| User confusion on first invalid save | Low | Clear messages per failure kind; dialog remains open with prior settings. |
| Log noise in support | Low | Single WARNING per failed save attempt; no raw user text. |

Overall **low** risk for this change set.

## Test adequacy

- **Parser:** Strong — scenarios map to FR-1, AC-1, AC-2 (empty segments, bad tokens,
  separators, range), and empty/valid paths (FR-5 / AC-3).
- **Integration / UI:** **Partial by design** — no automated test asserts `QMessageBox` or dialog
  acceptance; acceptable per architecture. Manual QA checklist: invalid input blocks save and
  shows warning; valid list saves and persists.
- **Regression:** Command documented in `40-code-cleanup.md`; **49 passed** (verified in STEP 6
  review run).

## Follow-up recommendations

1. **Optional:** Add a focused UI or integration test for the settings dialog save path if the
   project standardizes on Qt test harnesses.
2. **Optional:** Product follow-up (separate story) for duplicate codes in the line edit if
   deduplication or warnings become desired.
3. **Process:** Update `00-roadmap.md` PM line after user gate — STEP 6 checkpoint recorded there.

## STEP 6 verdict

- **Ready for user review** of this document and for **STEP 7** (developer documentation) after
  process approval per `.cursor/rules/00-rules.mdc`.
- **No rejection** — no fixes required from Senior or Junior engineer before proceeding on the
  basis of technical debt alone.

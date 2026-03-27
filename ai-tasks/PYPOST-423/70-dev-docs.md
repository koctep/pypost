# PYPOST-423: Developer notes — retryable status codes validation

## Overview

This task replaces silent dropping of invalid retryable HTTP status code tokens with
explicit validation on settings save. Parsing and validation live in
`pypost.models.retry`; the settings UI blocks accept and shows a warning when input is
invalid.

## Developer-facing changes

### New API (`pypost.models.retry`)

- **`parse_retryable_status_codes(raw: str)`** — Returns either:
  - `list[int]` of validated codes, or
  - **`RetryableCodesValidationFailure`** with:
    - **`reason`**: one of `empty_segment`, `invalid_token`, `out_of_range` (stable for
      tests and logs).
    - **`message`**: user-facing guidance (shown in `QMessageBox`).
- **Rules:**
  - Comma-separated tokens; whitespace around commas is trimmed per segment.
  - **Empty or whitespace-only** raw string → **valid** empty list `[]`.
  - **Empty segment** after split (e.g. `500,`, `,500`, `500,,503`) → failure
    (`empty_segment`).
  - Each non-empty token must be **digits only** (`str.isdigit()`); otherwise
    `invalid_token`.
  - Parsed integer must be in **100–599** inclusive; otherwise `out_of_range`.

### Settings dialog (`pypost.ui.dialogs.settings_dialog`)

- **`SettingsDialog.accept()`** calls `parse_retryable_status_codes` on the retryable
  codes line edit **before** `super().accept()`.
- On **`RetryableCodesValidationFailure`**:
  - Emits a **WARNING** log (see Observability).
  - Shows **`QMessageBox.warning`** with title `"Invalid retryable status codes"` and
    body `parsed_codes.message`.
  - **Returns without** calling `super().accept()` — dialog stays open, `new_settings`
    is not set, **no persistence** for this save attempt.
- On success, builds `RetryPolicy` with the parsed list and proceeds as before.

### Files to know

| Area | File |
| ---- | ---- |
| Parse / validate | `pypost/models/retry.py` |
| Save guard + UI | `pypost/ui/dialogs/settings_dialog.py` |
| Unit tests | `tests/test_retryable_status_codes_parse.py` |

## Validation behavior and user feedback on save

1. User clicks **Save** in Settings.
2. Retryable field text is parsed; any failure shows a modal warning and **blocks** close.
3. Valid path: dialog accepts, `MainWindow` receives new settings and persists as before.
4. Invalid path: user corrects input and saves again; prior on-disk config is unchanged
   until a successful accept.

## Tests and verification commands

From the repository root (with `.venv` installed):

**Focused tests (retryable codes + related regression):**

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_retryable_status_codes_parse.py \
  tests/test_retry.py \
  tests/test_settings_persistence.py \
  tests/test_apply_settings_font.py \
  -q
```

**Full suite (optional):**

```bash
./scripts/test.sh
```

**Lint and line length** (changed modules):

```bash
./scripts/lint.sh pypost/models/retry.py pypost/ui/dialogs/settings_dialog.py \
  tests/test_retryable_status_codes_parse.py
./scripts/check-line-length.sh pypost/models/retry.py pypost/ui/dialogs/settings_dialog.py \
  tests/test_retryable_status_codes_parse.py
```

## Observability and troubleshooting

### What is logged

- On blocked save due to validation, **one WARNING** per attempt from
  `pypost.ui.dialogs.settings_dialog`:
  - Message includes prefix **`retryable_codes_settings_validation_failed`**
  - **`reason=`** is one of: `empty_segment`, `invalid_token`, `out_of_range`
- **Not logged:** raw line-edit text (reduces noise and avoids logging free-form user
  input).

### Distinguishing from HTTP retry logs

- Runtime HTTP retries use different log lines in `request_service` (e.g. `retryable_status`).
- Filter support cases on **`retryable_codes_settings_validation_failed`** for settings
  validation only.

### Troubleshooting

| Symptom | Check |
| ------- | ----- |
| Cannot close Settings on Save | Invalid field: one WARNING per attempt; modal shows guidance. |
| Many `invalid_token` | Wrong separator or non-digits; use commas only (e.g. `429,500`). |
| `empty_segment` | Trailing/duplicate commas or missing numbers between commas. |
| `out_of_range` | Values outside 100–599 (e.g. `99`, `600`). |

### References

- Architecture: `ai-tasks/PYPOST-423/20-architecture.md`
- Observability detail: `ai-tasks/PYPOST-423/50-observability.md`
- Technical debt / review: `ai-tasks/PYPOST-423/60-review.md`

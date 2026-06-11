# PYPOST-492: Group security/logging settings section in SettingsDialog

## Programming language

**Python** — PySide6 desktop UI. Follow `.cursor/lsr/do-python.md`.

## Problem statement

The `log_hidden_key_names` checkbox and alert webhook fields are security- and logging-related
settings scattered in the Settings dialog. The checkbox sits alone after general preferences,
while webhook fields appear at the bottom after retry policy rows. This hurts discoverability
for operators tuning logging redaction and alert delivery.

Source: follow-up from [PYPOST-448](https://pypost.atlassian.net/browse/PYPOST-448) tech debt.

## Goals

- Improve **discoverability** of security and logging preferences in Settings.
- Present related controls as a **cohesive group** without changing behavior or persistence.

## Scope

### In scope

- Add a visible **"Security / Logging"** section header in `SettingsDialog`.
- Move `log_hidden_key_names` checkbox to sit **with** alert webhook URL and auth header fields.
- Regression tests for layout grouping and existing save/load behavior.

### Out of scope

- Changing defaults, validation, or `AppSettings` schema.
- Retry policy layout, encryption section layout, or new settings fields.
- Observability logging for settings changes (unchanged).

## User stories

- As an **operator**, I want security and logging settings grouped together so I can find
  redaction and alert options without scanning the full dialog.
- As an **operator**, I want existing saved values to load unchanged after the layout update.

## Functional requirements

1. **FR-1 (Section header)** — Settings dialog shows a labeled "Security / Logging" section.
2. **FR-2 (Grouping)** — `log_hidden_key_names`, alert webhook URL, and alert webhook auth
   header appear contiguously under that section, in that order.
3. **FR-3 (Persistence)** — Save/load of all three fields unchanged; no schema changes.
4. **FR-4 (Regression)** — Existing tests for `log_hidden_key_names` continue to pass.

## Acceptance criteria

- AC-1: Section header text is exactly "Security / Logging".
- AC-2: Checkbox is no longer placed after "Confirm before overwriting requests".
- AC-3: Webhook fields immediately follow the checkbox within the section.
- AC-4: Automated tests assert section presence and field order.
- AC-5: Manual smoke: open Settings, verify grouping, save and reopen — values preserved.

## Risks

- Low: layout-only change; `accept()` logic unchanged.

# PYPOST-423: Retryable status codes input must not silently drop invalid values

## Context

- **Jira:** PYPOST-423
- **Origin:** Technical debt noted while closing PYPOST-402 (TD-6: validate retryable status
  codes input in settings).
- **Related (informational only):** PYPOST-402; this task is scoped independently.

## Problem statement

Users configure which HTTP status codes should be treated as retryable in application
settings. Today, parts of the input that are not recognized as valid status code entries for
this feature are **silently ignored**. The user receives no indication that something was
wrong.

That leads to a poor and risky experience: the user may believe the full list was saved
while the effective configuration is empty, incomplete, or different from what they typed
(for example when separators or formatting do not match what the product expects). Retry
behavior can then diverge from user expectations without any visible warning.

## Goals

- Ensure users **always know** when their retryable status codes input cannot be applied as
  entered.
- Prevent **silent loss** of intended configuration for this field.
- Align expectations between what the user types and what the application will use for
  retries.

## Scope

### In scope

- Validation and user-visible feedback for the **retryable HTTP status codes** field in the
  application settings flow (the same setting area addressed by PYPOST-402 TD-6).
- Behavior on **save** (or equivalent confirmation): invalid or ambiguous input must not be
  persisted without the user understanding the issue.

### Out of scope

- Other settings fields, unrelated dialogs, or other Jira work items.
- Changing the **meaning** of retry policy or retry logic beyond what is needed to reflect
  the user’s validated input.
- Architecture, libraries, or concrete UI control choices (handled in STEP 2+).

## User stories

- As a **user configuring retries**, I want to be **warned** when my status codes cannot be
  parsed so I do not unknowingly save a wrong or empty list.
- As a **user**, I want **clear guidance** on what input format is expected so I can fix
  mistakes before or when saving.
- As a **user**, I want **valid** input to continue to work as today, without extra friction.

## Main entities (business view)

| Entity | Role |
| ------ | ---- |
| **User** | Configures retry behavior via settings. |
| **Retry policy** | Parameters for retries, including which status codes are retryable. |
| **Settings persistence** | Saving approved configuration so it applies on next use. |

## Functional requirements

1. **FR-1 — Detect invalid input:** When the user confirms settings, the product must
   determine whether the retryable status codes field contains any token that is not a valid
   status code entry for this feature. That includes tokens that are not valid HTTP status
   codes under the product’s rules, not only non-numeric text. It also includes empty or
   misleading effective results caused solely by dropping bad tokens.
2. **FR-2 — No silent save:** If the input is invalid or would result in a misleading
   effective list compared to what the user typed, the product must **not** save that field’s
   new value until the user has seen clear feedback that the input was not accepted (for
   example an error or blocked save with explanation). The exact presentation is not fixed
   here.
3. **FR-3 — Actionable feedback:** The user must receive a **clear, readable** explanation
   that the input could not be accepted as entered, so they can correct it (without
   prescribing the exact wording or control in this document).
4. **FR-4 — Preserve stable state:** On failed validation, previously saved settings for this
   area must remain unchanged until the user provides acceptable input and saves
   successfully.
5. **FR-5 — Valid paths unchanged:** When the input is fully valid according to the rules
   above, behavior must match the product’s intended handling of retryable status codes (no
   regression for correctly formatted lists).

## Non-functional requirements

1. **NFR-1 — Clarity:** Error or guidance text must be understandable without insider
   knowledge of implementation details.
2. **NFR-2 — Consistency:** Feedback should feel consistent with how other settings in the
   same dialog surface validation problems (where applicable).
3. **NFR-3 — Responsiveness:** Validation runs in the save path and should not introduce a
   noticeable delay for typical input sizes.

## Acceptance criteria

1. Given text that contains **non-numeric or otherwise unacceptable** tokens in the
   retryable status codes field, when the user tries to save settings, then the product
   **shows feedback** and **does not** persist the new value for that field as if it were
   valid.
2. Given input that would previously yield an **empty** effective list while the visible
   text was **non-empty** (for example due to unsupported separators), when the user tries to
   save, then the user is **informed** and the invalid save is **blocked** as in AC-1.
3. Given a **valid** list of retryable codes in the supported format, when the user saves,
   then the configured codes are stored and used as intended (no regression).
4. Requirements and roadmap for PYPOST-423 remain free of **implementation** prescriptions;
   language choice is recorded below only as mandated by process.

## Risks and assumptions

| Type | Description |
| ---- | ----------- |
| **Assumption** | Delimiter rules are documented or implied; UX may clarify in STEP 2+. |
| **Assumption** | Other settings may validate input; align behavior where practical. |
| **Assumption** | Repeated valid codes: unchanged unless tied to silent loss; dedup out of scope. |
| **Risk** | Low: few users rely on silent truncation; explicit validation is preferable. |

## Programming language

**Python.** This task applies to the existing PyPost desktop UI; implementation is expected in
the `pypost` Python package, following project Python guidelines in `.cursor/lsr/do-python.md`
from architecture onward.

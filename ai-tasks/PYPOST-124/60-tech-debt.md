# PYPOST-124: Technical Debt Analysis

## Shortcuts Taken

- **Fixed colors** ([PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395)): `darkorange`
  is hardcoded like other `JsonHighlighter` colors; dark-theme migration remains deferred.
- **Regex scope** ([PYPOST-113](https://pypost.atlassian.net/browse/PYPOST-113)): Placeholder
  scan is line-local and may false-positive inside string literals that happen to contain
  `{{...}}` text — same contract as hover/tokenizer.

## Code Quality Issues

- None blocking. Key highlighting logic simplified; behavior preserved.

## Missing Tests

- No visual/regression screenshot test for response viewer (acceptable; unit tests cover
  `QTextDocument` formatting).
- Placeholders spanning multiple lines (split across `\n` inside `{{`) are not matched —
  invalid for normal `{{...}}` usage.

## Performance Concerns

- One additional `TEMPLATE_PLACEHOLDER_PATTERN.finditer` per block — negligible for typical
  request/response sizes. Large-body optimization tracked under PYPOST-120.

## Deviations from Architecture

- None. Implementation matches `20-architecture.md`.

## Follow-up Tasks

No new follow-up Jira issues required. Source item from PYPOST-13 `40-tech-debt.md` is
resolved by this task.

## Blocker Review Verdict

**SAFE TO CLOSE** — acceptance criteria met; tests pass; no unsafe incomplete work.

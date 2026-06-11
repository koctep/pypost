# PYPOST-460: Technical Debt Analysis

## Shortcuts Taken

- None. Shared tokenizer replaces duplicate regex without behavior change.

## Code Quality Issues

- `VariableHoverHelper` in `pypost/ui/widgets/mixins.py` still uses a separate
  `EXPRESSION_PATTERN` for hover preview; not unified with core tokenizer (different
  use case: full token with braces for tooltip display).

## Missing Tests

- No dedicated test that `render_string` performs a single tokenization call (would require
  mocking); parity covered by existing integration and observability tests.

## Performance Concerns

- Standalone `validate_content(string)` still tokenizes once per call — acceptable for API
  callers outside the render path.
- UI hover path still uses its own regex iterator; low volume.

## Follow-up Tasks

- [PYPOST-536](https://pypost.atlassian.net/browse/PYPOST-536): Unify or document relationship
  between UI `EXPRESSION_PATTERN` and core tokenizer if hover semantics should match validation
  exactly.
- [PYPOST-461](https://pypost.atlassian.net/browse/PYPOST-461): Expand resolver test matrix
  for malformed nested expressions and empty-argument edge cases (pre-existing follow-up).

## Blocker review (Phase C)

**Verdict: SAFE TO CLOSE**

- Acceptance criteria met: shared utility, single render-path scan, tests green, observability
  parity preserved.
- No blockers identified.

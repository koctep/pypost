# PYPOST-437: Technical Debt Analysis

## Shortcuts Taken

- Hidden state is modeled as `hidden_keys` (set of variable names) rather than
  per-variable objects. This keeps compatibility and minimizes blast radius, but couples
  hidden state to key names.
- Masking remains a UI/display-level safeguard only; values are still stored in plain text
  in `environments.json` by design (out of scope from requirements).

## Code Quality Issues

- `EnvironmentDialog` logic was partially refactored by extracting value-item helpers
  (`_make_value_item`, `_extract_real_value`). Remaining complexity is in row-level flow
  (`on_var_changed`, hidden-toggle path) and can be further decomposed if needed.
- Hidden-toggle logging currently records variable key names. This is acceptable for
  observability, but organizations with strict logging policies may want this to be
  configurable.

## Missing Tests

- No critical missing tests identified for PYPOST-437 scope.

## Performance Concerns

- No significant performance impact expected. Membership checks in `hidden_keys` are O(1).
- Additional storage logs are low-frequency and tied to environment operations.

## Follow-up Tasks

- [PYPOST-449, Low] Further decompose `EnvironmentDialog` row-update/rebuild helpers.
- [PYPOST-448, Medium] Make hidden-key name logging configurable.
- [PYPOST-446, High] Define and implement masking policy for hidden-derived values in
  History view/logs.
- [PYPOST-447, Medium] Optional encrypted-at-rest storage for sensitive environment values.

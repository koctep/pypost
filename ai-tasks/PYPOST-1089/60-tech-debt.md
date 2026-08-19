# PYPOST-1089: Technical Debt Analysis

## Shortcuts Taken

1. **`number`-type int/float disambiguation is a substring check, not real numeric
   parsing.** `_coerce_default_number()` in `pypost/ui/widgets/request_editor.py`
   decides `int(raw)` vs `float(raw)` by checking `"." not in raw`. Verified by direct
   probe: scientific-notation floats that have no literal dot (e.g. `1e-10`, `5e+20`)
   fail `int("1e-10")`, the `ValueError` is swallowed by `_parse_default()`'s generic
   fallback, and the default is silently dropped (`default=None`) with only a DEBUG
   log — no error is surfaced to the user. Normal-range floats (`3.14`, `1234567890123.0`,
   `0.0001`) round-trip correctly; only the scientific-notation edge case is affected.
2. **`_coerce_default_boolean()` never raises**, unlike the other six coercers in
   `_COERCERS`. `raw.lower() in ("true", "1")` maps *any* unrecognized text (typos,
   `"yes"`, `"maybe"`, stray whitespace-only-after-strip content) to an explicit `False`
   rather than falling back to `None` the way `integer`/`array`/`object`/etc. do on bad
   input. This is a real behavioral inconsistency inside a dispatch dict whose other six
   entries share a "raise on bad input, caller catches" contract — verified by direct
   probe (`_coerce_default_boolean("maybe")` → `False`).
3. **Default column is a plain-text cell for every param type**, including `boolean`
   (no checkbox, unlike the Required column which does use a real checkbox item) and
   `array`/`object` (no JSON validation or multi-line editor for a single-line table
   cell). This was a deliberate, documented trade-off in `20-architecture.md`'s Q&A
   ("Cell stores the default as a human-readable string"), not an oversight — but it is
   still a UX shortcut worth tracking as debt rather than a closed decision, since a
   type-aware editor (checkbox for booleans at minimum) is a natural follow-up.
4. **Changing the Type combo does not touch the Default cell.** `_on_param_type_changed()`
   (request_editor.py) only re-emits `itemChanged` for the Description column; it never
   clears, re-validates, or visually flags the Default cell for the row. A user can
   switch a param's Type from `string` to `integer` while the Default cell still holds
   `"hello"`; nothing warns them, and the stale text silently becomes `default=None` the
   next time `get_data()` runs — the only trace is an invisible DEBUG log.

## Code Quality Issues

1. `_coerce_default_boolean`'s "never fails" contract vs. the other six `_COERCERS`
   entries' "raise on bad input" contract is easy to miss in review since they're called
   identically from `_parse_default()`. Worth either documenting the asymmetry inline or
   normalizing it (see Follow-up Tasks).
2. `McpToolParam` has no `model_config = ConfigDict(validate_assignment=True)`, so
   `_validate_default_type()` (called from `model_post_init`) only runs at construction
   time. A future code path that does `spec.default = something` post-construction
   (grepped the codebase — no such mutation site exists today) would silently bypass
   validation. Latent risk, not an active bug; flagging so it isn't rediscovered the hard
   way later.
3. The type-to-Python-type mapping is expressed twice, by hand, in two different files:
   the validation whitelist (`McpToolParam._validate_default_type()` in `models.py`) and
   the coercion dispatch (`McpParamsTable._COERCERS` in `request_editor.py`). Both are
   correct and in sync today, but nothing enforces that they stay in sync if a new MCP
   param type is ever added — a contributor could add a type to `_MCP_PARAM_TYPES` and
   `_validate_default_type()` while forgetting to add a matching `_COERCERS` entry (or
   vice versa), and the only symptom would be silent `default=None` drops in the UI with
   no test failure pointing at the cause.

## Missing Tests

1. No test exercises a `type="number"` default round-trip through `McpParamsTable`
   (`set_data()` → `get_data()`) verifying an `int` default (e.g. `5`) stays `int` and a
   `float` default (e.g. `3.14`) stays `float`. This gap was explicitly flagged during
   the Step 4 review round and left open — `test_round_trip_preserves_default` in
   `tests/test_request_editor_mcp_params.py` only covers `integer_or_string`.
2. No test covers scientific-notation numeric strings for `type="number"` (Shortcuts
   #1) — currently silently drops the default with no assertion anywhere confirming
   (or guarding against) that behavior.
3. No test exercises the *table-level* fallback-to-`None` path end to end, i.e. no test
   asserts that an unparsable Default cell (e.g. `"abc"` typed against `type="integer"`)
   produces `default=None` in the `McpToolParam` returned by `get_data()` without
   raising. The two new model-level tests (`test_boolean_default_string_raises`,
   `test_integer_default_float_raises`) only exercise direct `McpToolParam(...)`
   construction, not the UI coercion path that is supposed to prevent that error from
   ever reaching the model in practice.
4. No test covers `_coerce_default_boolean`'s silent-`False`-on-garbage-input behavior
   (Shortcuts #2) — currently unverified and undocumented in the test suite.
5. No test asserts that `_validate_default_type()` rejects a `bool` default for
   `type="integer"`, `"number"`, or `"integer_or_string"` (Python's `bool` is an `int`
   subclass, so this exclusion is easy to regress silently). Verified by direct probe
   that the current code correctly raises `ValidationError` for
   `McpToolParam(type="integer", default=True)`, but no test pins that behavior down.
6. Table round-trip tests (`TestMcpParamsTable`) cover `array`/`object` and
   `integer_or_string`; there is no equivalent round-trip test for `string` or
   `boolean` defaults specifically going through `set_data()`/`get_data()`.

## Performance Concerns

None identified. Row counts in `McpParamsTable` are UI-scale (a handful to a few dozen
params per request); `_validate_default_type()` is O(1) per field; JSON
encode/decode in `_serialise_default`/`_coerce_default_array`/`_coerce_default_object`
operates on small per-cell values. No hot path is affected by this change.

## Deviations from Architecture

None of substance. `20-architecture.md`'s "Main Interfaces and APIs" section specifies
`model_post_init` calling `_validate_default_type()`, and the coercion contract table
matches `_COERCERS` 1:1 — both match the shipped code exactly. One documentation-only
note: the roadmap's Step 4 entry and this Jira ticket's summary refer to the validator
loosely as a "model_validator"; the shipped implementation is a `model_post_init` hook
(matching the codebase's existing `Settings` convention per `50-observability.md`), not
a `@model_validator`-decorated method. This is terminology drift in prose, not a code
deviation — flagged only so a future reader doesn't go looking for a decorator that
doesn't exist.

## Follow-up Tasks

1. **NON-BLOCKER — enhancement.** Fix `_coerce_default_number()`'s int/float
   disambiguation to handle scientific notation correctly (e.g. try `int(raw)` first
   inside a `try`, fall back to `float(raw)`, instead of gating on substring `"."`
   presence) so defaults like `1e-10` or `5e+20` round-trip instead of silently
   vanishing. `pypost/ui/widgets/request_editor.py::_coerce_default_number`.
   Jira: [PYPOST-1095](https://pypost.atlassian.net/browse/PYPOST-1095)
2. **NON-BLOCKER — enhancement.** Make `_coerce_default_boolean()` reject unrecognized
   text (raise `ValueError` for anything other than an accepted true/false spelling)
   instead of silently defaulting to `False`, bringing it in line with the other six
   `_COERCERS` entries' fail-and-fall-back-to-`None` contract.
   `pypost/ui/widgets/request_editor.py::_coerce_default_boolean`.
   Jira: [PYPOST-1096](https://pypost.atlassian.net/browse/PYPOST-1096)
3. **NON-BLOCKER — enhancement.** Add the missing test coverage enumerated above,
   at minimum: (a) `number`-type int/float round-trip through `McpParamsTable`, (b) a
   table-level test that an unparsable Default cell yields `default=None` from
   `get_data()`, (c) a `bool`-excluded-from-`integer`/`number`/`integer_or_string`
   regression test in `tests/test_mcp_tool_contract.py`.
   Jira: [PYPOST-1097](https://pypost.atlassian.net/browse/PYPOST-1097)
4. **NON-BLOCKER — enhancement.** Consider a type-aware Default cell editor (at
   minimum a checkbox for `boolean`, matching the existing Required column's checkbox
   pattern) and clearing/flagging the Default cell when the Type combo changes
   (`_on_param_type_changed()`), so a stale Default value doesn't silently disappear
   with no visible feedback. UX-only; no data-model change required.
   Jira: [PYPOST-1099](https://pypost.atlassian.net/browse/PYPOST-1099)
5. **NON-BLOCKER — enhancement.** Extend type validation to actual MCP tool-call
   arguments received at runtime (`pypost/core/mcp_server_impl.py::_build_execution_variables`,
   where `merged_args` is built from client-supplied `mcp_args` merged with
   `param_spec.default`). Today only the *default* value is type-checked
   (`McpToolParam._validate_default_type()`); a client can still pass an
   argument of the wrong type for a declared param and it flows through unchecked.
   Out of scope for PYPOST-1089 (which is default-only per its Definition of Done), but
   a natural larger follow-up now that the type-checking logic exists as a reference.
   Jira: [PYPOST-1100](https://pypost.atlassian.net/browse/PYPOST-1100)
6. **NON-BLOCKER — documentation.** Note in dev docs (Step 8) that the validator is a
   `model_post_init` hook, not a `@model_validator` decorator, to avoid the terminology
   drift described above propagating further.
   Jira: [PYPOST-1098](https://pypost.atlassian.net/browse/PYPOST-1098)

No pre-existing test failures were found during this run — the full 22-test suite
(`tests/test_mcp_tool_contract.py`, `tests/test_request_editor_mcp_params.py`) and
`make lint` (flake8 on `pypost/`, markdown lint, relative link check) were both
re-confirmed clean at the end of this step with no code changes.

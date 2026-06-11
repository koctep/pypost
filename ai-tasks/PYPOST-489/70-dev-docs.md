# PYPOST-489 — Developer Documentation

## Summary

Test-only task. No `doc/dev/` updates required.

Existing documentation in `doc/dev/hidden_variables.md` (PYPOST-448 STEP 7) already describes
default masked toggle logging and the `log_hidden_key_names` setting.

## Test location

`tests/test_env_persistence_e2e.py::test_default_masked_toggle_log_after_persistence_round_trip`

Covers persistence round-trip with default `EnvironmentDialog` constructor — complementary to
`tests/test_settings_hidden_toggle_logging_e2e.py` (PYPOST-490 settings chain).

## Related

- [PYPOST-448](https://pypost.atlassian.net/browse/PYPOST-448) — configurable hidden-key logging
- [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490) — settings integration test

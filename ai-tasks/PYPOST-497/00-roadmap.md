# Roadmap: PYPOST-497

## Step Status

- [x] STEP 1–7 complete

## Summary

Domain validation moved to `pypost/core/environment_ops.py`:

- `validate_environment_rename` — environment name rules (used by delegate)
- `validate_environment_variable_name` — variable key rules (used by table sync)

`EnvironmentDialog` delegates to core helpers; inline rename uses `EnvironmentNameDelegate`.

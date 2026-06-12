# PYPOST-54: Dev Docs

## Updated

- `doc/dev/environments_dialog.md` — copy-on-edit contract, presenter apply flow, `environments`
  property.

## Key points for developers

1. Pass presenter environments into `EnvironmentDialog`; do not expect in-place mutation.
2. After `exec()`, read `dialog.environments` and assign to presenter state before save.
3. `clone_environments()` in `environment_ops` is the supported deep-copy helper.

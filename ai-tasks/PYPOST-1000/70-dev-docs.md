# PYPOST-1000: Dev Docs

## Updates

- `doc/dev/environments_dialog.md` — Import environments Tests paragraph:
  documented PYPOST-1000 presenter wiring lock
  (`test_open_env_manager_passes_working_read_import_file`) alongside
  existing pure/widget/Overwrite coverage notes.

## Overview of documented behavior

No new runtime feature; documentation records how CI proves
`EnvPresenter._open_env_manager` injects a storage-backed `read_import_file`
into `EnvironmentDialog`.

# PYPOST-827: Dev Docs Update

## Changes

Updated developer docs for the shared hang-resistant nested `QEventLoop` wait:

- `doc/dev/gui_testing.md` — § Bounded nested `QEventLoop` waits now points at
  `tests.helpers.process_until.process_until`, lists responsiveness + three sibling
  consumers, and drops the “porting tracked as PYPOST-827” note (done). Hang-regression
  test names kept.
- `doc/dev/testing.md` — nested-`exec()` guidance references the shared helper instead of
  local `_process_until`.
- `doc/dev/environment_storage_async.md` — PYPOST-823 section notes the shared helper and
  PYPOST-827 sibling port.

## Validation

- [x] Docs name `tests.helpers.process_until.process_until` as the shared wait
- [x] Three siblings + responsiveness listed as consumers
- [x] PYPOST-827 porting note removed / marked done
- [x] Hang-regression test names retained in `gui_testing.md`

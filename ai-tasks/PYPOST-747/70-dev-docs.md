# PYPOST-747 — Developer Documentation

> Parent: [PYPOST-747](https://pypost.atlassian.net/browse/PYPOST-747)

## What Changed

Created canonical logging convention reference at `doc/dev/logging.md`.

## Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/logging.md` | **New** — convention, domain catalog, legacy migration |
| `doc/dev/observability_audit.md` | Link to `logging.md`; trim duplicate naming section |
| `doc/dev/README.md` | TOC entry for logging convention |

## For Maintainers

When adding or renaming log events, update the relevant domain table in `logging.md` and follow
the migration checklist if replacing legacy strings.

# PYPOST-443: Developer documentation (STEP 7)

## Created / updated

| File | Action |
| ---- | ------ |
| `doc/dev/metric_rename_migration.md` | **Created** — operator migration guide |
| `doc/dev/README.md` | **Updated** — table of contents link |

## Content summary

`metric_rename_migration.md` covers:

- Overview of PYPOST-422 rename and PYPOST-443 transitional alias
- Architecture diagram (single tracker, dual export)
- Rollout checklist: discover → plan → deploy/verify → communicate
- PromQL before/after examples
- Sunset timeline and troubleshooting table
- Test commands

## Cross-references

- Implementation: `pypost/core/metrics.py`
- Prior task: `ai-tasks/PYPOST-422/70-dev-docs.md`
- Observability detail: `ai-tasks/PYPOST-443/50-observability.md`

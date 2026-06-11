# PYPOST-376: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/solid_audit.md` | Added **Regression baseline metrics** section |
| `doc/dev/testing.md` | Added **SOLID audit baseline (PYPOST-376)** section |

## Key Points for Maintainers

- Baseline snapshot: `ai-tasks/PYPOST-376/baseline-metrics.md`
- Caps defined in `scripts/audit_baseline_metrics.py` (`FILE_CAPS`, `MAIN_WINDOW_CLASS_CAP`)
- CI guard: `tests/test_solid_audit_baseline.py`

## Regenerate Snapshot

```bash
.venv/bin/python scripts/audit_baseline_metrics.py \
  --markdown ai-tasks/PYPOST-376/baseline-metrics.md
```

## Verify Caps

```bash
.venv/bin/python scripts/audit_baseline_metrics.py --check
pytest tests/test_solid_audit_baseline.py -v
```

## Updating Caps After Intentional Growth

1. Remeasure with the script (stdout or `--json`).
2. Set new cap ≈ measured value + 10% headroom.
3. Update constants in `scripts/audit_baseline_metrics.py`.
4. Regenerate `baseline-metrics.md` and note the change in the task or PR description.

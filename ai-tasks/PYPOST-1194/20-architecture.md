# PYPOST-1194: Raise SOLID FILE_CAPS for collections_presenter and tabs_presenter LOC drift

## Research

### R-1 Confirmed failure mode

`tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_audit_module_inventory_within_caps`
fails because `scripts/audit_baseline_metrics.py` `FILE_CAPS` lag measured LOC:

| Module | Measured LOC | Current cap |
| --- | ---: | ---: |
| `pypost/ui/presenters/collections_presenter.py` | 486 | 403 |
| `pypost/ui/presenters/tabs_presenter.py` | 1059 | 785 |

Pre-existing at base `18a4d9d1` (PYPOST-1192 triage). Policy and maintenance
live in `doc/dev/solid_audit.md`: prefer extraction before raising; if growth is
intentional, document rationale, retain ~10% headroom, regenerate snapshot.

### R-2 Headroom policy (prior art)

Same pattern as PYPOST-735 / PYPOST-1071 / PYPOST-717:

`new_cap = ceil(measured * 1.10)`

| Module | Measured | New cap (~10%) |
| --- | ---: | ---: |
| `collections_presenter.py` | 486 | **535** |
| `tabs_presenter.py` | 1059 | **1165** |

### R-3 Extraction vs raise

`doc/dev/websocket_draft_tab.md` still documents tabs_presenter at **785** and
pushes draft/close logic into helpers — that guidance remains valid for *future*
growth. Current 1059 LOC already includes prior feature work; a full extraction
in this Low/SP-3 debt ticket is out of scope. Ticket default: **raise caps** for
intentional growth. Follow-up debt may continue splitting tabs_presenter if
maintainers want the 785 target restored.

### R-4 Modules involved (unchanged runtime shape)

| Module | Responsibility |
| --- | --- |
| `scripts/audit_baseline_metrics.py` | `FILE_CAPS`, measurement, `--check` |
| `ai-tasks/PYPOST-376/baseline-metrics.md` | Generated snapshot |
| `tests/test_solid_audit_baseline.py` | Pytest inventory / freshness guards |
| `doc/dev/solid_audit.md` | Maintainer procedure + closure notes |
| Presenter sources | Measured only — no behavioral edit |

## Implementation Plan

1. Update `FILE_CAPS` entries for the two presenters to 535 and 1165 with
   PYPOST-1194 rationale comments (measured + ~10% headroom).
2. Regenerate `ai-tasks/PYPOST-376/baseline-metrics.md` via the generator
   (`--markdown`).
3. Add a short PYPOST-1194 note to `doc/dev/solid_audit.md`; align any
   stale 785 LOC claims in related docs only where they describe current
   caps (keep extraction guidance as aspirational where appropriate).
4. Confirm green:
   `make test PYTEST_ARGS="tests/test_solid_audit_baseline.py"`.

**Mandatory — Failing Repro (next Step 3):** The named inventory test already
exists and fails red today on stale caps. Step 3 **confirms** it fails under
`make test PYTEST_ARGS="tests/test_solid_audit_baseline.py"` for the intended
LOC-vs-cap messages (no new test file; no production fix in Step 3). Desired
behavior after Step 4: inventory within caps (empty violation list).

## Architecture

```text
FILE_CAPS (audit_baseline_metrics.py)
        │
        ├─ measure LOC of monitored paths
        ├─ check_caps / --check
        └─ regenerate baseline-metrics.md
                │
                └─ test_solid_audit_baseline.py
                     (inventory within caps + snapshot freshness)
```

No new modules, no presenter API changes, no observability changes. Cap
enforcement mechanism unchanged; only declared limits and snapshot refresh.

## Q&A

| Question | Answer |
| --- | --- |
| New red test? | No — confirm existing inventory test is red. |
| Touch presenter logic? | No. |
| Headroom formula? | `ceil(LOC * 1.10)` → 535 / 1165. |

# PYPOST-699: Resolve empty utils/ package

## Research

- `pypost/utils/__init__.py` is empty (0 bytes).
- Grep across the repo shows no `from pypost.utils` or `import pypost.utils` usage.
- Audit remediation option: "Remove from docs or add shared helpers when needed."
- Shared helpers already live next to their consumers (e.g. `pypost/ui/widgets/fold/scan_utils.py`).

## Implementation Plan

1. Delete `pypost/utils/` directory.
2. Update `doc/dev/architecture.md` tree — remove `utils/` entry; reattach `fixtures/` as
   the last top-level package.
3. Update `doc/dev/architecture_audit.md`:
   - L-006 → **Remediated** (PYPOST-699)
   - R-P3-001 → **Done** (PYPOST-699)
4. Run `make check`.

## Architecture

No new modules. Package boundary map loses the unused utilities layer:

```text
pypost/
├── main.py, version.py
├── core/
├── models/
├── ui/
└── fixtures/   # test helpers only
```

Future shared helpers should be colocated with their domain (`core/`, `ui/`) or introduced
only when a second consumer appears.

## Q&A

- **Q:** Why not keep `utils/` for future helpers?
- **A:** An empty package adds no value and was flagged as documentation drift; YAGNI applies
  until a concrete helper is needed.

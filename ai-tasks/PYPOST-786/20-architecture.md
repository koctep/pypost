# PYPOST-786: Licensing documentation architecture

## Research

- **PyPost license:** MIT (`LICENSE` at repository root).
- **PySide6 license:** LGPL-3.0 (Qt for Python wheels bundle Qt libraries as shared objects).
- **Audit finding L-002:** Obligations matter when shipping standalone binaries or app bundles;
  low impact for source-only or `pip install` workflows where users obtain PySide6 themselves.
- **Existing references:** `doc/dev/dependencies_audit.md` § License Notes; PYPOST-691
  architecture license baseline table.

## Document Structure

Create `doc/dev/licensing.md` with:

1. **Overview** — MIT project + LGPL GUI dependency; scope of the guide.
2. **When obligations apply** — Table contrasting development, pip install, and binary
   redistribution scenarios.
3. **How PySide6 is linked** — Dynamic linking via PyPI wheels; no static Qt linking in
   PyPost source.
4. **Distributor checklist** — Notices, LGPL text, corresponding source, object-code offer,
   modification and relinking rights.
5. **PyPost-specific notes** — What the project ships today (source + MIT `LICENSE` only).
6. **References** — Official Qt/PySide6 and LGPL-3.0 links.

## Cross-links

| File | Change |
| --- | --- |
| `doc/dev/dependencies_audit.md` | Link R-P3-002 to `licensing.md`; mark recommendation Done |
| `doc/dev/README.md` | Add entry under Audits or new Licensing section |

No new tests — documentation-only deliverable; `make check` validates existing suite unchanged.

## Q&A

- **Why a standalone `licensing.md` instead of expanding `dependencies_audit.md`?** The audit
  doc is an inventory; distributor obligations deserve a focused, linkable guide maintainers
  can update independently of audit refresh cycles.

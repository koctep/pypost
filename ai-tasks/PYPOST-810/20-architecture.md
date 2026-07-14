# PYPOST-810: Legal review gate architecture

## Research

- **PYPOST-786:** `doc/dev/licensing.md` covers LGPL obligations and a distributor checklist.
- **PYPOST-809:** `LICENSES/transitive.csv` and `make check-license-inventory` supply
  transitive attribution evidence for gate item G5.
- **Current shipping model:** Source-only; no official frozen binaries or installers.
- **Follow-up origin:** PYPOST-786 `60-tech-debt.md` — counsel should review distributor
  checklist against target platforms before first binary artifact.

## Document Structure

Extend `doc/dev/licensing.md` with two sections after the distributor checklist:

### 1. Pre-binary-release legal review gate

| Element | Purpose |
| --- | --- |
| Gate table G1–G8 | Numbered release blockers with owner and evidence columns |
| Maintainer workflow | Ordered steps from lock freeze through sign-off |
| Scope boundary | Clarifies what the gate does not cover (SBOM formats, signing policy) |

Gate items map to existing artifacts:

- G2–G4 → distributor checklist (LGPL notices, source offer, replacement)
- G5 → PYPOST-809 inventory workflow
- G6 → existing § Version pinning
- G7 → new platform-specific table
- G1, G8 → process / counsel items

### 2. Platform-specific distribution notes

Three subsections (macOS, Windows, Linux) plus a cross-platform verification checklist:

| Platform | Focus |
| --- | --- |
| macOS | `.app`/`.dmg`, `@rpath` replacement, Qt plugins, codesign/notarization pointer |
| Windows | `.dll` layout, MSVC runtime, MSI vs portable, plugin discovery |
| Linux | `.so` / `RPATH`, Flatpak conveyance, distro packages vs frozen tarball |

## Cross-links

| File | Change |
| --- | --- |
| `doc/dev/licensing.md` | New gate and platform sections; troubleshooting rows; title cites PYPOST-810 |
| `doc/dev/dependencies_audit.md` | License Notes link to gate anchor |

No new tests — documentation-only; `make check` validates existing suite unchanged.

## Q&A

- **Why a table gate instead of prose only?** Release engineers need auditable evidence
  columns; mirrors CI gate patterns elsewhere in the repo.
- **Why separate platform section?** LGPL obligations are similar but packaging paths differ
  per OS; counsel review (G7) is per-platform.

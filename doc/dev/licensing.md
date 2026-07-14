# Licensing and Distribution (PYPOST-786, PYPOST-810)

## Overview

PyPost is released under the **MIT License** ([`LICENSE`](../LICENSE) at the repository root).
The desktop GUI depends on **PySide6** (Qt for Python), which is licensed under **GNU
LGPL-3.0**.

Most other Python dependencies are permissive (MIT, Apache-2.0, BSD). PySide6 is the main
license consideration when **redistributing PyPost together with Qt libraries** — for
example as a frozen binary, OS installer, or app bundle.

This guide summarizes LGPL-3.0 distribution obligations for maintainers and distributors.
It is **not legal advice**. Consult qualified counsel before commercial redistribution.

**Related:** [Dependencies and Supply Chain Audit](dependencies_audit.md) (PYPOST-691),
finding L-002 / recommendation R-P3-002.

## When LGPL obligations apply

| Scenario | Typical LGPL impact |
| --- | --- |
| Clone repo and run from source (`python -m pypost`) | Low — you obtain PySide6 via pip; Qt libraries stay separate shared objects |
| End user runs `pip install` / `make install` on their machine | Low — user installs PySide6 from PyPI; no PyPost-branded binary bundle |
| CI runs tests with PySide6 wheels | Low — internal/development use |
| Ship a **standalone executable** (PyInstaller, cx_Freeze, etc.) bundling Qt | **High** — you convey a combined work; LGPL compliance steps required |
| Ship an **installer or app bundle** (.dmg, .msi, Flatpak) including Qt `.so`/`.dylib`/`.dll` | **High** — same as above |
| Modify PySide6/Qt and redistribute those libraries | **High** — must convey corresponding source for your modifications |

**Rule of thumb:** If your distribution **includes Qt shared libraries** (not merely Python
source that tells users to `pip install PySide6`), treat LGPL-3.0 obligations as applicable.

## How PySide6 is used in PyPost

- PyPost imports PySide6 at runtime; it does **not** statically link Qt into application
  object code.
- Official PySide6 wheels from PyPI ship Qt as **dynamic libraries** loaded at runtime.
- Application code under `pypost/` is MIT-licensed; PySide6 remains a **separate library**
  dependency.

Dynamic linking is the expected integration path and is compatible with LGPL-3.0 when
distributor obligations below are met.

## Distributor checklist (LGPL-3.0)

When you redistribute PyPost **with** PySide6/Qt libraries, plan to:

1. **License and copyright notices**
   - Include the full **LGPL-3.0** license text for Qt/PySide6.
   - Preserve Qt and PySide6 **copyright notices** shipped with the libraries.
   - Include PyPost's **MIT** `LICENSE` for application source (separate from LGPL).

2. **Inform recipients the library is LGPL**
   - Document that PySide6/Qt components are under LGPL-3.0 and where to find license files
     in your package (e.g. `LICENSES/` or `ThirdPartyNotices.txt`).

3. **Corresponding source and object-code offer (Section 6)**
   - For each LGPL library you convey, provide **corresponding source** (or a written offer
     valid for at least three years to obtain it).
   - For user-installed replacements: design the package so users can **substitute a modified
     PySide6/Qt** build (relinking) where technically feasible — avoid designs that prevent
     replacing bundled Qt `.so`/`.dylib`/`.dll` files.

4. **Application license separation**
   - PyPost MIT source does **not** need to be relicensed under LGPL when dynamically linking
     to PySide6.
   - If you **modify** PySide6 or Qt libraries themselves, those modifications must be
     available under LGPL terms.

5. **Attribution for other dependencies**
   - PySide6 is not the only third-party component in a full environment. A complete release
     should include notices for MIT/Apache/BSD deps. The committed transitive inventory lives
     in [`LICENSES/transitive.csv`](../../LICENSES/transitive.csv) (PYPOST-809); regenerate
     with `make generate-license-inventory` after production lock changes.

## Pre-binary-release legal review gate (PYPOST-810)

PyPost has **not** published official frozen binaries or installers yet. Before the **first**
binary artifact is released under the PyPost project name, complete this gate. Treat unchecked
items as **release blockers** until resolved or explicitly waived in writing by qualified
counsel.

This gate supplements — it does not replace — the [Distributor checklist](#distributor-checklist-lgpl-30)
above and the [platform notes](#platform-specific-distribution-notes) below.

### Release readiness checklist

| # | Gate item | Owner | Evidence |
| --- | --- | --- | --- |
| G1 | **Counsel review** — qualified legal counsel reviews this guide, the distributor checklist, and the planned artifact layout for each target platform | Legal / maintainer | Written sign-off (email, memo, or ticket comment) referencing PySide6/Qt versions |
| G2 | **LGPL packaging plan** — notices, LGPL-3.0 text, and PyPost MIT `LICENSE` are included in the shipped bundle (e.g. `LICENSES/`, `ThirdPartyNotices.txt`, or in-app About) | Release engineer | File manifest or installer spec |
| G3 | **Corresponding source offer** — written offer or bundled source pointers for LGPL libraries (PySide6/Qt) valid for ≥3 years per LGPL §6 | Release engineer | Offer text in package + URL or archive location |
| G4 | **Re-linking / replacement** — bundle layout allows substituting user-built PySide6/Qt shared libraries where technically feasible (see platform notes) | Release engineer | Packaging doc or smoke test replacing one Qt `.so`/`.dylib`/`.dll` |
| G5 | **Transitive inventory** — `LICENSES/transitive.csv` regenerated from the production lock used to build the binary; `make check-license-inventory` passes | Maintainer | Committed CSV + CI green |
| G6 | **Version record** — exact `PySide6`, Qt, and Python versions bundled are recorded in release notes and build metadata | Release engineer | Release notes / SBOM / build log |
| G7 | **Platform matrix** — each target OS/format (macOS `.dmg`, Windows `.msi`/`.exe`, Linux Flatpak/AppImage/deb) reviewed against the platform table below | Release engineer + counsel | Per-platform checklist sign-off |
| G8 | **Downstream clarity** — README or release page states who is **conveying** the combined work and where to obtain LGPL components | Maintainer | Published release page |

### Maintainer workflow

1. Freeze production dependencies (`requirements.txt`) and regenerate
   `LICENSES/transitive.csv` (`make generate-license-inventory`).
2. Draft the binary layout (which Qt `.so`/`.dylib`/`.dll` files ship, where notices live).
3. Complete G1–G8; do not tag a binary release until all items are checked or counsel documents
   an explicit waiver.
4. After the first binary release, re-run G2–G6 whenever PySide6/Qt versions or packaging
   tooling change.

### What this gate does not cover

- Automated SPDX/SBOM export formats (out of scope; see PYPOST-809).
- Trademark, export-control, or app-store policy review (counsel may add items under G1).
- Security signing (codesign, notarization, Authenticode) — required for distribution on some
  platforms but separate from LGPL license compliance.

## Platform-specific distribution notes

When bundling PySide6/Qt shared libraries, obligations are broadly the same across platforms
(LGPL notices, source offer, replacement rights). **Packaging mechanics differ** — plan per
target OS before building installers.

### macOS

| Topic | Guidance |
| --- | --- |
| Typical artifacts | `.app` bundle inside a `.dmg` or zip; PyInstaller/cx_Freeze place Qt frameworks under `Contents/Frameworks/` or adjacent `.dylib` files |
| Dynamic libraries | PySide6 wheels ship `libQt6*.dylib` and plugin directories (`platforms`, `styles`, etc.). Include all Qt libs the app loads at runtime, not only `libpyside6` |
| Replacement (LGPL) | Prefer `@rpath` / `@loader_path` layouts so users can swap bundled `.dylib` files without re-signing the entire bundle if your counsel agrees; document which paths are user-replaceable |
| Plugins | Qt platform plugins (e.g. `libqcocoa.dylib`) must be discoverable via `QT_PLUGIN_PATH` or standard bundle layout — missing plugins are a common packaging failure, not a license issue |
| Codesigning / notarization | Apple Gatekeeper requires signed and notarized binaries for wide distribution. Coordinate with G1 — signing may affect how users replace LGPL libraries |
| Python runtime | Frozen builds often embed a Python framework; MIT-licensed PyPost code remains separate from LGPL Qt libs in the bundle |

### Windows

| Topic | Guidance |
| --- | --- |
| Typical artifacts | Folder-style frozen exe, one-file PyInstaller extract, or `.msi` installer |
| Dynamic libraries | PySide6 ships `Qt6*.dll`, `pyside6.abi3.dll`, and plugin folders (`platforms`, `styles`). Ship MSVC runtime dependencies if your freeze tool does not bundle them |
| Replacement (LGPL) | Keep Qt `.dll` files in a dedicated directory (e.g. `PySide6/` or `_internal/`) documented in `ThirdPartyNotices.txt` so users can overwrite DLLs with a modified build |
| PATH / plugin discovery | Set `PATH` or use `QCoreApplication` library paths so Qt finds `platforms/qwindows.dll` — test on a clean VM without dev tools installed |
| Installer vs portable | MSI may write to `Program Files` (admin install). LGPL obligations apply regardless; ensure notices are visible post-install (About dialog or `LICENSES` in install dir) |
| Authenticode | Recommended for SmartScreen trust; not an LGPL requirement |

### Linux

| Topic | Guidance |
| --- | --- |
| Typical artifacts | Tarball with frozen binary, `.AppImage`, Flatpak, `.deb`/`.rpm` |
| Dynamic libraries | PySide6 wheels bundle `libQt6*.so` and plugins under `PySide6/Qt/lib` or similar; glibc baseline matters — build on an old enough distro or use manylinux-style baseline |
| Replacement (LGPL) | Prefer `$ORIGIN`-relative `RPATH` so users can replace `.so` files beside the executable; avoid stripping `DT_NEEDED` paths that force system Qt unless you intend users to use distro Qt |
| Flatpak / sandbox | Flatpak runtimes may supply Qt separately — clarify whether **you** convey LGPL Qt or the runtime does; counsel should review Flatpak manifest licensing |
| Distro packages | `.deb`/`.rpm` that depend on `python3-pyside6` from distro repos may shift conveyance to the distro maintainer; document which model PyPost official builds use |
| FHS paths | If installing to `/usr/lib`, ensure license files land in `/usr/share/doc/pypost/` or equivalent per distro policy |

### Cross-platform packaging checklist

Before tagging a binary release, verify on each platform:

1. Application launches on a **clean** machine/VM without a development venv.
2. `LICENSES/` or equivalent notices are present in the installed tree.
3. LGPL-3.0 full text and PySide6 copyright notices are included.
4. Documented path exists for users to obtain PySide6/Qt corresponding source matching the
   bundled versions.
5. At least one documented method to replace bundled Qt shared libraries (or counsel-approved
   alternative) has been tested or reviewed.

## Transitive license inventory (PYPOST-809)

| Context | Command |
| --- | --- |
| Committed output | `LICENSES/transitive.csv` (50 packages from `requirements.txt`) |
| Regenerate | `make generate-license-inventory` (requires `make install`) |
| Verify | `make check-license-inventory` |
| CI | Job `check-license-inventory` in `.github/workflows/test.yml` |

The inventory is built with pinned `pip-licenses` from the dev lock. The script filters
`pip-licenses --format=csv --with-urls` output to packages listed in the committed production
lock so dev-only tooling is excluded.

## What PyPost ships today

The upstream repository distributes:

- MIT-licensed **source code** and the root **`LICENSE`** file.
- **`LICENSES/transitive.csv`** — SPDX-style attribution for all packages in the production
  lock (`requirements.txt`), regenerated via `make generate-license-inventory` (PYPOST-809).
- **No** pre-built installers, frozen binaries, or bundled Qt libraries.

End users and developers install PySide6 via `requirements.txt` / `pip` (currently pinned
to `PySide6==6.11.1`). Future official release artifacts should follow the checklist above
if they bundle Qt.

## Version pinning

Production dependency pins live in `requirements.in` / `requirements.txt`. When preparing a
binary release, record the **exact PySide6 and Qt versions** bundled so corresponding source
can be identified (PyPI sdist/wheel and Qt version metadata).

## Troubleshooting

| Question | Guidance |
| --- | --- |
| Do I need this guide for local development? | No — running from source with your own venv is not redistribution |
| Does MIT PyPost code "infect" to GPL/LGPL? | Not when PySide6 is dynamically linked and LGPL terms are satisfied for the Qt libraries |
| Where is the PySide6 license in a venv? | After `pip install PySide6`, see `site-packages/PySide6/` and package metadata on PyPI |
| How do I refresh third-party attribution? | `make generate-license-inventory` after editing `requirements.in`; commit `LICENSES/transitive.csv` |
| Who owns compliance for a downstream fork's installer? | The party **conveying** the binary bundle |
| What must happen before the first official binary? | Complete [Pre-binary-release legal review gate](#pre-binary-release-legal-review-gate-pypost-810) (G1–G8) |
| Where are macOS/Windows/Linux packaging notes? | [Platform-specific distribution notes](#platform-specific-distribution-notes) |

## References

- [PySide6 on PyPI](https://pypi.org/project/PySide6/) — license metadata (LGPL-3.0)
- [Qt for Python — Licensing](https://doc.qt.io/qtforpython-6/licensing/index.html)
- [GNU LGPL-3.0](https://www.gnu.org/licenses/lgpl-3.0.html)
- [PyPost dependencies audit — License Notes](dependencies_audit.md#license-notes)
- Parent audit report: [ai-tasks/PYPOST-691/30-audit-report.md](../../ai-tasks/PYPOST-691/30-audit-report.md)

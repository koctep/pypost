# Licensing and Distribution (PYPOST-786)

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

## References

- [PySide6 on PyPI](https://pypi.org/project/PySide6/) — license metadata (LGPL-3.0)
- [Qt for Python — Licensing](https://doc.qt.io/qtforpython-6/licensing/index.html)
- [GNU LGPL-3.0](https://www.gnu.org/licenses/lgpl-3.0.html)
- [PyPost dependencies audit — License Notes](dependencies_audit.md#license-notes)
- Parent audit report: [ai-tasks/PYPOST-691/30-audit-report.md](../../ai-tasks/PYPOST-691/30-audit-report.md)

# PYPOST-1233: Fix E402 pytestmark import-order findings in four tests/ modules

## Research

This is a 1-story-point, purely mechanical source-ordering fix — no new module,
component, or interface is involved. Research consisted of confirming the exact
current shape of the four affected files and the existing regression guard:

- `tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir`
  (added by PYPOST-1070) runs `flake8 --select=E402 tests/` as a subprocess and
  asserts zero findings. Its own docstring documents the remediation:
  relocate each file's `pytestmark = pytest.mark.timeout(N)` line to *after*
  the file's last top-level import, because flake8's `module_imports_on_top_of_file`
  check (E402) treats any non-import top-level statement as ending the file's
  import block — every import after `pytestmark` then gets flagged.
- Verified (via `grep -n "^import\|^from\|pytestmark"`) that all four files
  named in the requirements currently have `pytestmark` positioned before one
  or more trailing top-level imports:
  - `tests/test_examples_modernization.py` — `pytestmark` at line 7, imports
    continue through line 16.
  - `tests/test_examples_modernization_repro.py` — `pytestmark` at line 7,
    imports continue through line 14.
  - `tests/test_ui_library_manager.py` — `pytestmark` at line 18, imports
    (including PySide6 and pypost imports) continue through line 52.
  - `tests/test_ui_library_manager_repro.py` — `pytestmark` at line 13,
    imports continue through line 26.
- Confirmed marker resolution is attribute-value-based, not source-position-based
  (`item.get_closest_marker("timeout")`), matching the guard test's own
  docstring and the precedent already established at scale by PYPOST-1070
  (110 files remediated with this identical pattern, zero behavioral
  regressions).

No further research (web or otherwise) is warranted: this is a well-precedented,
single-repo convention fix with an existing test that already specifies the
target shape and an existing 110-file precedent for the remediation mechanics.

## Implementation Plan

For each of the four files, move the `pytestmark = pytest.mark.timeout(30)`
line to sit immediately after that file's last top-level import statement
(i.e., to the position PYPOST-1070 already established as convention across
the other 110 files in `tests/`). Concretely:

1. `tests/test_examples_modernization.py` — move `pytestmark = pytest.mark.timeout(30)`
   (currently line 7) to directly below the last import in the
   `pypost.models.models` import block (currently ending at line 16).
2. `tests/test_examples_modernization_repro.py` — move `pytestmark = pytest.mark.timeout(30)`
   (currently line 7) to directly below the last import (currently
   `from pypost.core.collection_serializer import read_collection_file` at line 14).
3. `tests/test_ui_library_manager.py` — move `pytestmark = pytest.mark.timeout(30)`
   (currently line 18) to directly below the last import (currently
   `from pypost.ui import widget_ids` at line 52). Per the requirements, the
   PySide6 imports have no ordering constraint relative to `pytestmark` and
   need no special handling.
4. `tests/test_ui_library_manager_repro.py` — move `pytestmark = pytest.mark.timeout(30)`
   (currently line 13) to directly below the last import (currently
   `from pypost.ui import widget_ids` at line 26).

In every file: preserve the blank-line spacing convention used elsewhere in
`tests/` (one blank line between the import block and `pytestmark`, one blank
line after `pytestmark` before the next top-level statement), and change
nothing else — no import reordering beyond the relocation, no content edits,
no test-body changes, no other files touched.

**Mandatory — Failing Repro (next Step 3):** No new test is needed. The
existing permanent regression guard
`tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir`
(added by PYPOST-1070) is *already* the red automated repro for this exact
defect — it runs `flake8 --select=E402 tests/` and currently reports 20
findings, all attributable to these four files' `pytestmark`-before-imports
ordering. Step 3's job is to verify/confirm this pre-existing test is red for
the reason this task addresses (run
`make test PYTEST_ARGS="tests/test_lint_pytestmark_e402.py"` and confirm
failure, and optionally run `flake8 --select=E402 tests/` directly to confirm
the 20 findings map onto the four named files), not to author a new test.
Sequencing: confirm existing red guard (Step 3) → apply the four-file
relocation (Step 4) → confirm the guard test passes and reports zero E402
findings.

## Architecture

No architectural change. This task does not introduce, modify, or remove any
module, component, interface, or dependency — it reorders two lines
(`pytestmark` relative to the trailing import block) within four existing
test files. There is no module diagram, interaction scheme, or new
architectural pattern to document; the "architecture" in scope is the
source-ordering convention itself, which is unchanged (imports first, then
`pytestmark`) and already fully specified by the PYPOST-1070 precedent and the
guard test's docstring.

## Q&A

- **Q: Does this task need any new interfaces or module boundaries defined?**
  A: No — see Requirements Q&A and Architecture section above; this is a
  source-ordering fix with zero behavioral or structural change.
- **Q: Why does Step 3 not add a new test?** A: A real, currently-red
  automated check already exists in the tree
  (`tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir`)
  and directly covers this defect (E402 findings in exactly these four
  files). Writing a duplicate test would be redundant; Step 3's task is to
  confirm this existing test is the red repro, not invent a new one.

# PYPOST-1070: Repo-wide flake8 E402 noise from pytestmark-before-imports convention in tests/

## Research

### Baseline (inherited from Step 1, re-verified here)

`.venv/bin/python -m flake8 --jobs=1 --select=E402 tests/` → **642 findings across 110 files**,
runtime **~1.9s** (measured directly). Confirmed unchanged from Step 1's figure.

### Why `pytestmark = ...` trips E402: read the actual checker, don't guess

flake8 7.3.0 in this repo's `.venv` delegates E402 to **pycodestyle 2.14.0**'s
`module_imports_on_top_of_file` check
(`.venv/lib/python3.13/site-packages/pycodestyle.py:1164-1215`). Read directly rather than
assumed from memory. Its logic, per top-level logical line:

```python
allowed_keywords = ('try', 'except', 'else', 'finally', 'with', 'if', 'elif')

if indent_level:                       # indented code (inside try/if/etc.) is exempt
    return
...
if line.startswith('import ') or line.startswith('from '):
    if checker_state.get('seen_non_imports', False):
        yield 0, "E402 module level import not at top of file"
elif re.match(DUNDER_REGEX, line):     # __version__ = ... etc. — exempt
    return
elif any(line.startswith(kw) for kw in allowed_keywords):  # try:/if:/with: — exempt
    return
elif is_string_literal(line):          # docstrings — exempt
    ...
else:
    checker_state['seen_non_imports'] = True   # <-- pytestmark = ... lands here
```

`DUNDER_REGEX = r"^__([^\s]+)__(?::\s*...)? = "` (`pycodestyle.py:151`). `pytestmark` does not
match (no leading/trailing `__`), so it can never be dunder-exempted, and it isn't a `try`/`if`/
`with` guard either — it is a plain module-level assignment, which unconditionally sets
`seen_non_imports = True` and causes every subsequent top-level `import`/`from` line to be
flagged. This is the exact, version-pinned mechanism behind all 642 hits — not a guess.

**The three categories of legitimate `# noqa: E402` use** (matches this repo's own two existing
non-test precedents, `pypost/core/storage.py`, and general Python community practice — sys.path
shims before importing a not-yet-importable local package, `django.setup()` before importing
app modules, conditional/platform-gated imports pycodestyle's static keyword list can't cover)
all share one property: **a genuine ordering constraint forces the statement before the import**
— the import would not resolve, or would resolve to the wrong thing, if reordered. `pytestmark`
has no such constraint (see next section) — its position before imports is a *convention choice*
this project made, not a technical necessity. That distinction is the crux of the Step 2 decision.

### Does moving `pytestmark` after imports break timeout enforcement? Verified, not assumed

Read `tests/conftest.py:50-56` directly:

```python
def pytest_runtest_setup(item):
    if item.get_closest_marker("timeout") is None:
        pytest.fail(...)
```

`item.get_closest_marker("timeout")` is pytest's marker-resolution API — it walks the collected
item's marker stack (function → class → module), which pytest populates from the **module's
`pytestmark` attribute value**, not from where in the source file the assignment textually
appears. A module-level `pytestmark = pytest.mark.timeout(30)` contributes the same marker to
every test in that module regardless of whether it's the 3rd or the 30th line of the file, as
long as it executes at module import time (which any top-level statement does, in source order,
before pytest collection runs any test). Moving the assignment later in the file — but still at
module level, still executed during import — cannot change what `get_closest_marker` sees.
Confirmed empirically-consistent with the 106+ files (of 234 total using the convention) that
**already** place `pytestmark` after all imports today and are not reported as missing timeout
markers.

### In-repo precedent: which shape is actually already dominant?

Corrected the requirements doc's "216 files" figure while researching the target file set: that
count (`grep -rl '^pytestmark = pytest.mark.timeout' tests/`) only matches the single-call form.
There is also an 18-file **list form** (`pytestmark = [pytest.mark.timeout(60), pytest.mark.foo]`,
e.g. `tests/test_agent_lifecycle_smoke.py`), all currently already placed after imports (0 of the
18 appear in the 110 E402-flagged files). So **234 files** total use the module-level
`pytestmark` convention in either shape; **110 of 234 (~47%)** trigger E402; the other **124
(~53%) already place `pytestmark` after all imports** and are E402-clean today. Two representative
already-clean examples read directly:

```python
# tests/test_function_registry.py — imports, blank lines, THEN pytestmark
import pytest
import unittest

from jinja2 import Environment

from pypost.core.function_registry import FunctionRegistry


pytestmark = pytest.mark.timeout(30)


class TestFunctionRegistry(unittest.TestCase):
    ...
```

```python
# tests/test_agent_lifecycle_smoke.py — list-form pytestmark, also after imports
from __future__ import annotations

import socket

import pytest
from PySide6.QtWidgets import QApplication

from pypost.agent.lifecycle import AgentAppSession

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]
```

This is the key fact that settles the decision: **"imports first, then `pytestmark`" is already
the majority in-repo shape**, not a novel pattern Step 2 is inventing. The 110 broken files are
the minority outliers relative to the project's own existing practice.

### Repo has zero `# noqa: E402` precedent anywhere

`grep -rln 'noqa: E402' tests/ pypost/` → 0 matches (re-confirmed; matches Step 1's finding).
The two existing `# noqa` uses in `pypost/` are for `F401` (deliberately-unused re-exports in
`settings_dialog.py`) and `BLE001` (bare-except lint rule, `storage.py`/`ui_wait.py`) — different
codes, different justification shape (both are "this is intentional, no fix exists" cases, not
"this could be trivially reordered instead" cases). No E402-noqa idiom exists in this codebase to
extend.

### `.flake8` config has no `per-file-ignores`

`.flake8` (repo root) is minimal — `max-line-length = 100` and `extend-select = T201` only. A
blanket `per-file-ignores = tests/*.py: E402` config-level suppression was considered and
rejected: it would silence **all** E402 in **all** of `tests/` forever, including any future
genuinely-misplaced import unrelated to `pytestmark` — directly defeating User Story 1 in the
requirements doc ("so that any *new* findings I introduce are visible instead of buried"). Scoped
per-line `# noqa: E402` comments avoid that over-suppression but carry their own problems (next
section). Neither suppression variant was selected — see Decision below.

### `make test` already has flake8 available — no new dependency needed

`Makefile:152` — `test: $(VENV_MARKER) venv-test venv-otel`. `venv-test`
(`Makefile:32-46`) installs the `dev` extra from `pyproject.toml`, which includes
`flake8>=7,<8` (`pyproject.toml:34`). So any pytest test under `tests/` can shell out to
`python -m flake8` and it will be present in the same interpreter whenever `make test` runs —
confirmed via `tests/test_makefile.py:815 test_venv_test_installs_pytest_and_flake8`, an existing
precedent test that already asserts this.

## Decision: fix mechanism

**Chosen: (b) Restructure** — move `pytestmark = pytest.mark.timeout(...)` (or the list form) to
immediately after the last top-level import statement in each of the 110 currently-flagged
files. Rejected: (a) per-line `# noqa: E402` suppression.

### Justification

1. **No technical constraint favors "before imports."** The three research findings above
   establish, from primary sources (pycodestyle's own source, `conftest.py`'s own resolution
   code, and 124 already-working in-repo files), that `pytestmark`'s position is a pure style
   convention with zero functional dependency on where it sits relative to imports. When no
   ordering constraint exists, the flake8-native fix (satisfy the check structurally) is strictly
   preferable to suppressing the check — suppression is the tool reserved for cases (2) where a
   constraint genuinely exists and can't be designed around.
2. **The requirements doc's own User Story 3 disqualifies option (a).** Verbatim: contributors
   want a documented convention that "does not require also knowing an undocumented follow-up
   step (e.g., manually adding `# noqa: E402`) to keep the file lint-clean." Option (a) is
   exactly that undocumented follow-up step, forever: `make lint` never covers `tests/`
   (confirmed, see Scope below), so nothing mechanically catches a contributor who adds a new
   import after `pytestmark` in an existing or new file and forgets the `# noqa`. Option (a)
   would "fix" today's 642 hits while leaving the underlying trap — and the DX problem User
   Story 1 complains about — fully armed for the next contributor. Option (b) removes the trap:
   there is no longer any position where an import can land "after" `pytestmark`, because the
   documented pattern puts `pytestmark` last.
3. **Consistency is structurally cheaper under (b).** Under (a), full repo consistency would
   still require a second decision about whether the 124 already-clean files should also be
   forced to insert (harmless but pointless) `# noqa: E402` markers to "match," or whether the
   repo permanently carries two coexisting shapes (some files with imports-after-`pytestmark`
   +noqa, some with imports-before). Under (b), the 124 already-clean files need **zero** changes
   — they already are the target shape. Full-repo consistency (FR2's "ideally all 216 [234]
   files") falls out for free rather than requiring extra work or an explicit decision to leave
   it inconsistent.
4. **Mechanical/scale safety favors (b).** Option (a) requires locating and annotating all 642
   individual import lines (up to 18 in a single file, e.g. `tests/test_mcp_server_impl.py`,
   `tests/test_env_presenter.py`) — 642 discrete line-level edit sites, each one a chance for an
   off-by-one or a missed continuation line. Option (b) requires exactly **one relocated
   statement per file** — 110 discrete edit sites (file-level, not line-level), a ~6x smaller
   mechanical surface, and the edit is structurally uniform (cut one AST node's line span, paste
   it after another AST node's line span) rather than requiring per-line pattern matching across
   every import style (`import x`, `from x import y`, multi-line parenthesized imports, etc.).
5. **Zero behavioral risk, verified.** `tests/conftest.py`'s enforcement is proven
   position-independent (Research, above), so (b) carries no risk to the mandatory-timeout gate
   — consistent with this ticket's NFR that this is a formatting fix, not a behavioral change.
6. **Cost of (b) is a one-time doc-and-code reshuffle, paid once.** `doc/dev/testing.md`'s
   example snippet needs updating to show the new canonical order (small, one-time). This is
   strictly less ongoing cost than (a)'s permanent per-new-import tax.

### Why not rename `pytestmark` to something dunder-shaped (e.g. `__pytestmark__`)?

Not viable — `pytestmark` is a pytest-reserved module attribute name; pytest looks it up by that
exact identifier to collect module-level marks. Renaming it would silently stop applying the
marker at all (a real behavioral break, forbidden by the DoD). Not considered further.

## Implementation Plan

### Scope of the mechanical restructure

Applies to exactly the **110 files** flake8 currently flags (642 hits) — not all 234 files using
the convention. The other 124 already match the target shape (see Research) and need no edit;
touching them would only add unrelated diff noise to a ticket explicitly scoped as a
formatting/consistency fix. Full-repo consistency is still achieved (see Decision point 3).

### The mechanical fix script (design for Step 4 to implement and run — not implemented in this
step)

**Location (proposed for Step 4):** `scripts/fix_pytestmark_e402.py` (one-shot repo-maintenance
script, same category as other `scripts/*.py` one-shot/CI helpers already in the repo, e.g.
`scripts/lint_user_docs.py`).

**Why AST-based location + line-based editing, not pure regex and not `ast.unparse`:**
- Pure regex on `^pytestmark = pytest\.mark\.timeout\(` would silently miss all 18 list-form
  files (`pytestmark = [...]`) if any of them ever needed the fix, and is fragile against
  multi-line calls. `ast.parse` correctly locates the assignment regardless of its RHS shape
  (`Call` or `List`) via `node.lineno` / `node.end_lineno`.
- `ast.unparse()`-based rewriting was rejected: it regenerates the *entire* file from the AST,
  losing/reflowing comments, string quote style, and blank-line intent everywhere in the file —
  a far larger, harder-to-review diff than necessary. Using AST only to *find* line spans, then
  slicing the **original source text**, changes only the lines that need to move.

**Algorithm (per target file):**

```python
import ast

def fix_file(path):
    src = path.read_text()
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)

    # 1. Locate the single module-level `pytestmark = ...` assignment.
    mark_node = None
    for node in tree.body:                      # tree.body = top-level statements only
        if (isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "pytestmark"):
            mark_node = node
            break
    if mark_node is None:
        return "skip: no module-level pytestmark assignment found"  # defensive; unexpected

    # 2. Find the last top-level import that currently sits AFTER pytestmark.
    top_level_imports = [
        n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
    ]
    imports_after = [n for n in top_level_imports if n.lineno > mark_node.lineno]
    if not imports_after:
        return "skip: already E402-clean (no imports after pytestmark)"

    last_import_end = max(n.end_lineno for n in top_level_imports)

    # 2b. Fourth trigger condition: detect any top-level statement that is neither `mark_node`
    #     nor an import, but whose line falls inside the import span (first import's lineno
    #     through last_import_end). Relocating pytestmark alone cannot fix E402 in this shape —
    #     pycodestyle trips `seen_non_imports` on the FIRST non-import top-level statement it
    #     reaches in source order, regardless of where pytestmark itself ends up, so an import
    #     block split by an intervening def/class stays split and E402 still fires on every
    #     import after the split point. Confirmed against tests/test_request_save_orchestrator.py
    #     (see "Known exception" below) — do not silently report "fixed" while E402 remains.
    first_import_start = min(n.lineno for n in top_level_imports)
    stray_nodes = [
        n for n in tree.body
        if n is not mark_node
        and not isinstance(n, (ast.Import, ast.ImportFrom))
        and first_import_start <= n.lineno <= last_import_end
    ]
    if stray_nodes:
        return "skip: manual review — non-import, non-pytestmark statement between imports"

    # 3. Slice by line number (1-indexed lineno/end_lineno -> 0-indexed list slots).
    mark_lines = lines[mark_node.lineno - 1 : mark_node.end_lineno]
    before_mark = lines[: mark_node.lineno - 1]
    between = lines[mark_node.end_lineno : last_import_end]   # imports (+ blanks/comments)
    after_imports = lines[last_import_end :]

    # 4. Trim a single blank line that used to directly follow pytestmark (avoid a double blank
    #    at the old removal point); trim leading blanks off `after_imports` (we'll insert our
    #    own canonical spacing there instead).
    if between and between[0].strip() == "":
        between = between[1:]
    while after_imports and after_imports[0].strip() == "":
        after_imports = after_imports[1:]

    # 5. Reassemble: imports first, one blank line, pytestmark, two blank lines, rest of file
    #    (matches the dominant shape observed in the 124 already-clean files).
    new_lines = (
        before_mark
        + between
        + ["\n"]
        + mark_lines
        + ["\n", "\n"]
        + after_imports
    )
    new_src = "".join(new_lines)

    # 6. Safety check: the rewritten file must still parse before it's accepted.
    ast.parse(new_src)
    path.write_text(new_src)
    return "fixed"
```

**Driver behavior (Step 4):**
- Target set: the 110 files from `flake8 --select=E402 --jobs=1 tests/ | cut -d: -f1 | sort -u`
  (computed fresh at fix time, not hardcoded, in case the set has drifted since this step).
- `--check` / dry-run mode: report per-file `skip`/`fixed`/`error` without writing, so the diff
  can be reviewed (`git diff --stat`) before committing.
- Idempotent: re-running on an already-fixed file hits the "already E402-clean" skip branch — a
  second pass is a safe no-op, which also makes the script reusable if a future contributor
  reintroduces the old order in one file.
- Built-in verification: after processing, the script itself shells out to
  `flake8 --jobs=1 --select=E402 tests/` and exits non-zero (printing the remaining findings) if
  the count isn't 0 — Step 4 gets an immediate pass/fail signal instead of a separate manual step.
- Any file where `mark_node` can't be found, or where more than one module-level `pytestmark`
  assignment exists, or where the post-edit `ast.parse` fails, **or where the fourth check above
  (a non-import, non-`pytestmark` statement sitting between imports) trips**, is left untouched
  and reported for manual review rather than guessed at. **This is not purely defensive: exactly
  one of the 110 files is a confirmed instance of the fourth condition** (see "Known exception"
  immediately below) — the driver's manual-review report is expected to name that one file, not
  zero files. (An earlier draft of this section claimed zero exceptions across the 110; that claim
  was false and is corrected here after re-tracing the algorithm against this file's real source —
  see below.)

**Known exception: `tests/test_request_save_orchestrator.py`.** Its current shape (imports
elided for brevity):

```python
import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from unittest.mock import MagicMock, patch

from pypost.models.models import Collection, RequestData

def _mock_save_dialog(...):   # top-level def — NOT an import, NOT pytestmark
    ...
from pypost.models.settings import AppSettings
from pypost.ui.request_save_orchestrator import (...)
from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager, _make_request

@pytest.mark.usefixtures("qapp")
class TestRequestSaveOrchestrator(unittest.TestCase):
    ...
```

The top-level `def _mock_save_dialog(...)` (currently lines 10-22) is sandwiched between two
import groups — a pre-existing structural issue unrelated to the `pytestmark`-before-imports
convention this ticket targets, dating to PYPOST-317 (June 2026), not something introduced by or
in scope of this ticket's root cause. Tracing the algorithm against this file's actual source
confirms relocating `pytestmark` alone does not fix it: step 1 finds `mark_node` fine (exactly one
`pytestmark` assignment, so the first trigger doesn't fire); step 2's `imports_after` is non-empty
so the file isn't skipped as already-clean; without the fourth check added above, the reassembly
would move `pytestmark` to after the *last* top-level import line, but `_mock_save_dialog`'s
definition travels along inside the `between` slice unchanged and still ends up sitting between
the `from pypost.models.models...` import and the `from pypost.models.settings...` import — the
import block stays split in two either way. The rewritten file still parses fine (`ast.parse`
succeeds, so the third trigger doesn't fire either), but running `flake8 --select=E402` against
that mechanically-"fixed" result still reports **3 findings**, on the relocated
`from pypost.models.settings...`, `from pypost.ui.request_save_orchestrator...`, and
`from tests.test_tabs_presenter...` lines — because the function definition, not `pytestmark`'s
position, is what splits the import block, and moving `pytestmark` never touches the function.

**Concrete Step 4 instruction for this file (not an open question):** the fourth trigger condition
above will cause the script to skip this file and flag it for manual review rather than reporting
it "fixed." The manual fix: relocate the `_mock_save_dialog` function definition to immediately
after where `pytestmark` ends up (i.e., after all seven import statements and after `pytestmark`,
before the `@pytest.mark.usefixtures("qapp")` decorator / `TestRequestSaveOrchestrator` class).
This rests on the same principle as the `pytestmark` fix itself — Python has no requirement that
function definitions precede other top-level code, only that names be defined before their first
use, and `_mock_save_dialog` is only called from inside test methods, never at import time — and it
matches this file's own target shape better than the alternative: moving the trailing three-import
block up above the function would leave two separate import groups wrapped around the function
instead of one contiguous import block, a worse match for the dominant one-contiguous-import-block
shape used throughout this fix (see Research/Decision above). This is the **only** manual
follow-up required by this ticket; no other file among the 110 needs one.

### Documentation updates (Step 4, not this step)

- `doc/dev/testing.md` §"Per-test timeouts (mandatory)" → "Declaration" (currently lines
  883-897): update the example to show imports-first-then-`pytestmark`, matching the new
  canonical order:

  ```python
  import pytest

  from pypost.whatever import Thing

  pytestmark = pytest.mark.timeout(30)
  ```

  Add one sentence noting `# noqa: E402` is **not** the project's convention for this pattern —
  imports must come before `pytestmark`, full stop — to close off the option being
  reintroduced piecemeal by a future contributor who hits the same flake8 warning and reaches
  for the first fix they find (a suppression comment) instead of the documented order.
- `.cursor/lsr/do-testing.md` — confirmed (Step 1 Q&A, re-confirmed here: `.gitignore:48` lists
  `.cursor`, no `.cursor/` directory exists on disk) not reachable/committable in this checkout.
  Its live agent-facing equivalent in this environment is the global skill file
  `/home/.claude/skills/do-testing/SKILL.md` (§"Per-Test Timeout (MANDATORY)", module-scope
  example at lines 51-57) — **outside this git repository**, not part of any commit this task
  produces. Step 4 should update it as a best-effort secondary step (same example-order change),
  tracked separately from the repo commit; Step 8 (dev docs) should note this split explicitly so
  it isn't silently forgotten. This is unchanged from the requirements doc's own conclusion —
  restated here because Step 2 must design what Step 4 actually does with it, not just note the
  constraint.

### What does NOT change

- `pypost/` — zero files; this ticket's defect is entirely within `tests/`.
- `Makefile`'s `lint` target — stays `flake8 --jobs=1 pypost/` only (`Makefile:188`, unchanged).
- `tests/conftest.py` — zero changes; its marker-resolution mechanism is exactly why the fix is
  safe, not something the fix needs to touch.
- Any non-E402 flake8 finding in `tests/` (E302/E304/E305/F401/W293/E501/W391/E741/F841 — 350
  findings, explicitly out of scope per requirements doc).

### Explicit architectural decision: should `make lint` be widened to cover `tests/` too?

**No — stays out of scope for this ticket, decided explicitly here (not just inherited
silently).** Reasons:
1. The requirements doc's DoD and Scope (out) already settle this at the requirements level, and
   its Q&A explicitly states no such CI expansion is planned.
2. Even after this ticket's fix lands, `tests/` still carries **350 non-E402 findings** (E302
   217, E304 53, E305 32, F401 20, W293 13, E501 7, W391 4, E741 3, F841 1 — Step 1's full-scan
   count, re-confirmed unaffected by this ticket's E402-only scope). Widening `make lint` to
   `tests/` today, even after this fix, would immediately fail CI on those 350 pre-existing,
   unrelated findings. That is a materially larger cleanup than this ticket funds — it belongs in
   its own future ticket (candidate follow-up for Step 7's tech-debt notes), not folded into
   PYPOST-1070 as a scope-creep add-on.
3. This ticket's actual value (closing the E402/pytestmark inconsistency) is fully realized via
   the new permanent regression test (see Failing Repro below), which enforces the *specific*
   thing this ticket fixes without requiring the *general* `tests/`-wide lint gate to also be
   solved first.

### Sequencing

1. (This step) Research + decision — done.
2. Step 3: write the permanent regression test (below), confirm it is red today (642 hits,
   naturally, no fix landed).
3. Step 4: implement `scripts/fix_pytestmark_e402.py` per the algorithm above; run it in
   `--check` mode, review the diff, run for real across the 110 files; apply the one documented
   manual follow-up to `tests/test_request_save_orchestrator.py` (see "Known exception" above —
   the script's fourth trigger condition will skip and flag this file rather than "fix" it, and
   the manual relocation of `_mock_save_dialog` described there is required in addition to the
   mechanical pass); update `doc/dev/testing.md`; best-effort update the global `do-testing`
   skill file outside the repo commit; confirm the Step 3 regression test now passes — which,
   for this one file, requires the manual follow-up above and not just the mechanical script, so
   this is expected going in rather than something Step 4 has to debug from an unexplained
   final-verification failure; run the full suite (`make test`) to confirm no behavioral change;
   run `make lint` to confirm it's still `pypost/`-only and still green (unaffected by this
   ticket, per design).
4. Step 5 onward: normal cleanup/observability/tech-debt/docs passes.

### Mandatory — Failing Repro (Step 3)

This task **does** have a concrete, automatable, currently-red assertion to encode — even though
it has no *runtime test-outcome* behavioral change (NFR: timeout values/enforcement/test results
must be identical before and after). The behavioral change under test is **static: the E402
finding count**, which is exactly the kind of thing a red/green automated check should gate.

**What it asserts:** `flake8 --jobs=1 --select=E402 tests/` produces zero findings.

**Where it lives:** new file `tests/test_lint_pytestmark_e402.py` — a `tests/`-local meta/lint
test, following the existing precedent of `tests/test_makefile.py` (repo-tooling assertions
living as ordinary pytest tests) and `tests/test_pytest_exit_policy.py`. Not under `scripts/`,
not a Makefile target — see "Permanent vs. one-time" below for why.

**Why this file itself won't trip the very check it's asserting:** it is a **new** file authored
directly in the Step-3-target shape (imports first, `pytestmark` last) — it doesn't pre-exist in
the legacy order, so there's no bootstrapping problem. Sketch:

```python
"""Regression test: tests/ must have zero flake8 E402 findings caused by the
pytestmark-before-imports pattern (PYPOST-1070)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_no_e402_findings_in_tests_dir():
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--jobs=1", "--select=E402", "tests/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0 and not result.stdout.strip(), (
        "flake8 found E402 findings in tests/ (expected zero — see PYPOST-1070):\n"
        f"{result.stdout}"
    )
```

(Illustrative sketch only, per this step's instructions — Step 3 owns actually writing and
committing it, and should add an environment-availability skip, e.g.
`pytest.importorskip("flake8")`, so the test degrades gracefully rather than erroring if run
outside `make test`'s `venv-test`-provisioned environment.)

- `timeout=30` for the marker / `timeout=20` for the subprocess call: measured actual runtime is
  ~1.9s for this exact invocation against the current 642-hit tree; 30s (the "pure unit" tier
  per `doc/dev/testing.md`'s recommended tiers) leaves >10x headroom.
- Uses `sys.executable` (the interpreter already running pytest, guaranteed to have `flake8`
  installed via `venv-test`, per `Makefile:32-46` and `pyproject.toml:34`), not a hardcoded
  `.venv/bin/python` path — portable across however `make test`/CI invoke pytest.
- Scope is deliberately `--select=E402` (not full flake8), matching the DoD's E402-only "zero"
  criterion — this test is not meant to also gate the other 350 pre-existing findings (E302 etc.)
  that are explicitly out of scope.

**How Step 3 forces it red without the 110-file fix existing yet:** no special trick needed — the
repository is *already* in the red state (642 E402 hits, verified fresh in this step). Step 3
writes only this one new test file (touching nothing under the 110 legacy files, which remain
Step 4's job) and confirms via `pytest tests/test_lint_pytestmark_e402.py -v` that it fails today,
with the subprocess's `stdout` embedded in the assertion message showing the current 642 hits.
That failing run **is** the red proof handed to Step 3's independent review.

**Permanent vs. one-time — decided: permanent.** Reasons:
- Cost is genuinely cheap: ~2s wall-clock, no new runtime dependency (flake8 already required by
  `venv-test`), one small file.
- It runs automatically as part of `make test` (the file is a normal `tests/*.py` module —
  `pytest`'s default collection under `tests/ -m "not slow"`, `Makefile:152-154`, picks it up
  with no Makefile edit and no addition to `make lint`'s scope) — this is precisely how the
  ticket's DoD requirement ("`flake8 --jobs=1 tests/` reports zero E402... attributable to the
  pytestmark pattern") gets continuously enforced *without* widening `make lint` to cover
  `tests/` generally (which is explicitly out of scope, see above) and without requiring a
  separate CI step.
- Directly serves the ticket's own stated purpose: "prevent recurrence" of the
  pytestmark/E402 inconsistency. A one-time verification script, deleted after Step 4, would
  confirm the fix landed but would do nothing to stop a future contributor from reintroducing the
  legacy order in a new test file — exactly the gap User Story 1 and User Story 3 complain about.
  A permanent test closes that gap for the cost of one ~2-second subprocess call per test run.
- Should **not** be marked `@pytest.mark.slow` (default, included in `make test`'s fast run)
  given the measured ~2s runtime — Step 4 should re-measure after the fix (110 fewer findings to
  format doesn't change flake8's file-scan cost meaningfully) and only add `slow` if runtime
  proves disruptive, which is not expected.

## Architecture

### Module / component breakdown

| Component | Changes in this ticket | Owner step |
| --- | --- | --- |
| `tests/*.py` (109 of the 110 files currently flagged) | `pytestmark` assignment relocated to immediately after the last top-level import; no other content changes | Step 4 (script) |
| `tests/test_request_save_orchestrator.py` (1 of the 110, known exception) | `pytestmark` relocated by the script as usual, **plus** manual relocation of `_mock_save_dialog`'s definition to after all imports/`pytestmark` — see "Known exception" above | Step 4 (script + manual follow-up) |
| `tests/*.py` (remaining 124 files using the convention) | None — already in target shape | N/A |
| `tests/test_lint_pytestmark_e402.py` (new) | New permanent regression test | Step 3 (write, red) → stays in place through Step 4 (goes green) |
| `scripts/fix_pytestmark_e402.py` (new) | New one-shot mechanical-fix script (design above) | Step 4 |
| `doc/dev/testing.md` | Example snippet reordered; one sentence added ruling out `# noqa: E402` as the convention | Step 4 |
| `/home/.claude/skills/do-testing/SKILL.md` (global, outside repo) | Best-effort mirror of the same example reorder | Step 4, tracked outside the repo commit |
| `tests/conftest.py` | No changes (verified safe to leave untouched) | N/A |
| `pypost/` | No changes | N/A |
| `Makefile` (`lint`, `check` targets) | No changes — explicitly stays `pypost/`-only | N/A (explicit non-goal, justified above) |

### Interaction / data flow

```
contributor writes/edits a test file
        │
        ▼
follows doc/dev/testing.md's documented order:
  import pytest
  ...other imports...
  pytestmark = pytest.mark.timeout(N)      <-- now always LAST, after step 4's fix
        │
        ▼
pycodestyle's module_imports_on_top_of_file check (flake8 E402)
  sees only imports/docstring/dunders before any non-import statement
  → checker_state['seen_non_imports'] stays False through the whole import block
  → zero E402 findings
        │
        ▼
tests/test_lint_pytestmark_e402.py (make test, every run)
  subprocess: flake8 --jobs=1 --select=E402 tests/
  asserts empty output              <-- permanent regression gate
        │                                (independent of make lint, which stays pypost/-only)
        ▼
tests/conftest.py::pytest_runtest_setup
  item.get_closest_marker("timeout")   <-- unaffected by pytestmark's new position
  → mandatory-timeout gate still enforced, unchanged
```

### Architectural pattern

This is a **convention-normalization + regression-lock** pattern, not a new
module/interface/pattern in the product sense (no new classes, no new runtime interfaces — this
ticket touches test-file source layout and docs only). The closest named pattern is "linter
config as executable contract": instead of adding an exception to the linter's config (which
would be invisible/undiscoverable to a contributor and easy to silently broaden), the fix makes
the codebase satisfy the linter's actual rule, and locks that in with a same-suite automated
check rather than relying on tribal knowledge or periodic manual `flake8` runs.

## Q&A

**Q: Why not use flake8's `per-file-ignores` config instead of either inline noqa or
restructuring?**
A: Considered and rejected (see Research). It would suppress *all* E402 in `tests/*.py` forever,
including genuinely misplaced future imports unrelated to `pytestmark` — directly contradicts
User Story 1 in the requirements doc, which wants *new* findings to stay visible. Also still
requires the same doc-consistency work as option (a) without even solving option (a)'s "two
coexisting shapes forever" problem.

**Q: Does restructuring risk introducing new E302/E305 (blank-line) findings?**
A: Possible at the margins (moving a statement changes surrounding blank-line counts), but out of
scope for this ticket's DoD (E402 only) and not something Step 2 needs to solve — noted here so
Step 4 knows to spot-check (not gate on) the full non-`--select` flake8 count before/after as a
sanity signal, without treating any E302/E305 delta as a blocker.

**Q: Should the mechanical script also touch the 18 list-form (`pytestmark = [...]`) files or the
124 already-clean single-call files?**
A: No — none of the 18 list-form files are in the 110 currently-flagged set (verified: 0 overlap
between `grep -rl '^pytestmark = \['` and the E402-flagged file list), and the 124 already-clean
files need no edit by definition. The script's AST-based detection *would* handle either shape
correctly if it ever encountered a broken one (design is general, not narrowed to the single-call
form), but Step 4's actual run only needs to target the 110.

**Q: Why a new test file instead of adding a test method to the existing
`tests/test_makefile.py`?**
A: `test_makefile.py` is scoped to Makefile automation/venv-provisioning contracts (per its own
docstring, "Integration tests for root Makefile automation"). This check is a `tests/`-directory
lint-content assertion, unrelated to Makefile behavior — a separate, clearly-named file
(`test_lint_pytestmark_e402.py`) keeps the two concerns discoverable independently and avoids
overloading an already-large file (900+ lines).

**Q: Could the regression test instead live as a `make lint`-adjacent Makefile target instead of
a pytest test?**
A: Deliberately not — that would either (a) require adding `tests/` to `make lint`'s flake8
invocation, which is explicitly out of scope per the requirements DoD and reintroduces the "350
unrelated pre-existing findings" problem discussed above, or (b) require a *new*, separate
Makefile target that isn't wired into any existing `make test`/`make check`/CI invocation and so
would need someone to remember to run it — exactly the "manual verification step nobody runs"
failure mode this ticket is trying to close. A pytest test under `tests/` piggybacks on
`make test`'s existing, always-run collection with zero new wiring.

**Q: Live web research — why does the Research section rely on locally-available sources
(pycodestyle's installed source, in-repo file survey) rather than `websearch`?**
A: Per this step's task instructions: "you do not need live web access, use your own knowledge
plus what you find in this repo." The installed `pycodestyle.py` (exact version pinned by this
repo's `requirements.txt`/`pyproject.toml`, 2.14.0) is strictly more authoritative than a
web-search summary of flake8/E402 behavior would be — it is the literal code that produces every
one of the 642 findings this ticket addresses — so this was treated as the primary source rather
than a limitation to work around.

"""PYPOST-1070: permanent regression test asserting ``tests/`` has zero flake8
E402 ("module level import not at top of file") findings.

Background (see ``ai-tasks/PYPOST-1070/20-architecture.md`` for full evidence)
--------------------------------------------------------------------------
Many files under ``tests/`` place the module-level ``pytestmark = ...``
assignment (used to declare the mandatory per-test timeout, see
``tests/conftest.py::pytest_runtest_setup`` and ``doc/dev/testing.md``) *before*
the file's remaining imports. pycodestyle's ``module_imports_on_top_of_file``
check (flake8 code E402) treats any non-import, non-dunder, non-``try``/``if``/
``with``-guarded top-level statement as marking "end of the import block" --
``pytestmark = ...`` is exactly such a statement, so every import that follows
it is flagged. This is a pure convention/ordering issue: relocating
``pytestmark`` to *after* all imports does not change what
``item.get_closest_marker("timeout")`` sees (marker resolution is driven by the
module attribute's value, not its source position), so the fix carries zero
behavioral risk -- it is purely a static/lint-count assertion, not a runtime
behavior change.

This test is the permanent, `make test`-integrated regression lock for that
fix: it shells out to flake8 (scoped to ``--select=E402`` only, matching this
ticket's DoD -- other pre-existing, out-of-scope findings such as E302/E305/F401
in ``tests/`` are deliberately not gated here) and asserts the findings are
empty. PYPOST-1070 Step 4 completed that relocation across the flagged files;
this test now prevents later edits from reintroducing the ordering defect.

Why this file itself will not trip the very check it enforces: it is a *new*
file, authored directly in the target shape -- all imports first, then
``pytestmark`` -- so there is no legacy ordering to inherit.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]

# Measured actual runtime of this exact invocation against the current
# (642-hit) tree is ~1.9s (see ai-tasks/PYPOST-1070/20-architecture.md). 20s
# for the subprocess call itself, 30s for the pytest-level marker above,
# leaves generous (>10x) headroom over the measured baseline.
_SUBPROCESS_TIMEOUT_S = 20


def test_no_e402_findings_in_tests_dir():
    """``flake8 --select=E402 tests/`` must report zero findings.

    Before the Step 4 fix, this reported 642 findings across 110 files, all
    attributable to the pytestmark-before-imports convention described in the
    module docstring above. It is now a permanent regression guard: it detects
    the defect but deliberately leaves remediation to the offending file.
    """
    pytest.importorskip("flake8")

    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--jobs=1", "--select=E402", "tests/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT_S,
        check=False,
    )

    findings = [line for line in result.stdout.splitlines() if line.strip()]

    if result.returncode != 0 or findings:
        # flake8 exits 1 (findings present) or a nonzero error code (bad
        # invocation, e.g. missing tests/ path, config error). Distinguish the
        # two in the failure message so a triager doesn't waste time hunting
        # for pytestmark culprits when the real problem is an invocation bug,
        # and give the first several concrete file:line hits so the ticket
        # this test guards is immediately identifiable without re-running
        # flake8 by hand.
        preview_count = 10
        preview = "\n".join(findings[:preview_count])
        more = (
            f"\n... and {len(findings) - preview_count} more"
            if len(findings) > preview_count
            else ""
        )
        pytest.fail(
            "flake8 --jobs=1 --select=E402 tests/ reported "
            f"{len(findings)} finding(s) (expected 0). "
            f"returncode={result.returncode!r}. "
            "See PYPOST-1070: this is a permanent regression guard for the "
            "pytestmark-before-imports convention. If this fires, a new or "
            "edited file under tests/ has a top-level `pytestmark = ...` "
            "assignment positioned before one or more imports -- relocate it "
            "to immediately after the file's last top-level import.\n"
            f"First {min(preview_count, len(findings))} finding(s):\n{preview}{more}\n"
            f"--- flake8 stderr (if any) ---\n{result.stderr}",
            pytrace=False,
        )

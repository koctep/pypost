# PYPOST-1070: Repo-wide flake8 E402 noise from pytestmark-before-imports convention in tests/

## Programming Language

Python. The affected files are the pytest test modules under `tests/`; any fix mechanism
(inline suppression comments or import reordering) is applied to `.py` source files and, per
the ticket, mirrored into two Markdown convention documents (`doc/dev/testing.md` and — where
reachable, see Q&A — `.cursor/lsr/do-testing.md`).

## Goals

The project mandates a specific pattern for declaring the per-test timeout that every pytest
module must carry (see `do-testing` agent rules, mirrored in `doc/dev/testing.md` §"Per-test
timeouts (mandatory)"):

```python
import pytest

pytestmark = pytest.mark.timeout(30)

import gc          # ... remaining imports follow
import json
...
```

Because `pytestmark = ...` is a statement, not an import, flake8's E402 check ("module level
import not at top of file") flags every import line that follows it. The repo's own mandated
test-authoring convention therefore systematically conflicts with the repo's own linter, on a
large and growing fraction of `tests/`.

This matters for two reasons, independent of whether it currently gates CI:

1. **Local-linting hygiene / developer experience.** Any contributor who runs `flake8` (or an
   IDE/editor integration backed by flake8) against `tests/` — not just `pypost/` — sees
   hundreds of warnings that are 100% attributable to a convention the project itself requires,
   not to real code-quality problems. This trains developers to tune out flake8 output for
   `tests/`, which risks masking genuine E402 or other findings introduced by accident.
2. **Consistency of the repo's own mandated convention with its own linter config.** A
   convention that a project enforces (via `do-testing` agent rules and `tests/conftest.py`'s
   timeout-marker gate) should not simultaneously be flagged as a style violation by the same
   project's chosen linter. Leaving this unresolved is a standing inconsistency between two
   parts of the project's own tooling.

Whether this is purely a local nuisance or something CI-relevant depends on the scope of
`make lint`, which currently only targets `pypost/` — see Q&A for the verified answer and its
forward-looking implication.

## User Stories

- As a **developer** running `flake8` locally (directly, or via an editor/IDE integration) to
  check my own working tree, I want `tests/` to be free of E402 findings caused by the
  mandated `pytestmark` convention, so that any *new* findings I introduce are visible instead
  of buried in hundreds of pre-existing, convention-caused warnings.
- As a **maintainer** who might one day widen `make lint` / CI static analysis beyond
  `pypost/` to also cover `tests/`, I want the mandated test-file convention to already be
  E402-clean, so that widening the lint gate doesn't require a separate, disruptive cleanup
  pass just to reach a green baseline.
- As a **contributor writing a new test file**, I want the documented `pytestmark` convention
  (`.cursor/lsr/do-testing.md` / `doc/dev/testing.md`) to describe a pattern that doesn't
  itself trigger flake8 warnings, so that following the documented convention exactly does not
  require also knowing an undocumented follow-up step (e.g., manually adding `# noqa: E402`)
  to keep the file lint-clean.
- As the **owner of the do-testing convention documents**, I want the convention described in
  `doc/dev/testing.md` (and its agent-facing counterpart) to match the convention actually
  applied across `tests/`, so the docs stay a trustworthy source of truth rather than
  describing a pattern that in practice always needs an undocumented workaround.

## Definition of Done

- [ ] Running `flake8 --jobs=1 tests/` (the same invocation style `make lint` uses for
      `pypost/`, pointed at `tests/`) reports **zero E402 findings attributable to the
      pytestmark-before-imports pattern** — i.e., no test file emits E402 solely because its
      module-level `pytestmark = pytest.mark.timeout(...)` assignment sits between `import
      pytest` and the file's remaining imports. (E402 findings from unrelated causes, if any
      exist or are newly introduced, are out of scope for "zero" here — none were observed
      during Step 1's verification; see Q&A.)
- [ ] Exactly one convention is chosen and applied consistently across every currently affected
      file (measured at 110 files / 642 hits as of this writing — see Q&A for the count and its
      reproduction command) — not a mix of "some files use noqa, some are reordered."
- [ ] The chosen convention is documented in `doc/dev/testing.md` (repo-tracked) and, where the
      file is reachable for edits in this environment, `.cursor/lsr/do-testing.md` (see Q&A on
      why this second file's editability is uncertain), so that a future contributor who
      follows the documented pattern for a *new* test file does not reintroduce E402 findings.
- [ ] `tests/conftest.py`'s existing mandatory-timeout-marker enforcement (the fixture that
      fails test setup when `item.get_closest_marker("timeout")` is `None`) continues to pass
      unchanged — the fix must not weaken or bypass that gate.
- [ ] The full test suite (`make test` / equivalent) still passes after the change — this is a
      lint/style/documentation fix, not a behavioral change, so no test's runtime behavior
      should differ.
- [ ] `make lint` (which only runs flake8 against `pypost/`) is unaffected/unchanged in scope by
      this ticket — this ticket does not add `tests/` to the enforced CI gate (see Q&A for why
      that's an explicit non-goal).

## Task Description

### Problem

`.venv/bin/python -m flake8 --jobs=1 tests/` reports 642 E402 findings across 110 files (see
Q&A for the verified count and how it differs from the ticket's original "692 hits across 207
files" estimate). Every instance has the same root cause: a test module that follows the
project's mandatory per-test-timeout convention —

```python
import pytest

pytestmark = pytest.mark.timeout(30)

import gc
import json
...
from pypost.core.alert_manager import AlertManager, AlertPayload
```

— places a non-import statement (`pytestmark = ...`) between the first import and the rest of
the module's imports. flake8's E402 check treats every import after that statement as "not at
top of file." Confirmed in the wild, e.g. `tests/test_alert_manager.py` (9 E402 hits from
exactly this shape) and `tests/test_code_editor.py` (10 hits).

`make lint` invokes `flake8 --jobs=1 pypost/` only (`Makefile` line 188) — `tests/` is never
passed to flake8 in any Makefile target, so none of these 642 findings currently fail CI or
`make lint`/`make check`. This is a local/IDE-linting nuisance today, not a build-breaking
defect.

### Candidate fix directions (from the Jira description — not decided in this step)

The ticket names two repo-wide conventions to choose between; picking one requires
architectural judgment and is Step 2's job, not this step's:

1. **Suppress**: add a per-file (or module-wide) `# noqa: E402` convention to the mandated
   test-file pattern, applied to every import line after `pytestmark`. Mechanically simple and
   preserves the exact `import pytest` / `pytestmark` / remaining-imports ordering that
   `do-testing.md` currently documents and that 216 existing files already follow (110 of which
   currently trigger E402; the other 106 already have this ordering without tripping E402,
   typically because they have no further imports below `pytestmark`). Downside: `# noqa`
   comments must be applied to *every* subsequent import line in an affected file (not just
   one), which is what produces multi-hit files (up to 18 hits in `tests/test_mcp_server_impl.py`
   and `tests/test_env_presenter.py`).
2. **Restructure**: move `pytestmark = pytest.mark.timeout(...)` to after all imports, so no
   import line follows it. This is the flake8-native fix (no suppression comments needed) but
   changes the documented convention itself, meaning every currently-affected file's import
   block needs reordering, and `do-testing.md` / `doc/dev/testing.md`'s example snippets need
   to change to show the new canonical order. One relevant data point gathered in this step:
   `tests/conftest.py`'s enforcement of the mandatory timeout marker resolves it via pytest's
   `item.get_closest_marker("timeout")` API, not by the marker assignment's textual position in
   the file — so moving `pytestmark` after imports does not, on its own, appear to break the
   existing timeout-enforcement mechanism. (This is an observation to feed into Step 2's
   decision, not a decision itself — Step 2 should still verify it empirically before relying
   on it.)

### Scale consideration for Step 2

110 files / 642 hits is too large a set to edit file-by-file by hand without high risk of
inconsistency or missed files. Whichever convention is chosen, Step 2 should plan for a
**scripted/mechanical edit** (e.g., a small Python/AST or regex-based rewrite script run once
across all affected files, with `flake8 --select=E402 tests/` used as the before/after
verification), not manual editing of 110 individual files. This step does not choose the
mechanism, but the file/hit count is significant enough evidence that "apply it consistently
across all affected test files in one pass" (the ticket's own phrasing) implies automation.

### Scope (in)

- Resolving the 642 E402 findings in `tests/` caused specifically by the pytestmark-before-
  imports pattern, via one consistently-applied convention.
- Updating `doc/dev/testing.md` (and, if reachable, `.cursor/lsr/do-testing.md`) so the
  documented convention matches what's actually applied.
- Verifying `tests/conftest.py`'s timeout-marker enforcement and the full test suite still pass
  after the change.

### Scope (out)

- Adding `tests/` to `make lint`'s enforced flake8 gate (this ticket does not change CI scope —
  see Q&A).
- Fixing any other flake8 codes present in `tests/` (E302, E304, E305, F401, W293, E501, W391,
  E741, F841 were also observed during Step 1's verification pass — none are in scope for this
  ticket, which is specifically about E402 from the pytestmark convention).
- Any behavioral change to test execution, timeout values, or the timeout-marker enforcement
  mechanism itself.

### Constraints and assumptions

- The fix must not weaken or remove the mandatory-per-test-timeout requirement or its
  enforcement in `tests/conftest.py`.
- The fix must not change any test's actual timeout value or runtime behavior — this is a
  formatting/documentation-consistency fix.
- `.cursor/` is listed in `.gitignore` (line 48) and does not exist in this checkout at all;
  `.cursor/lsr/do-testing.md` is therefore not a file this repo's git history tracks in this
  environment. See Q&A for how this affects the DoD's documentation-update criterion.
- 216 files currently use the module-level `pytestmark = pytest.mark.timeout(...)` convention;
  106 of them already have no import lines after `pytestmark` (or already order imports before
  it) and so are already E402-clean under the current pattern — those files may still be worth
  bringing into whatever convention Step 2 picks, for consistency, even though they aren't
  contributing to the current 642-hit count.

## Main Entities and Interactions

- **Test module**: a `.py` file under `tests/` that pytest collects; the unit this ticket
  operates on.
- **`pytestmark` convention**: the mandated module-level marker assignment
  (`pytestmark = pytest.mark.timeout(N)`) that every test module must carry, per `do-testing`
  agent rules and `doc/dev/testing.md`.
- **flake8 E402 check**: the static-analysis rule that flags import statements appearing after
  non-import, module-level code.
- **`make lint`**: the Makefile target that runs flake8 against `pypost/` only; does not
  currently touch `tests/`.
- **`tests/conftest.py` timeout gate**: the pytest fixture that fails test setup when a
  collected test has no resolvable `timeout` marker, independent of where in the file that
  marker was assigned.
- **Convention documents**: `doc/dev/testing.md` (repo-tracked) and `.cursor/lsr/do-testing.md`
  (agent-facing mirror; not present/tracked in this checkout — see Q&A), which describe the
  mandated pattern to contributors and AI agents respectively.

The test module is authored following the `pytestmark` convention as documented; flake8's E402
check inspects the resulting import ordering; `make lint` does not currently exercise this path
against `tests/`, so the conflict is externally invisible to CI today but visible to anyone
running flake8 directly against `tests/`. The convention documents are the source contributors
and agents read when writing new test files, so whichever fix is chosen must be reflected there
to prevent regression.

## Functional Requirements

1. Zero flake8 E402 findings in `tests/` attributable to the pytestmark-before-imports pattern,
   verified by `flake8 --jobs=1 tests/` (or `--select=E402 tests/`).
2. One convention applied consistently across all currently affected files (and, ideally, all
   216 files using the `pytestmark` timeout convention, for long-term consistency).
3. `doc/dev/testing.md` updated to document the chosen convention's exact code shape.
4. `.cursor/lsr/do-testing.md` updated to match, to the extent that file is reachable/editable
   in the implementation environment (see Q&A).

## Non-Functional Requirements

- **No behavioral change**: test timeout values, timeout enforcement, and test outcomes must be
  identical before and after.
- **Consistency**: the fix must not leave a mix of suppressed and reordered files without a
  documented reason.
- **Maintainability**: given the scale (110+ files), the fix should be applied via a repeatable,
  scripted mechanism rather than ad hoc manual edits, so a future contributor adding a new test
  file can follow one documented, linter-clean pattern going forward.

## Q&A

**Q: Is `make lint` scoped only to `pypost/`, or does anything already lint `tests/`?**
A: Verified directly from `Makefile` (lines 187-190): the `lint` target runs
`$(BIN)/python -m flake8 --jobs=1 pypost/`, followed by two documentation-link checker scripts.
Nothing in the Makefile passes `tests/` to flake8, mypy, or any other static-analysis tool.
`check` (line 198) is `lint test verify-ai-tasks` — `lint` here is the same `pypost/`-only
target. So today, this really is out-of-CI-gate-scope: no Makefile target and (by extension) no
CI workflow currently fails on E402 findings in `tests/`.

**Q: Could a future CI expansion make this relevant?**
A: Yes, plausibly. If `make lint` is ever widened to also cover `tests/` — a reasonable future
step, since `pypost/` is already gated and `tests/` is the only major Python source tree left
out — the 642 pre-existing E402 findings would immediately fail that gate unless this ticket
(or an equivalent cleanup) has already landed. Resolving this now is explicitly a
readiness/DX investment against that possibility, not just a cosmetic fix. (No such CI
expansion is currently planned or in scope for this ticket — this is forward-looking context
only, called out because the ticket text raises the question.)

**Q: Does the ticket's "692 E402 hits across 207 files" figure still hold?**
A: No — verified independently in this step by running
`.venv/bin/python -m flake8 --jobs=1 tests/` (and cross-checked with `--select=E402` and
`--isolated`, all three give the same result): **642 E402 findings across 110 files**, as of
2026-08-20. Two things likely explain the gap:
1. **Hit-count drift (692 → 642, ~7% lower)**: plausible ordinary drift from `tests/` churn
   since the ticket was filed (test files added/removed/edited across several sprints,
   including sprint 1303 itself — e.g. an untracked new stress test file present in this
   checkout, `tests/test_agent_dialog_settle_teardown_stress.py`, from a concurrent PYPOST-1040
   task). Not surprising and doesn't change the conclusion.
2. **File-count gap (207 claimed vs. 110 measured, ~2x)**: this looks like more than drift. 216
   files in `tests/` currently use the module-level `pytestmark = pytest.mark.timeout(...)`
   convention at all (`grep -rl '^pytestmark = pytest.mark.timeout' tests/`), which is close to
   the ticket's "207." But only 110 of those 216 actually trigger E402 — the other 106 have no
   import statements after their `pytestmark` line (or already order imports before it), so
   flake8 has nothing to flag in them. The most likely explanation is that the original
   "207 files" count measured *files using the convention* rather than *files actually
   triggering E402* — a looser (and now measurably incorrect) proxy for the thing the ticket is
   actually about. Recorded here per this step's instruction to verify rather than blindly
   trust the ticket text; Step 2 and later steps should use **642 hits / 110 files** as the
   baseline, not the ticket's original numbers.

**Q: Is `.cursor/lsr/do-testing.md` — the file both the ticket and `doc/dev/testing.md` (lines
881 and 1764) point to — actually present and editable in this repository?**
A: No, not in this checkout. `.gitignore` line 48 lists `.cursor`, and no `.cursor/` directory
exists on disk here at all (confirmed: `ls .cursor` → "No such file or directory"). It is a
machine-local, gitignored mirror of the equivalent agent-facing rules, which in this environment
are served instead as the global `do-testing` Claude Code skill
(`/home/.claude/skills/do-testing/SKILL.md`) — content-equivalent (same mandatory `pytestmark`
pattern, same tiers) but outside this git repository and outside anything a commit in this repo
can change. **Implication for later steps**: the DoD's "update `.cursor/lsr/do-testing.md`"
criterion cannot be satisfied by a repo commit in this environment — only `doc/dev/testing.md`
is reachable and repo-tracked. Step 2/4 should treat `doc/dev/testing.md` as the authoritative,
committable target and either skip the `.cursor` file with a note (since it's gitignored/absent
here) or, if the actual global skill file is later found to be in-scope and editable, update it
as a best-effort secondary step outside the repo commit.

**Q: What other flake8 codes appear in `tests/` besides E402, and are they in scope?**
A: A full (non-`--select`) `flake8 --jobs=1 tests/` run also reports E302 (217), E304 (53), E305
(32), F401 (20), W293 (13), E501 (7), W391 (4), E741 (3), and F841 (1) — 992 total findings
across all codes. None of these are caused by the pytestmark convention and none are in scope
for this ticket, which the Jira description scopes specifically to E402. Left as-is; not
mentioned in the DoD's "zero" criterion, which is scoped to E402 only.

**Q: Is a bulk mechanical/scripted edit across 110+ files sane to do in one pass, or should
this be split up?**
A: Not decided in this step (architectural judgment, Step 2's job), but the evidence gathered
here — 110 files, 642 hits, all sharing the exact same structural cause and no existing `# noqa`
precedent anywhere in `tests/` (`grep -rl 'noqa: E402' tests/` → 0 matches) — points toward a
single scripted pass with `flake8 --select=E402 tests/` as an automatic before/after check,
rather than either manual per-file edits or splitting the work across multiple tickets. Offered
as input to Step 2, not a decision made here.

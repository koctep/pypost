# PYPOST-1011: Technical Debt Analysis

## Shortcuts Taken

None found. The implementation matches `20-architecture.md` almost exactly:

- `write_json_export_file(path, payload, *, error_cls)` in the new
  `pypost/core/export_file_writer.py` is the single real implementation
  (`mkdir(parents=True, exist_ok=True)` → `json.dumps(indent=2)` →
  `write_text(text + "\n", encoding="utf-8")`), catching exactly
  `(OSError, TypeError, ValueError)` and re-raising as
  `error_cls(f"Could not write file: {exc}") from exc`, as planned.
- `pypost/core/collection_export.py::write_export_file` and
  `pypost/core/environment_export.py::write_export_file` are now thin wrappers
  (`write_json_export_file(path, payload, error_cls=...)` + the existing
  domain-specific `logger.info(...)` line), with public signatures, return
  type, and raised exception types unchanged — verified by re-reading both
  files (lines 95-98 and 106-109 respectively).
- No cross-domain import was introduced: `export_file_writer.py` imports
  neither `collection_export` nor `environment_export`, and neither domain
  module imports the other (confirmed by inspection — `collection_export.py`
  imports only `pypost.core.export_file_writer` and `pypost.models.models`;
  `environment_export.py` imports `pypost.core.export_file_writer`,
  `pypost.core.storage_interface`, and `pypost.models.models`).
- Both call sites (`pypost/ui/presenters/collection_export_actions.py`,
  `pypost/ui/widgets/environments/environment_list_widget.py`) were left
  untouched, per the "no call-site changes" plan — confirmed by `git status`
  showing no diff for the environment widget, and the collection-export
  presenter's modification in the working tree belongs to the unrelated,
  concurrent PYPOST-1010 ticket (out of scope for this review, per task
  instructions).
- The rejected-alternative rationale in `20-architecture.md` (injected
  `error_cls` vs. a shared exception base class) was followed as decided —
  no shared exception type was introduced, avoiding an unnecessary public API
  change to two independently-referenced error classes.

The one intentional, already-reviewed behavior change — widening environment
export's caught-exception set from `{OSError}` to `{OSError, TypeError,
ValueError}` so it now also wraps non-serializable payloads — was the
explicit purpose of this ticket (closing a real bug/gap), not a shortcut.

## Code Quality Issues

Minor, non-blocking observations — none warrant a follow-up on their own:

- `write_json_export_file`'s `payload` parameter is typed as plain `object`
  (necessarily generic, since the helper is domain-agnostic), which is looser
  than the `dict | list[dict]` / `list[dict] | dict` types each domain
  wrapper still declares for its own `payload` parameter. This is the correct
  trade-off for a shared, dependency-free leaf module — the domain wrappers
  are exactly where the more specific types belong — but it's worth noting
  that `write_json_export_file` itself gives up static guarantee that
  `payload` is JSON-serializable-shaped; that's caught at runtime via the
  `TypeError`/`ValueError` wrapping instead, which is the intended and
  already-documented design (see `20-architecture.md`, "Selected pattern").
- `CollectionExportError` and `EnvironmentExportError` still have byte-identical
  one-line docstrings (`"Raised when an export file cannot be written."`).
  This duplication predates this ticket (both classes already existed with
  that docstring before the refactor) and consolidating them would require
  either a shared base exception (explicitly rejected in the architecture
  doc, for good reason — see Q&A) or cross-domain coupling. Not new debt from
  this change; not worth a follow-up.

## Missing Tests

No coverage gaps found for the code actually touched by this ticket:

- `tests/test_export_file_writer.py` directly covers `write_json_export_file`:
  successful write (parent-dir creation, indented UTF-8 JSON with trailing
  newline), `OSError` wrapped into the caller-supplied `error_cls`,
  `TypeError` (non-serializable payload) wrapped into the caller-supplied
  `error_cls`, and a check that a *different* caller-supplied `error_cls` is
  actually used (guards against a hardcoded exception type sneaking back in).
- `tests/test_environment_export.py::test_write_export_file_raises_on_non_serializable_payload`
  closes the Step 3 red-test gap (environment export previously let a raw
  `TypeError` escape for a non-serializable payload; now wrapped in
  `EnvironmentExportError` via the shared helper).
- `tests/test_environment_export.py::test_write_export_file_raises_on_write_failure`
  and the equivalent in `tests/test_collection_export.py` continue to cover
  the `OSError` path end-to-end through each domain wrapper.
- Both domains' existing round-trip tests
  (`test_write_export_file_round_trips_through_import`,
  `test_exported_json_is_single_object_shape`) continue to pin the on-disk
  format (indented JSON, trailing newline, UTF-8) through the new
  consolidated code path.
- Not covered, and not needed: a test asserting that
  `write_json_export_file` raises a `ValueError` specifically (as opposed to
  `TypeError`) for a non-serializable payload. `json.dumps` can raise
  `ValueError` for circular references or certain float values (`NaN`/`Infinity`
  with `allow_nan=False`), but no current caller passes payloads that could
  trigger that path, and the `TypeError` case (the realistic failure mode,
  covered by three separate tests across the two test files) already
  exercises the same `except (OSError, TypeError, ValueError)` branch. Not
  worth a dedicated test for an unreachable-in-practice sub-case.

All in-scope tests pass: `make test PYTEST_ARGS="tests/test_environment_export.py
tests/test_collection_export.py tests/test_export_file_writer.py -v"` — 27/27
passed (re-verified during this review). `make lint` clean. `make typecheck`
— mypy baseline OK (219 known errors, no new ones).

## Timeout Marker Check (BLOCKER gate)

Verified per `.cursor/lsr/do-testing.md`: every in-scope test file declares an
explicit module-level `pytestmark = pytest.mark.timeout(60)`:

- `tests/test_export_file_writer.py:10`
- `tests/test_environment_export.py:22`
- `tests/test_collection_export.py:23` (not in this ticket's file-scope list,
  but exercises the same shared helper through the collection wrapper, so
  checked for completeness)

No missing timeout markers found. **Not a blocker.**

## Performance Concerns

None. The change is a pure code-motion/consolidation refactor — same three
operations (`mkdir` → `json.dumps` → `write_text`), same call count, no new
loops, no new I/O, no new serialization passes. `json.dumps(indent=2)` was
already used by both domains before this change; nothing here alters
algorithmic complexity or adds overhead on the write path.

## Follow-up Tasks

None required for this ticket's own scope — the work is complete, matches the
architecture plan, and introduces no new debt.

One doc-freshness note (not new debt, action deferred to this same task's
Step 8, not a separate follow-up): `doc/dev/collection_export.md:136` and
`doc/dev/environments_dialog.md:181-193` document `write_export_file(path,
payload)` at the call-site/API level (signature, exception type, on-disk
format) — that description is still accurate today (the public contract is
unchanged), but neither doc currently mentions that both domains now share
the same underlying `pypost/core/export_file_writer.py` implementation. Step
8 (Dev Docs) should add a short pointer to the new shared module in one or
both of these files so future readers don't rediscover the duplication this
ticket just removed. No separate Jira follow-up needed — this is in-scope for
Step 8 of this same ticket.

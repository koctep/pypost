# PYPOST-429: ELF Core Dump Investigation Report

**Date:** 2026-06-12  
**Status:** Closed — unreproducible native crash; no application defect found on current HEAD

## 1. Incident summary

| Field | Value |
| --- | --- |
| Artifact | `core` (ELF core dump, ~86 MB) |
| Location | Repository root |
| Removed in | PYPOST-403 (`afd2a58`, 2026-03-25) |
| Attributed test module | `tests/test_tabs_presenter.py` (PYPOST-403 requirements §4) |
| Committed to git? | **No** — never tracked; local working-tree file only |

## 2. Evidence gathered

### 2.1 Git history

- `git log --all -- core` returns no commits; the dump was never versioned.
- PYPOST-403 deleted the file from the working tree and added anchored patterns to `.gitignore`:

  ```gitignore
  # ELF core dumps
  /core
  /core.*
  ```

### 2.2 Related code history

- `TestOnRequestError` in `tests/test_tabs_presenter.py` was introduced in PYPOST-400
  (`031194b`). That class exercises `TabsPresenter._on_request_error` with mocked dialog helpers.
- PYPOST-403 fixed separate CI failures (HTTPClient `TemplateService`, `HistoryManager.flush`) and
  removed the dump as housekeeping — it did not change `test_tabs_presenter.py`.

### 2.3 Reproduction (2026-06-12)

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_tabs_presenter.py -v
# Result: 60 passed in 0.91s — no crash, no core file
```

Full `make test` on the same date reported unrelated failures in `test_makefile.py` and
`test_http_client_sse_probe.py`; **no segfault** and no new `core` file.

## 3. Root-cause classification

**Verdict: unreproducible native (C++/Qt) process crash — not a current Python application bug.**

An ELF `core` file is produced when the OS kernel writes a full process image after `SIGSEGV`,
`SIGABRT`, or similar. Python exceptions do not create `core` files unless `ulimit -c` is enabled
and a native extension aborts.

### 3.1 Ranked hypotheses (historical)

| Rank | Hypothesis | Rationale |
| --- | --- | --- |
| 1 | Manual pytest without offscreen Qt | Running `pytest tests/test_tabs_presenter.py` without `QT_QPA_PLATFORM=offscreen` can trigger native Qt platform plugin crashes on headless or mixed GUI sessions. `tests/conftest.py` sets offscreen via `setdefault`, but only when pytest loads conftest **before** widget imports. Direct `unittest` discovery or IDE runners may skip or reorder this. |
| 2 | QApplication lifecycle during PYPOST-400 development | `TestOnRequestError` uses `unittest.TestCase` with `setUpClass` creating `QApplication.instance() or QApplication([])` while pytest also provides a module-scoped `qapp` fixture. During iterative development of error-dialog tests, mixed lifecycles are a known Qt footgun. |
| 3 | Transient PySide6 / Qt macOS bug | One-off segfaults in Qt offscreen or Cocoa backends are documented upstream; without the dump or lldb backtrace, version-specific bugs cannot be confirmed. |

### 3.2 Ruled out

- **Python-level exception in `_on_request_error`**: would not produce an 86 MB ELF core.
- **Current CI regression**: all 60 `test_tabs_presenter` tests pass on HEAD; no crash artifact.
- **Committed secret / binary**: file was never in git history.

## 4. Preventive measures (already in place)

| Measure | Where |
| --- | --- |
| Ignore repo-root core dumps | `.gitignore` (`/core`, `/core.*`) |
| Offscreen Qt default | `tests/conftest.py` (`QT_QPA_PLATFORM=offscreen`) |
| Makefile test target | `QT_QPA_PLATFORM=offscreen` in `make test` |
| GUI test guide | `doc/dev/gui_testing.md` (updated in PYPOST-429) |

## 5. Recommendations

1. **No code fix** on current HEAD — crash is not reproducible.
2. **If a future segfault occurs**: preserve the dump, run `lldb -c core --batch -o bt`, note
   Python and PySide6 versions, and file a new ticket with the backtrace.
3. **Local hygiene**: delete `core` after investigation; never `git add core`.
4. **Optional future work** (non-blocker): migrate `TestOnRequestError` from `unittest.TestCase`
   to pytest style with the shared `qapp` fixture for consistent QApplication lifecycle.

## 6. Conclusion

The deleted `core` file was a **local native crash artifact** from a manual test session around
`test_tabs_presenter.py`, most likely during or after PYPOST-400 error-handling work. The
underlying defect **does not reproduce** on current HEAD with standard offscreen Qt settings. PYPOST-403
already prevented recurrence via `.gitignore`. This investigation closes the debt item with
documentation only.

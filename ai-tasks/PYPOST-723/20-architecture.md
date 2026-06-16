# PYPOST-723: Architecture

## Approach

Pure documentation change, no code. Added a symptom/cause/fix table to
`doc/dev/testing.md` under a new subsection, derived from:

- `.github/workflows/test.yml` (Ubuntu, Python 3.11/3.13 matrix, Qt/EGL apt packages)
- `pypost/core/curl_generator.py` (`sys.platform == "win32"` branches as an example
  of OS-gated code that legitimately differs in coverage by platform)
- PYPOST-718 (Makefile PYTHON= coupling fix, already merged)
- Existing brief notes in `doc/dev/test_audit.md` § Local vs CI

`test_audit.md` keeps its original brief bullets (historical audit record) and now
links to the detailed table instead of duplicating it.

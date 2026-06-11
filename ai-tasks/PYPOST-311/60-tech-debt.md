# PYPOST-311: Technical Debt Analysis

## Shortcuts Taken

- **Test tooling outside cache key**: pytest, flake8, and pytest-cov are installed via
  unpinned one-liners and are not part of `cache-dependency-path`. Acceptable — they are small
  and change rarely compared to application dependencies.

## Code Quality Issues

- None blocking.

## Missing Tests

- No automated test for GitHub Actions YAML; workflow correctness relies on CI self-validation.

## Performance Concerns

- First run after `requirements.txt` change remains cold-cache (full PyPI download). Expected.
- Unpinned requirements (e.g. `PySide6` without `==`) may resolve to different versions on
  cache hit within the same hash — pre-existing; pinning is out of scope for this task.

## Follow-up Tasks

- **Pin application dependencies** — optional hardening for fully reproducible installs across
  time (separate Debt issue if pursued).
- **requirements-test.txt** — consolidate CI test tooling with its own cache key if install
  time becomes measurable (low priority).

## Blocker Review

**Verdict: SAFE TO CLOSE** — acceptance criteria met; cache keyed on `requirements.txt`,
both CI jobs updated, documentation added, workflow bug fixed.

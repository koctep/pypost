# PYPOST-169: Technical Debt

## Resolved

- **Integration Tests** (PYPOST-23) — live HTTP `/metrics` scrape after `MetricsManager.start_server`.

## Remaining (non-blocker)

- **PYPOST-170** — verify GUI actions increment counters via registry inspection.
- **PYPOST-174** — overlaps partially with PYPOST-177 unit tests; live HTTP now covered here.

## Verdict

**SAFE TO CLOSE** — acceptance criteria met; tests pass with socket bind permissions.

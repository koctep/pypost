# PYPOST-821: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

Used static SVG stroke + QSS path assertions instead of rendered pixel contrast against
native dark tab chrome. Documented in the test: offscreen CI cannot reliably measure that
luminance. This matches acceptance preference for asset/path over pixel checks.

## Code Quality Issues

None introduced. Constants (`DEFAULT_CLOSE_ICON_STROKE`, `LEGACY_LOW_CONTRAST_CLOSE_STROKE`)
encode the contract next to the assertion so the rationale is discoverable.

## Missing Tests

| Scenario | Status |
| --- | --- |
| QSS no `::tab` geometry / close metrics | Already covered |
| Default `close.svg` stroke `#999999` + QSS wiring | Covered (this task) |
| Hover icon visual regression | Unchanged; QSS path sanity only |
| Pixel contrast vs live dark chrome | Not automated — impractical offscreen; optional manual |

## Performance Concerns

None. File read + regex on a tiny SVG and stylesheet.

## Follow-up Tasks

None required for acceptance. Optional later: theme-specific close icons if light/dark
single-colour trade-offs become unacceptable (out of PYPOST-796/821 scope).

## Blocker Review

**SAFE TO CLOSE** — acceptance criteria met; test passes under `make test`; no production
regressions; timeout markers present.

# PYPOST-787: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

- `metrics_otel.py` still uses direct OpenTelemetry imports; no lazy-import guard for missing OTel
  (module is optional at install time, not import-safe without overlay).
- OTel overlay is installed in `make install` for contributor convenience even though production
  `requirements.txt` omits OTel.

## Code Quality Issues

None blocking. Makefile and test dependency-chain checks extended for OTel targets.

## Missing Tests

- No CI job validates `pip install -e ".[otel]"` end-to-end (overlay lock is the CI path).

## Performance Concerns

None. Smaller default production install (fewer packages in `requirements.txt`).

## Follow-up Tasks

### NON-BLOCKER

#### Lazy-import metrics_otel when OTel not installed

- **Priority:** P3
- **Description:** Importing `pypost.core.metrics_otel` fails without OTel packages; acceptable
  today because nothing imports it at app startup.
- **Remediation:** Add optional import guard if a code path begins importing the module
  unconditionally.
- **Jira:** [PYPOST-811](https://pypost.atlassian.net/browse/PYPOST-811)

#### Wire pip install -e ".[otel]" in Makefile

- **Priority:** P3
- **Description:** Makefile uses `requirements-otel.txt` overlay; PEP 621 extra is documented
  but not the primary install path.
- **Remediation:** Consider consolidating when editable install is wired (PYPOST-806).
- **Jira:** [PYPOST-812](https://pypost.atlassian.net/browse/PYPOST-812)

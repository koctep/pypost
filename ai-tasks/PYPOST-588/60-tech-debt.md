# PYPOST-588: Technical Debt Analysis

## Resolution

Follow-up from PYPOST-143. `HTTPClient` and `RequestService` still create local
`TemplateService()` instances when `template_service=None` for test ergonomics. Production
composition in `main.py` always injects a shared instance. Requiring explicit injection in
leaf classes is future hardening, deferred beyond Sprint 577.

## Blocker Review

**Verdict: SAFE TO CLOSE** — documented deferral; production path correct; no code changes required.

## Follow-up Tasks

Revisit in a future sprint when tightening test/production DI boundaries.

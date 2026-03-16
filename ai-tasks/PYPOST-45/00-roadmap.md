# PYPOST-45 Roadmap: Replace `template_service` Global with Constructor Injection

## Steps

- [x] **Analyst** — Gather requirements → `10-requirements.md`
- [x] **Product Owner** — Review `10-requirements.md` for business logic correctness
- [x] **Senior Engineer** — Create architecture plan → `20-architecture.md`
- [x] **Team Lead** — Review `20-architecture.md`
- [x] **Junior Engineer** — Implement code changes per `20-architecture.md`
  - [x] Remove global from `pypost/core/template_service.py`
  - [x] Add injection to `HTTPClient`
  - [x] Add injection to `RequestService`
  - [x] Add injection to `MCPServerImpl`
  - [x] Add new injection-verification tests
  - [x] Code cleanup → `40-code-cleanup.md`
- [x] **Senior Engineer** — Observability review → `50-observability.md`
- [x] **Team Lead** — Tech debt analysis → `60-review.md`
- [x] **Team Lead** — Dev docs → `70-dev-docs.md`
- [x] **Team Lead** — Final commit

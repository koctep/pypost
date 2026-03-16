# PYPOST-44: Roadmap — Replace MetricsManager Singleton with Injection

## Steps

- [x] **Analyst** — Gather requirements, create `10-requirements.md`
- [x] **Product Owner** — Review `10-requirements.md` for business logic correctness
- [x] **Senior Engineer** — Create `20-architecture.md` (design injection chain, identify all
      touch points, plan constructor signature changes)
- [x] **Team Lead** — Review `20-architecture.md`
- [x] **Junior Engineer** — Implement code changes per architecture
  - [x] Remove singleton from `MetricsManager`
  - [x] Update `main.py` to pass instance to `MainWindow`
  - [x] Update `MainWindow` constructor and wiring
  - [x] Update `TabsPresenter` constructor
  - [x] Update `RequestTab`, `RequestWidget`, `ResponseView` constructors
  - [x] Update `HTTPClient` constructor
  - [x] Update `RequestService` constructor
  - [x] Update `MCPServerImpl` constructor
  - [x] Update all tests to inject mock metrics
  - [x] Senior reviews code, Junior iterates
  - [x] Code cleanup (`40-code-cleanup.md`)
- [x] **Senior Engineer** — Observability review (`50-observability.md`)
- [x] **Team Lead** — Tech debt analysis (`60-review.md`), dev docs (`70-dev-docs.md`),
      final commit

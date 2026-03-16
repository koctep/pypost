# PYPOST-43 Roadmap: Decompose MainWindow into Presenters

## Steps

- [x] **Analyst** — gather requirements → `10-requirements.md`
- [x] **Product Owner** — review `10-requirements.md` for business logic correctness
- [x] **Senior Engineer** — create architecture plan → `20-architecture.md`
- [x] **Team Lead** — review `20-architecture.md`
- [x] **Junior Engineer** — implement `CollectionsPresenter`, `TabsPresenter`, `EnvPresenter`;
      refactor `MainWindow` to thin composition
  - [x] Extract `CollectionsPresenter`
  - [x] Extract `TabsPresenter`
  - [x] Extract `EnvPresenter`
  - [x] Slim down `MainWindow` to composition root
  - [x] Code cleanup → `40-code-cleanup.md`
- [x] **Senior Engineer** — add/update observability → `50-observability.md`
- [x] **Team Lead** — tech-debt analysis → `60-review.md`
- [x] **Team Lead** — dev docs → `70-dev-docs.md`
- [x] **Team Lead** — final commit

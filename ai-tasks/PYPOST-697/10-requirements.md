# PYPOST-697: Unify hover TemplateService instance

## Goals

Remove the duplicate module-level `TemplateService` used for hover tooltips so hover expression
rendering shares the composition-root instance from `main.py` (S-TMPL-003 / R-P2-004).

## Definition of Done

- [x] Hover path uses injected composition-root `TemplateService`
- [x] `MainWindow` wires hover at startup
- [x] `RequestWidget.set_template_service` forwards to hover resolver
- [x] Tests pass

## Q&A

| Question | Answer |
| --- | --- |
| Why not remove module default entirely? | Keeps isolated unit tests working until `set_template_service` is called |

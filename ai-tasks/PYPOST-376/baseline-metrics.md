# SOLID Audit Baseline Metrics

**Baseline date:** 2026-06-11

## MainWindow regression guard

| Metric | Audit era (PYPOST-40) | Baseline | Cap |
| --- | ---: | ---: | ---: |
| `main_window.py` file LOC | 1040 | 429 | 435 |
| `MainWindow` class LOC | 1040 | 385 | 390 |

## Module inventory caps

| Module | Audit era LOC | Baseline LOC | Cap |
| --- | ---: | ---: | ---: |
| `pypost/core/http_client.py` | 198 | 332 | 340 |
| `pypost/core/mcp_server_impl.py` | 231 | 283 | 325 |
| `pypost/core/qt/metrics.py` | 286 | 174 | 181 |
| `pypost/core/qt/worker.py` | 57 | 180 | 180 |
| `pypost/core/request_manager.py` | 201 | 260 | 260 |
| `pypost/core/request_service.py` | 95 | 489 | 530 |
| `pypost/core/storage.py` | 80 | 364 | 380 |
| `pypost/core/template_service.py` | 36 | 132 | 225 |
| `pypost/ui/presenters/collections_presenter.py` | — | 328 | 330 |
| `pypost/ui/presenters/env_presenter.py` | — | 470 | 470 |
| `pypost/ui/presenters/tabs_presenter.py` | — | 628 | 785 |
| `pypost/ui/widgets/mixins.py` | — | 386 | 411 |

Regenerate: `.venv/bin/python scripts/audit_baseline_metrics.py --markdown ai-tasks/PYPOST-376/baseline-metrics.md`

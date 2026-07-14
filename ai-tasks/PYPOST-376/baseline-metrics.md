# SOLID Audit Baseline Metrics

**Baseline date:** 2026-06-11

## MainWindow regression guard

| Metric | Audit era (PYPOST-40) | Baseline | Cap |
| --- | ---: | ---: | ---: |
| `main_window.py` file LOC | 1040 | 393 | 425 |
| `MainWindow` class LOC | 1040 | 353 | 380 |

## Module inventory caps

| Module | Audit era LOC | Baseline LOC | Cap |
| --- | ---: | ---: | ---: |
| `pypost/core/http_client.py` | 198 | 327 | 340 |
| `pypost/core/mcp_server_impl.py` | 231 | 273 | 325 |
| `pypost/core/qt/metrics.py` | 286 | 164 | 181 |
| `pypost/core/qt/worker.py` | 57 | 165 | 180 |
| `pypost/core/request_manager.py` | 201 | 259 | 260 |
| `pypost/core/request_service.py` | 95 | 487 | 530 |
| `pypost/core/storage.py` | 80 | 346 | 380 |
| `pypost/core/template_service.py` | 36 | 204 | 225 |
| `pypost/ui/presenters/collections_presenter.py` | — | 275 | 275 |
| `pypost/ui/presenters/env_presenter.py` | — | 448 | 465 |
| `pypost/ui/presenters/tabs_presenter.py` | — | 736 | 785 |
| `pypost/ui/widgets/mixins.py` | — | 373 | 411 |

Regenerate: `.venv/bin/python scripts/audit_baseline_metrics.py --markdown ai-tasks/PYPOST-376/baseline-metrics.md`

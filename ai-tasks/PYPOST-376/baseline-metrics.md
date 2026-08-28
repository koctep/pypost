# SOLID Audit Baseline Metrics

**Baseline date:** 2026-06-11

## MainWindow regression guard

| Metric | Audit era (PYPOST-40) | Baseline | Cap |
| --- | ---: | ---: | ---: |
| `main_window.py` file LOC | 1040 | 456 | 477 |
| `MainWindow` class LOC | 1040 | 408 | 426 |

## Module inventory caps

| Module | Audit era LOC | Baseline LOC | Cap |
| --- | ---: | ---: | ---: |
| `pypost/core/collection_item_dispatch.py` | — | 83 | 83 |
| `pypost/core/http_client.py` | 198 | 381 | 418 |
| `pypost/core/mcp_server_impl.py` | 231 | 314 | 325 |
| `pypost/core/qt/metrics.py` | 286 | 61 | 70 |
| `pypost/core/qt/metrics_tracking.py` | — | 140 | 145 |
| `pypost/core/qt/metrics_websocket.py` | — | 40 | 45 |
| `pypost/core/qt/worker.py` | 57 | 180 | 180 |
| `pypost/core/request_manager.py` | 201 | 250 | 264 |
| `pypost/core/request_service.py` | 95 | 437 | — |
| `pypost/core/storage.py` | 80 | 364 | 380 |
| `pypost/core/template_service.py` | 36 | 212 | 225 |
| `pypost/core/websocket_registry.py` | — | 129 | 131 |
| `pypost/ui/mcp_server_controller.py` | — | 229 | 296 |
| `pypost/ui/presenters/collections_presenter.py` | — | 490 | 535 |
| `pypost/ui/presenters/env_presenter.py` | — | 381 | 432 |
| `pypost/ui/presenters/mcp_controls_presenter.py` | — | 329 | 362 |
| `pypost/ui/presenters/tabs_presenter.py` | — | 1059 | 1165 |
| `pypost/ui/widgets/mixins.py` | — | 396 | 411 |

Regenerate: `.venv/bin/python scripts/audit_baseline_metrics.py --markdown ai-tasks/PYPOST-376/baseline-metrics.md`

# SOLID Audit Baseline Metrics

**Baseline date:** 2026-06-11

## MainWindow regression guard

| Metric | Audit era (PYPOST-40) | Baseline | Cap |
| --- | ---: | ---: | ---: |
| `main_window.py` file LOC | 1040 | 282 | 300 |
| `MainWindow` class LOC | 1040 | 246 | 260 |

## Module inventory caps

| Module | Audit era LOC | Baseline LOC | Cap |
| --- | ---: | ---: | ---: |
| `pypost/core/http_client.py` | 198 | 307 | 340 |
| `pypost/core/mcp_server_impl.py` | 231 | 294 | 325 |
| `pypost/core/metrics.py` | 286 | 150 | 165 |
| `pypost/core/request_manager.py` | 201 | 236 | 260 |
| `pypost/core/request_service.py` | 95 | 481 | 530 |
| `pypost/core/storage.py` | 80 | 342 | 380 |
| `pypost/core/template_service.py` | 36 | 182 | 200 |
| `pypost/core/worker.py` | 57 | 162 | 180 |
| `pypost/ui/presenters/collections_presenter.py` | — | 247 | 275 |
| `pypost/ui/presenters/env_presenter.py` | — | 421 | 465 |
| `pypost/ui/presenters/tabs_presenter.py` | — | 712 | 785 |

Regenerate: `.venv/bin/python scripts/audit_baseline_metrics.py --markdown ai-tasks/PYPOST-376/baseline-metrics.md`

# SOLID Audit Baseline Metrics

**Baseline date:** 2026-06-11

## MainWindow regression guard

| Metric | Audit era (PYPOST-40) | Baseline | Cap |
| --- | ---: | ---: | ---: |
| `main_window.py` file LOC | 1040 | 383 | 425 |
| `MainWindow` class LOC | 1040 | 343 | 380 |

## Module inventory caps

| Module | Audit era LOC | Baseline LOC | Cap |
| --- | ---: | ---: | ---: |
| `pypost/core/http_client.py` | 198 | 322 | 340 |
| `pypost/core/mcp_server_impl.py` | 231 | 235 | 325 |
| `pypost/core/metrics.py` | 286 | 161 | 165 |
| `pypost/core/request_manager.py` | 201 | 247 | 260 |
| `pypost/core/request_service.py` | 95 | 477 | 530 |
| `pypost/core/storage.py` | 80 | 346 | 380 |
| `pypost/core/template_service.py` | 36 | 204 | 225 |
| `pypost/core/worker.py` | 57 | 163 | 180 |
| `pypost/ui/presenters/collections_presenter.py` | — | 247 | 275 |
| `pypost/ui/presenters/env_presenter.py` | — | 448 | 465 |
| `pypost/ui/presenters/tabs_presenter.py` | — | 715 | 785 |

Regenerate: `.venv/bin/python scripts/audit_baseline_metrics.py --markdown ai-tasks/PYPOST-376/baseline-metrics.md`

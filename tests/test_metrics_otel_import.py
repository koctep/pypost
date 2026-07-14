"""Import-safety tests for metrics_otel (PYPOST-811)."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.timeout(30)

_METRICS_OTEL_KEY = "pypost.core.metrics_otel"


def _otel_module_names() -> list[str]:
    return [
        name
        for name in list(sys.modules)
        if name == "opentelemetry" or name.startswith("opentelemetry.")
    ]


def _block_otel_modules() -> dict[str, None]:
    blocked: dict[str, None] = {"opentelemetry": None}
    for name in _otel_module_names():
        blocked[name] = None
    return blocked


@pytest.fixture
def metrics_otel_without_otel() -> ModuleType:
    """Reload metrics_otel with OpenTelemetry blocked; restore after test."""
    saved_modules: dict[str, ModuleType | None] = {}
    keys_to_clear = [_METRICS_OTEL_KEY, *_otel_module_names()]

    for name in keys_to_clear:
        if name in sys.modules:
            saved_modules[name] = sys.modules.pop(name)

    blocked = _block_otel_modules()
    with patch.dict(sys.modules, blocked):
        importlib.invalidate_caches()
        reloaded = importlib.import_module(_METRICS_OTEL_KEY)
        yield reloaded

    for name in [_METRICS_OTEL_KEY, *_otel_module_names()]:
        sys.modules.pop(name, None)
    sys.modules.update(saved_modules)
    importlib.import_module(_METRICS_OTEL_KEY)


def test_metrics_otel_importable_without_otel_packages(metrics_otel_without_otel):
    mod = metrics_otel_without_otel
    assert hasattr(mod, "OtelMetricsTracker")
    assert hasattr(mod, "create_otel_metrics_tracker")


def test_otel_tracker_requires_otel_when_missing(metrics_otel_without_otel):
    mod = metrics_otel_without_otel
    with pytest.raises(ImportError, match="OpenTelemetry dependency is missing"):
        mod.OtelMetricsTracker()


def test_create_otel_metrics_tracker_requires_otel_when_missing(
    metrics_otel_without_otel,
):
    mod = metrics_otel_without_otel
    with pytest.raises(ImportError, match="OpenTelemetry dependency is missing"):
        mod.create_otel_metrics_tracker()

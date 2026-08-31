"""Tests for MetricsTrackerProtocol, NullMetrics, and MetricsManager compliance."""
from __future__ import annotations

import inspect
from collections.abc import Mapping
from typing import Any
from unittest.mock import MagicMock

import pytest

from pypost.core.metrics_otel import OtelMetricsTracker
from pypost.core.metrics_protocol import (
    NULL_METRICS,
    MetricsTrackerProtocol,
    NullMetrics,
    resolve_metrics,
)
from pypost.core.qt.metrics import MetricsManager
from pypost.models.errors import ErrorCategory

pytestmark = pytest.mark.timeout(30)


def _get_protocol_methods(protocol: type) -> dict[str, inspect.Signature]:
    """Extract non-dunder public methods and their callable signatures from a protocol."""
    methods: dict[str, inspect.Signature] = {}
    for name, member in inspect.getmembers(protocol, predicate=callable):
        if name.startswith("_"):
            continue
        methods[name] = inspect.signature(member)
    return methods


def _get_dummy_value(param: inspect.Parameter) -> Any:
    """Generate a valid dummy argument based on parameter type or name."""
    if param.default is not inspect.Parameter.empty:
        return param.default

    annotation = param.annotation
    ann_str = str(annotation)

    if annotation is bool or ann_str == "bool":
        return True
    if annotation is int or ann_str == "int":
        return 1
    if annotation is float or ann_str == "float":
        return 1.0
    if annotation is str or ann_str == "str":
        return "test"
    if annotation is ErrorCategory or "ErrorCategory" in ann_str:
        return ErrorCategory.NETWORK
    if "Mapping" in ann_str or annotation is Mapping:
        return {"test": 1}
    if "None" in ann_str:
        return None

    name = param.name.lower()
    if "count" in name or "bytes" in name:
        return 1
    if "duration" in name:
        return 0.5
    if "ready" in name or "matches" in name:
        return True
    if "counts" in name:
        return {"test": 1}
    if "category" in name:
        return ErrorCategory.NETWORK

    return "test"


def _assert_tracker_satisfies_all_protocol_methods(
    tracker_cls: type,
    protocol: type = MetricsTrackerProtocol,
) -> None:
    protocol_methods = _get_protocol_methods(protocol)
    assert protocol_methods, f"No methods found on {protocol.__name__}"

    missing_methods: list[str] = []
    signature_mismatches: list[str] = []

    for name, proto_sig in protocol_methods.items():
        if not hasattr(tracker_cls, name):
            missing_methods.append(name)
            continue
        impl_member = getattr(tracker_cls, name)
        if not callable(impl_member):
            missing_methods.append(f"{name} (not callable)")
            continue

        impl_sig = inspect.signature(impl_member)
        proto_params = [p for p in proto_sig.parameters.values() if p.name != "self"]
        impl_params = [p for p in impl_sig.parameters.values() if p.name != "self"]

        if len(proto_params) != len(impl_params):
            signature_mismatches.append(
                f"{name}: parameter count mismatch "
                f"(expected {len(proto_params)}, got {len(impl_params)})"
            )
            continue

        for p_proto, p_impl in zip(proto_params, impl_params):
            if p_proto.name != p_impl.name:
                signature_mismatches.append(
                    f"{name}: param name mismatch (expected {p_proto.name}, got {p_impl.name})"
                )
            elif p_proto.kind != p_impl.kind:
                signature_mismatches.append(
                    f"{name}: param '{p_proto.name}' kind mismatch "
                    f"(expected {p_proto.kind}, got {p_impl.kind})"
                )
            elif p_proto.default != p_impl.default:
                signature_mismatches.append(
                    f"{name}: param '{p_proto.name}' default mismatch "
                    f"(expected {p_proto.default}, got {p_impl.default})"
                )

    assert not missing_methods, (
        f"{tracker_cls.__name__} is missing {len(missing_methods)} methods "
        f"from {protocol.__name__}: {missing_methods}"
    )
    assert not signature_mismatches, (
        f"{tracker_cls.__name__} has {len(signature_mismatches)} signature "
        f"mismatches: {signature_mismatches}"
    )


def test_metrics_manager_satisfies_tracker_protocol():
    assert isinstance(MetricsManager(), MetricsTrackerProtocol)


def test_null_metrics_satisfies_tracker_protocol():
    assert isinstance(NullMetrics(), MetricsTrackerProtocol)
    assert isinstance(NULL_METRICS, MetricsTrackerProtocol)


def test_otel_tracker_satisfies_tracker_protocol():
    tracker = OtelMetricsTracker()
    assert isinstance(tracker, MetricsTrackerProtocol)


def test_metrics_manager_satisfies_all_protocol_methods():
    _assert_tracker_satisfies_all_protocol_methods(MetricsManager)


def test_null_metrics_satisfies_all_protocol_methods():
    _assert_tracker_satisfies_all_protocol_methods(NullMetrics)


def test_otel_tracker_satisfies_all_protocol_methods():
    _assert_tracker_satisfies_all_protocol_methods(OtelMetricsTracker)


def test_null_metrics_all_methods_callable_without_error():
    metrics = NullMetrics()
    protocol_methods = _get_protocol_methods(MetricsTrackerProtocol)
    assert len(protocol_methods) >= 40

    for name, sig in protocol_methods.items():
        method = getattr(metrics, name)
        kwargs = {}
        for param in sig.parameters.values():
            if param.name == "self":
                continue
            kwargs[param.name] = _get_dummy_value(param)
        result = method(**kwargs)
        assert result is None, f"{name} on NullMetrics did not return None"


def test_null_metrics_track_methods_are_no_ops():
    metrics = NullMetrics()
    metrics.track_request_sent("GET")
    metrics.track_request_error(ErrorCategory.NETWORK)
    metrics.set_mcp_server_up(True)
    metrics.track_mcp_client_connect("success")
    metrics.track_mcp_client_list_tools("error", "connect")


def test_resolve_metrics_returns_null_metrics_when_none():
    assert resolve_metrics(None) is NULL_METRICS


def test_resolve_metrics_returns_injected_tracker():
    mock = MagicMock(spec=MetricsTrackerProtocol)
    assert resolve_metrics(mock) is mock


def test_magic_mock_can_stand_in_for_tracker_protocol():
    mock = MagicMock(spec=MetricsTrackerProtocol)
    mock.track_request_sent("GET")
    mock.track_request_sent.assert_called_once_with("GET")

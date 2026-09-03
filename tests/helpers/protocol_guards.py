"""Reflection-based guards for runtime-checkable protocol implementations."""
from __future__ import annotations

import inspect

from pypost.core.metrics_protocol import MetricsTrackerProtocol


def _get_protocol_methods(protocol: type) -> dict[str, inspect.Signature]:
    """Extract non-dunder public methods and their callable signatures from a protocol."""
    methods: dict[str, inspect.Signature] = {}
    for name, member in inspect.getmembers(protocol, predicate=callable):
        if name.startswith("_"):
            continue
        methods[name] = inspect.signature(member)
    return methods


def _assert_tracker_satisfies_all_protocol_methods(
    tracker_cls: type,
    protocol: type = MetricsTrackerProtocol,
) -> None:
    """Assert that an implementation exposes every protocol method signature."""
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

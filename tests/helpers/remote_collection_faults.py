"""Fault-injection helpers for remote collection import tests (PYPOST-1426).

Build library-service doubles that simulate network drops, mid-stream TCP resets,
truncated JSON manifests, and malformed variable schemas without live I/O.
"""
from __future__ import annotations

import threading
from typing import Any, Callable
from unittest.mock import MagicMock

from pypost.core.collection_serializer import (
    CollectionSerializationError,
    deserialize_collection_from_json,
)
from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection

# Truncated object mid-variables array (partial JSON manifest).
TRUNCATED_COLLECTION_JSON = '{"name": "PartialRemote", "variables": ['

# Variable name must be a string; int name violates schema.
MALFORMED_VARIABLE_NAME_JSON = (
    '{"name": "BadSchemaRemote", "variables": [{"name": 123, "type": "string"}]}'
)

# Unsupported variable type string.
MALFORMED_VARIABLE_TYPE_JSON = (
    '{"name": "BadTypeRemote",'
    ' "variables": [{"name": "host", "type": "notatype", "default": "x"}]}'
)

BLOCK_BUDGET_S = 5.0


def recovered_collection() -> Collection:
    """Healthy collection returned after a successful retry."""
    return Collection(
        name="RecoveredRemote",
        variables=[
            CollectionVariable(name="recovered_key", type="string", default="recovered_val"),
        ],
    )


def raise_from_truncated_json() -> None:
    """Raise the same serialization error a truncated remote body produces."""
    deserialize_collection_from_json(TRUNCATED_COLLECTION_JSON)


def raise_from_malformed_variable_name() -> None:
    """Raise schema validation failure for a non-string variable name."""
    deserialize_collection_from_json(MALFORMED_VARIABLE_NAME_JSON)


def raise_from_malformed_variable_type() -> None:
    """Raise schema validation failure for an unsupported variable type."""
    deserialize_collection_from_json(MALFORMED_VARIABLE_TYPE_JSON)


def build_library_service(
    *,
    remote_name: str = "FaultyRemote",
    remote_path: str = "cols/faulty.json",
    read_side_effect: Callable[..., Collection] | BaseException | None = None,
) -> MagicMock:
    """Return a library service mock with one remote catalog entry."""
    mock_service = MagicMock()
    conn_mock = MagicMock()
    conn_mock.stable_id = "conn_1"
    conn_mock.name = "Remote Conn"
    mock_service.list_connections.return_value = [conn_mock]
    mock_service.list_manifest_collections.return_value = [
        {"name": remote_name, "path": remote_path},
    ]
    if isinstance(read_side_effect, BaseException):
        mock_service.read_collection.side_effect = read_side_effect
    elif read_side_effect is not None:
        mock_service.read_collection.side_effect = read_side_effect
    return mock_service


def connection_reset_side_effect(
    message: str = "Connection reset by peer mid-stream",
) -> Callable[..., Collection]:
    """Side effect that always raises ConnectionResetError (TCP reset / drop)."""

    def _read(connection_id: str, collection_path: str, **_kwargs: Any) -> Collection:
        raise ConnectionResetError(message)

    return _read


def broken_pipe_side_effect(
    message: str = "Broken pipe during remote collection transfer",
) -> Callable[..., Collection]:
    """Side effect that always raises BrokenPipeError."""

    def _read(connection_id: str, collection_path: str, **_kwargs: Any) -> Collection:
        raise BrokenPipeError(message)

    return _read


def truncated_json_side_effect() -> Callable[..., Collection]:
    """Side effect that raises CollectionSerializationError from truncated JSON."""

    def _read(connection_id: str, collection_path: str, **_kwargs: Any) -> Collection:
        raise_from_truncated_json()
        raise AssertionError("truncated JSON must raise")  # pragma: no cover

    return _read


def malformed_variable_name_side_effect() -> Callable[..., Collection]:
    """Side effect that raises CollectionSerializationError for bad variable name."""

    def _read(connection_id: str, collection_path: str, **_kwargs: Any) -> Collection:
        raise_from_malformed_variable_name()
        raise AssertionError("malformed name must raise")  # pragma: no cover

    return _read


def malformed_variable_type_side_effect() -> Callable[..., Collection]:
    """Side effect that raises CollectionSerializationError for bad variable type."""

    def _read(connection_id: str, collection_path: str, **_kwargs: Any) -> Collection:
        raise_from_malformed_variable_type()
        raise AssertionError("malformed type must raise")  # pragma: no cover

    return _read


def mid_stream_reset_or_abort_side_effect(
    *,
    entered: threading.Event,
    aborted: threading.Event,
    block_budget_s: float = BLOCK_BUDGET_S,
) -> Callable[..., Collection]:
    """Block until transport abort, else raise ConnectionResetError (mid-stream).

    When ``cancellation_token`` is provided, registers ``aborted.set`` as the
    transport-close callback (PYPOST-1425). If abort fires within the budget,
    raises ``OperationCancelledError``. Otherwise raises ``ConnectionResetError``
    to simulate a peer reset after a partial transfer wait.
    """
    from pypost.core.cancellation import OperationCancelledError

    def _read(
        connection_id: str,
        collection_path: str,
        cancellation_token: Any = None,
    ) -> Collection:
        entered.set()
        if cancellation_token is not None:
            cancellation_token.register_callback(aborted.set)
            if aborted.wait(timeout=block_budget_s):
                raise OperationCancelledError("socket closed by abort mid-stream")
        else:
            aborted.wait(timeout=block_budget_s)
        raise ConnectionResetError("Connection reset by peer mid-stream")

    return _read


def fail_then_recover_side_effect(
    first_error: BaseException,
) -> Callable[..., Collection]:
    """Fail once with ``first_error``, then return a healthy collection."""
    attempt = {"n": 0}

    def _read(connection_id: str, collection_path: str, **_kwargs: Any) -> Collection:
        attempt["n"] += 1
        if attempt["n"] == 1:
            raise first_error
        return recovered_collection()

    return _read


def assert_raises_collection_serialization(fn: Callable[[], None]) -> None:
    """Assert helper call raises CollectionSerializationError (suite sanity)."""
    try:
        fn()
    except CollectionSerializationError:
        return
    raise AssertionError("expected CollectionSerializationError")

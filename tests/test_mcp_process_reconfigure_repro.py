"""Behavioral acceptance tests for supervised reconfiguration (PYPOST-1463)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
import logging
from pathlib import Path
import socket
import threading
from typing import Iterator

import anyio
import pytest

from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.mcp_server_runner import ProcessServerRunner, ServerStartSpec
from pypost.models.settings import McpServerConfiguration
from tests.helpers.collection_integration_harness import CollectionVariablesIntegrationHarness
from tests.helpers.port_allocation import EphemeralPortReserve
from tests.test_mcp_process_isolation_repro import (
    _bind_execution_mode,
    _make_collection,
    _upsert_standalone,
)
from tests.test_mcp_server_integration import _mcp_list_tools

pytestmark = pytest.mark.timeout(90)


@dataclass
class RunningPair:
    """Real local endpoints plus an independently resolved replacement runtime."""

    registry: MCPServerRegistry
    target: str
    peer: str
    old: McpServerConfiguration
    replacement: McpServerConfiguration
    ports: list[int]
    completions: list[tuple[str, bool]]


def _tools(port: int) -> list[str]:
    return anyio.run(_mcp_list_tools, f"http://127.0.0.1:{port}/mcp")


def _assert_released(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind(("127.0.0.1", port))


@pytest.fixture
def running_pair(tmp_path: Path) -> Iterator[RunningPair]:
    reserve = EphemeralPortReserve(3)
    ports = reserve.allocate()
    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        _bind_execution_mode(harness, "process")
        registry = harness.registry
        try:
            target = _upsert_standalone(
                harness, index=1, port=ports[0], prefix="reconfigure", tool_name="old_tool"
            )
            peer = _upsert_standalone(
                harness, index=2, port=ports[1], prefix="reconfigure", tool_name="peer_tool"
            )
            registry.start(target)
            registry.start(peer)
            assert registry.wait_for_state(target, "running", timeout=15)
            assert registry.wait_for_state(peer, "running", timeout=15)
            assert _tools(ports[0]) == ["old_tool"]
            assert _tools(ports[1]) == ["peer_tool"]
            old = registry.configuration(target)
            assert old is not None
            harness.create_library(
                manifest_id="replacement-library",
                is_legacy_manifest=False,
                collections_data={
                    "replacement.json": _make_collection("replacement", "replacement_tool")
                },
            )
            replacement = old.model_copy(
                update={
                    "name": "Replacement configuration",
                    "library_id": "replacement-library",
                    "manifest_id": "replacement-library",
                    "library_collection_path": "collections/replacement.json",
                    "port": ports[2],
                },
                deep=True,
            )
            completions: list[tuple[str, bool]] = []
            registry.reconfiguration_finished.connect(
                lambda instance_id, committed: completions.append((instance_id, committed))
            )
            yield RunningPair(registry, target, peer, old, replacement, ports, completions)
        finally:
            registry.stop_all()
            assert reserve.verify_all_rebound(timeout=5)


def _assert_peer_unchanged(pair: RunningPair, previous: ProcessServerRunner) -> None:
    assert pair.registry.runner_for(pair.peer) is previous
    assert pair.registry.status(pair.peer).state == "running"
    assert _tools(pair.ports[1]) == ["peer_tool"]


@pytest.mark.parametrize("same_endpoint", [False, True], ids=["new-endpoint", "same-endpoint"])
def test_process_reconfigure_commits_only_replacement(
    running_pair: RunningPair, same_endpoint: bool, caplog: pytest.LogCaptureFixture
) -> None:
    pair = running_pair
    previous = pair.registry.runner_for(pair.target)
    peer = pair.registry.runner_for(pair.peer)
    assert isinstance(previous, ProcessServerRunner)
    assert isinstance(peer, ProcessServerRunner)
    replacement = pair.replacement.model_copy(
        update={"port": pair.ports[0] if same_endpoint else pair.ports[2]}
    )

    with caplog.at_level(logging.INFO, logger="pypost.core.mcp_server_registry"):
        pair.registry.reconfigure(pair.target, replacement)

    assert (
        f"mcp_registry_process_reconfigured instance_id={pair.target}"
        in caplog.messages
    )

    assert pair.registry.wait_for_state(pair.target, "running", timeout=15)
    accepted = pair.registry.configuration(pair.target)
    assert accepted == replacement
    current = pair.registry.runner_for(pair.target)
    assert isinstance(current, ProcessServerRunner)
    assert current is not previous
    assert not previous.worker_is_alive()
    assert _tools(replacement.port) == ["replacement_tool"]
    assert pair.completions == [(pair.target, True)]
    pair.registry._on_worker_unexpected_exit(previous.worker_id, 1)
    assert pair.registry.status(pair.target).state == "running"
    _assert_peer_unchanged(pair, peer)
    if not same_endpoint:
        _assert_released(pair.ports[0])


@pytest.mark.parametrize("same_endpoint", [False, True], ids=["new-endpoint", "same-endpoint"])
@pytest.mark.parametrize("fail_after_bind", [False, True], ids=["before-bind", "after-bind"])
def test_process_reconfigure_rejects_candidate_and_restores_service(
    running_pair: RunningPair,
    monkeypatch: pytest.MonkeyPatch,
    same_endpoint: bool,
    fail_after_bind: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    pair = running_pair
    peer = pair.registry.runner_for(pair.peer)
    assert isinstance(peer, ProcessServerRunner)
    original_start = ProcessServerRunner.start

    def reject_candidate(runner: ProcessServerRunner, spec: ServerStartSpec) -> None:
        if spec.configuration.name == pair.replacement.name:
            if fail_after_bind:
                original_start(runner, spec)
            raise RuntimeError("secret-candidate-payload-must-not-be-logged")
        original_start(runner, spec)

    monkeypatch.setattr(ProcessServerRunner, "start", reject_candidate)
    replacement = pair.replacement.model_copy(
        update={"port": pair.ports[0] if same_endpoint else pair.ports[2]}
    )

    with caplog.at_level(logging.WARNING, logger="pypost.core.mcp_server_registry"):
        pair.registry.reconfigure(pair.target, replacement)

    assert any(
        message.startswith("mcp_registry_process_reconfigure_rejected ")
        and f"instance_id={pair.target}" in message
        and "restored=True cleaned=True" in message
        for message in caplog.messages
    )
    assert "secret-candidate-payload-must-not-be-logged" not in caplog.text

    assert pair.registry.wait_for_state(pair.target, "running", timeout=15)
    assert pair.registry.configuration(pair.target) == pair.old
    assert _tools(pair.ports[0]) == ["old_tool"]
    assert pair.completions == [(pair.target, False)]
    _assert_peer_unchanged(pair, peer)
    _assert_released(pair.ports[2])


def test_process_reconfigure_reports_failed_restoration(
    running_pair: RunningPair, monkeypatch: pytest.MonkeyPatch
) -> None:
    pair = running_pair
    peer = pair.registry.runner_for(pair.peer)
    assert isinstance(peer, ProcessServerRunner)

    def reject_all_starts(runner: ProcessServerRunner, spec: ServerStartSpec) -> None:
        raise RuntimeError("deterministic startup and restoration failure")

    monkeypatch.setattr(ProcessServerRunner, "start", reject_all_starts)
    replacement = pair.replacement.model_copy(update={"port": pair.ports[0]})

    pair.registry.reconfigure(pair.target, replacement)

    assert pair.registry.wait_for_state(pair.target, "failed", timeout=15)
    assert not pair.registry.is_running(pair.target)
    assert pair.registry.configuration(pair.target) == pair.old
    assert pair.registry.status(pair.target).message
    assert pair.completions == [(pair.target, False)]
    _assert_released(pair.ports[0])
    _assert_released(pair.ports[2])
    _assert_peer_unchanged(pair, peer)


def test_stop_during_process_reconfigure_leaves_no_late_endpoint(
    running_pair: RunningPair, monkeypatch: pytest.MonkeyPatch
) -> None:
    pair = running_pair
    entered = threading.Event()
    release = threading.Event()
    stop_requested = threading.Event()
    original_start = ProcessServerRunner.start

    def hold_candidate(runner: ProcessServerRunner, spec: ServerStartSpec) -> None:
        if spec.configuration.name == pair.replacement.name:
            entered.set()
            assert release.wait(timeout=10)
        original_start(runner, spec)

    def stop_target() -> None:
        stop_requested.set()
        pair.registry.stop(pair.target)

    monkeypatch.setattr(ProcessServerRunner, "start", hold_candidate)
    with ThreadPoolExecutor(max_workers=2) as pool:
        change = pool.submit(pair.registry.reconfigure, pair.target, pair.replacement)
        try:
            if not entered.wait(timeout=5):
                change.result(timeout=5)
                pytest.fail("reconfiguration returned without starting its candidate")
            stopping = pool.submit(stop_target)
            assert stop_requested.wait(timeout=5)
        finally:
            release.set()
        change.result(timeout=20)
        stopping.result(timeout=20)

    assert pair.registry.status(pair.target).state == "stopped"
    assert not pair.registry.is_running(pair.target)
    _assert_released(pair.ports[0])
    _assert_released(pair.ports[2])
    assert _tools(pair.ports[1]) == ["peer_tool"]


def test_concurrent_process_edits_are_serialized(
    running_pair: RunningPair, monkeypatch: pytest.MonkeyPatch
) -> None:
    pair = running_pair
    entered, release, second_requested = threading.Event(), threading.Event(), threading.Event()
    original_start = ProcessServerRunner.start
    first = pair.replacement.model_copy(update={"port": pair.ports[0]})
    second = first.model_copy(update={"name": "Second accepted edit"})

    def hold_first(runner: ProcessServerRunner, spec: ServerStartSpec) -> None:
        if spec.configuration.name == first.name:
            entered.set()
            assert release.wait(timeout=10)
        original_start(runner, spec)

    def edit_again() -> None:
        second_requested.set()
        pair.registry.reconfigure(pair.target, second)

    monkeypatch.setattr(ProcessServerRunner, "start", hold_first)
    with ThreadPoolExecutor(max_workers=2) as pool:
        changing = pool.submit(pair.registry.reconfigure, pair.target, first)
        try:
            assert entered.wait(timeout=5)
            editing = pool.submit(edit_again)
            assert second_requested.wait(timeout=5)
            with pytest.raises(TimeoutError):
                editing.result(timeout=0.2)
        finally:
            release.set()
        changing.result(timeout=20)
        editing.result(timeout=20)
    assert pair.registry.configuration(pair.target) == second
    assert _tools(pair.ports[0]) == ["replacement_tool"]


@pytest.mark.parametrize("operation", ["clear", "restore_snapshot"])
def test_failed_cleanup_preserves_state_until_retry(
    running_pair: RunningPair, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    pair = running_pair
    runner = pair.registry.runner_for(pair.target)
    assert isinstance(runner, ProcessServerRunner)
    original_stop = runner.stop
    monkeypatch.setattr(runner, "stop", lambda: False)
    pair.registry._process_cleanup[pair.target] = [runner]
    action = (
        pair.registry.clear
        if operation == "clear" else lambda: pair.registry.restore_snapshot({})
    )

    with pytest.raises(RuntimeError, match="cleanup remains pending"):
        action()
    assert pair.registry.configuration(pair.target) == pair.old
    assert _tools(pair.ports[0]) == ["old_tool"]

    monkeypatch.setattr(runner, "stop", original_stop)
    action()
    assert pair.registry.configuration(pair.target) is None
    assert not runner.worker_is_alive()
    assert not pair.registry._process_cleanup


def test_stop_all_retries_cleanup_only_worker(
    running_pair: RunningPair,
) -> None:
    pair = running_pair
    runner = pair.registry.runner_for(pair.target)
    assert isinstance(runner, ProcessServerRunner)
    pair.registry._process_cleanup[pair.target] = [runner]
    pair.registry._runners.pop(pair.target)
    pair.registry._configurations.pop(pair.target)
    pair.registry.stop_all()
    assert not runner.worker_is_alive()
    assert not pair.registry._process_cleanup
    _assert_released(pair.ports[0])

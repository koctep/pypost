"""PYPOST-860: agent e2e failure artifact dump helper + hook wiring."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget

from pypost.agent.lifecycle import AgentAppSession, set_agent_session_failure_dump_hook
from pypost.agent.ui_snapshot import capture_ui_snapshot
from pypost.core.sensitive_text_sanitizer import HIDDEN_PLACEHOLDER
from pypost.fixtures.agent_e2e_failure import (
    dump_agent_e2e_failure_artifacts,
    make_direct_session_failure_dump_hook,
    resolve_artifact_root,
    safe_nodeid_dirname,
    session_from_funcargs,
)

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]


class _FakeEnv:
    def __init__(
        self,
        variables: dict[str, str] | None = None,
        hidden_keys: set[str] | None = None,
    ) -> None:
        self._variables = dict(variables or {})
        self._hidden_keys = set(hidden_keys or ())

    @property
    def current_variables(self) -> dict[str, str]:
        return dict(self._variables)

    @property
    def current_hidden_keys(self) -> set[str]:
        return set(self._hidden_keys)


def _find_by_name(node: dict[str, Any], name: str) -> dict[str, Any] | None:
    if node.get("name") == name:
        return node
    for child in node.get("children") or []:
        if isinstance(child, dict):
            found = _find_by_name(child, name)
            if found is not None:
                return found
    return None


def test_safe_nodeid_dirname_is_filesystem_safe() -> None:
    name = safe_nodeid_dirname("tests/test_x.py::test_y[a/b]")
    assert "/" not in name
    assert ":" not in name
    assert name


def test_resolve_artifact_root_default_and_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = resolve_artifact_root(tmp_path)
    assert root == tmp_path / "artifacts" / "agent_e2e"

    override = tmp_path / "custom_dumps"
    monkeypatch.setenv("PYPOST_AGENT_E2E_ARTIFACTS", str(override))
    assert resolve_artifact_root(tmp_path) == override


def test_dump_writes_snapshot_and_diagnostics(
    tmp_path: Path,
    agent_e2e_session: AgentAppSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    session = agent_e2e_session
    nodeid = "tests/test_agent_e2e_failure_artifacts.py::test_dump"
    with caplog.at_level(logging.INFO, logger="pypost.fixtures.agent_e2e_failure"):
        dump_dir = dump_agent_e2e_failure_artifacts(
            session,
            nodeid=nodeid,
            exc_type="AssertionError",
            exc_message="expected UI state",
            session_fixture="agent_e2e_session",
            artifact_root=tmp_path,
        )
    assert dump_dir is not None
    snap_path = dump_dir / "ui_snapshot.json"
    diag_path = dump_dir / "diagnostics.json"
    assert snap_path.is_file()
    assert diag_path.is_file()

    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    assert snap["role"] == "window"
    assert isinstance(snap["children"], list)

    diag = json.loads(diag_path.read_text(encoding="utf-8"))
    assert diag["nodeid"] == nodeid
    assert diag["exc_type"] == "AssertionError"
    assert diag["exc_message"] == "expected UI state"
    assert diag["session_fixture"] == "agent_e2e_session"
    assert diag["ui_ready"] is True
    assert "agent_e2e_failure_artifacts_written" in caplog.text


def test_dump_snapshot_reuses_masking(
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    """Hidden env values in the dumped snapshot stay masked."""
    assert QApplication.instance() is qapp
    secret = "super-secret-token-xyz"
    root = QWidget()
    root.env = _FakeEnv(  # type: ignore[attr-defined]
        variables={"api_key": secret},
        hidden_keys={"api_key"},
    )
    layout = QVBoxLayout(root)
    edit = QLineEdit(f"Authorization: Bearer {secret}")
    edit.setObjectName("secret_edit")
    layout.addWidget(edit)
    root.show()
    qapp.processEvents()

    # Prove capture path masks; dump uses the same session.ui_snapshot API.
    direct = capture_ui_snapshot(root)
    node = _find_by_name(direct, "secret_edit")
    assert node is not None
    assert secret not in (node["value"] or "")
    assert HIDDEN_PLACEHOLDER in (node["value"] or "")

    session = MagicMock(spec=AgentAppSession)
    session.ui_snapshot.return_value = direct
    session.window.is_ui_ready = True

    dump_dir = dump_agent_e2e_failure_artifacts(
        session,
        nodeid="masking_case",
        artifact_root=tmp_path,
    )
    assert dump_dir is not None
    written = json.loads((dump_dir / "ui_snapshot.json").read_text(encoding="utf-8"))
    written_node = _find_by_name(written, "secret_edit")
    assert written_node is not None
    assert secret not in (written_node["value"] or "")
    assert secret not in (dump_dir / "ui_snapshot.json").read_text(encoding="utf-8")


def test_dump_best_effort_on_capture_error(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    session = MagicMock(spec=AgentAppSession)
    session.ui_snapshot.side_effect = RuntimeError("boom")
    with caplog.at_level(
        logging.WARNING,
        logger="pypost.fixtures.agent_e2e_failure",
    ):
        dump_dir = dump_agent_e2e_failure_artifacts(
            session,
            nodeid="failing_capture",
            artifact_root=tmp_path,
        )
    assert dump_dir is None
    assert "agent_e2e_failure_artifacts_failed" in caplog.text


def test_dump_propagates_unexpected_exception(tmp_path: Path) -> None:
    """PYPOST-876: unexpected dump errors must not be swallowed as dump-failed.

    LookupError is outside the intentional best-effort catalogue
    (OSError, RuntimeError, TypeError, ValueError, AttributeError).
    """
    session = MagicMock(spec=AgentAppSession)
    session.ui_snapshot.side_effect = LookupError("unexpected dump bug")
    with pytest.raises(LookupError, match="unexpected dump bug"):
        dump_agent_e2e_failure_artifacts(
            session,
            nodeid="unexpected_dump_error",
            artifact_root=tmp_path,
        )


def test_session_from_funcargs_prefers_seeded() -> None:
    blank = MagicMock(spec=AgentAppSession)
    seeded = MagicMock(spec=AgentAppSession)
    resolved = session_from_funcargs(
        {
            "agent_e2e_session": blank,
            "seeded_agent_e2e_session": seeded,
        }
    )
    assert resolved is not None
    assert resolved[0] is seeded
    assert resolved[1] == "seeded_agent_e2e_session"
    assert session_from_funcargs({}) is None


def test_makereport_hook_dumps_on_fixture_assert_fail(
    tmp_path: Path,
) -> None:
    """Subprocess: failing agent_e2e_session test writes artifact files."""
    import os
    import subprocess
    import sys

    probe = tmp_path / "test_probe_fail.py"
    probe.write_text(
        "\n".join(
            [
                "import pytest",
                "pytestmark = [",
                "    pytest.mark.timeout(60),",
                "    pytest.mark.agent_e2e,",
                "]",
                "",
                "def test_probe_intentional_fail(agent_e2e_session):",
                "    assert agent_e2e_session.window.is_ui_ready is True",
                '    assert False, "intentional failure for artifact dump"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    artifact_root = tmp_path / "hook_artifacts"
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYPOST_AGENT_E2E_ARTIFACTS"] = str(artifact_root)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(probe),
            "-p",
            "no:cacheprovider",
            "-p",
            "tests._pytest_plugins.agent_e2e",
            "-q",
            "--tb=line",
            "-o",
            "markers=agent_e2e: agent e2e\ntimeout: per-test timeout",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    snaps = list(artifact_root.rglob("ui_snapshot.json"))
    diags = list(artifact_root.rglob("diagnostics.json"))
    assert snaps, result.stdout + result.stderr
    assert diags
    diag = json.loads(diags[0].read_text(encoding="utf-8"))
    assert diag["exc_type"] == "AssertionError"
    assert diag["session_fixture"] == "agent_e2e_session"
    assert "intentional failure" in (diag["exc_message"] or "")


def test_dump_hook_failure_logs_warning(
    qapp: QApplication,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """PYPOST-912: raising dump hook logs agent_session_failure_dump_hook_failed."""
    assert QApplication.instance() is qapp

    def _failing_hook(
        _session: AgentAppSession,
        _exc_type: type[BaseException],
        _exc: BaseException,
    ) -> None:
        raise RuntimeError("hook boom")

    set_agent_session_failure_dump_hook(_failing_hook)
    try:
        with caplog.at_level(logging.WARNING, logger="pypost.agent.lifecycle"):
            with pytest.raises(AssertionError, match="intentional dump hook caplog"):
                with AgentAppSession(offscreen=True, ready_timeout=30.0) as session:
                    assert session.window.is_ui_ready is True
                    assert False, "intentional dump hook caplog"
        assert "agent_session_failure_dump_hook_failed error=RuntimeError" in caplog.text
    finally:
        set_agent_session_failure_dump_hook(make_direct_session_failure_dump_hook())


def test_dumps_on_direct_session_assert_fail(
    tmp_path: Path,
) -> None:
    """PYPOST-875: direct AgentAppSession fail writes artifact files.

    Bare ``with AgentAppSession(...)`` inside the test body dumps the same
    snapshot + diagnostics as fixture-backed tests (plugin ``__exit__`` hook).
    """
    import os
    import subprocess
    import sys

    probe = tmp_path / "test_probe_direct_fail.py"
    probe.write_text(
        "\n".join(
            [
                "import pytest",
                "from pypost.agent.lifecycle import AgentAppSession",
                "pytestmark = [",
                "    pytest.mark.timeout(60),",
                "    pytest.mark.agent_e2e,",
                "]",
                "",
                "def test_probe_direct_intentional_fail():",
                "    with AgentAppSession(offscreen=True, ready_timeout=30.0) as session:",
                "        assert session.window.is_ui_ready is True",
                '        assert False, "intentional direct failure for artifact dump"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    artifact_root = tmp_path / "direct_hook_artifacts"
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYPOST_AGENT_E2E_ARTIFACTS"] = str(artifact_root)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(probe),
            "-p",
            "no:cacheprovider",
            "-p",
            "tests._pytest_plugins.agent_e2e",
            "-q",
            "--tb=line",
            "-o",
            "markers=agent_e2e: agent e2e\ntimeout: per-test timeout",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    snaps = list(artifact_root.rglob("ui_snapshot.json"))
    diags = list(artifact_root.rglob("diagnostics.json"))
    assert snaps, result.stdout + result.stderr
    assert diags
    diag = json.loads(diags[0].read_text(encoding="utf-8"))
    assert diag["exc_type"] == "AssertionError"
    assert diag["session_fixture"] == "direct"
    assert "intentional direct failure" in (diag["exc_message"] or "")

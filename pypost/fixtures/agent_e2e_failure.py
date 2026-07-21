"""On-disk failure artifacts for agent e2e (PYPOST-860).

Writes a masked UI snapshot plus concise diagnostics when a scenario fails.
Reuse ``AgentAppSession.ui_snapshot()`` so secrets follow PYPOST-835 masking.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from pypost.agent.lifecycle import AgentAppSession

logger = logging.getLogger(__name__)

DEFAULT_ARTIFACT_RELATIVE = Path("artifacts") / "agent_e2e"
ENV_ARTIFACT_ROOT = "PYPOST_AGENT_E2E_ARTIFACTS"
MAX_EXC_MESSAGE_LENGTH = 500
_SESSION_FIXTURE_NAMES = (
    "seeded_agent_e2e_session",
    "agent_e2e_session",
)


def resolve_artifact_root(rootpath: Path | None = None) -> Path:
    """Return the artifact root (env override or ``artifacts/agent_e2e``)."""
    override = os.environ.get(ENV_ARTIFACT_ROOT, "").strip()
    if override:
        path = Path(override)
        return path if path.is_absolute() else Path.cwd() / path
    base = rootpath if rootpath is not None else Path.cwd()
    return Path(base) / DEFAULT_ARTIFACT_RELATIVE


def safe_nodeid_dirname(nodeid: str) -> str:
    """Filesystem-safe directory name derived from a pytest nodeid."""
    cleaned = re.sub(r"[^\w.\-]+", "_", nodeid.strip())
    cleaned = cleaned.strip("._") or "unknown_test"
    return cleaned[:180]


def dump_agent_e2e_failure_artifacts(
    session: AgentAppSession,
    *,
    nodeid: str,
    exc_type: str | None = None,
    exc_message: str | None = None,
    session_fixture: str | None = None,
    artifact_root: Path | None = None,
) -> Path | None:
    """Write ``ui_snapshot.json`` + ``diagnostics.json``; return dump dir.

    Best-effort: capture or I/O errors are logged and return ``None`` so the
    original test failure remains the primary outcome.
    """
    root = artifact_root if artifact_root is not None else resolve_artifact_root()
    dump_dir = root / safe_nodeid_dirname(nodeid)
    try:
        dump_dir.mkdir(parents=True, exist_ok=True)
        snapshot = session.ui_snapshot()
        diagnostics = _build_diagnostics(
            session,
            nodeid=nodeid,
            exc_type=exc_type,
            exc_message=exc_message,
            session_fixture=session_fixture,
        )
        _write_json(dump_dir / "ui_snapshot.json", snapshot)
        _write_json(dump_dir / "diagnostics.json", diagnostics)
    except Exception as exc:  # noqa: BLE001 — never mask the test failure
        logger.warning(
            "agent_e2e_failure_artifacts_failed nodeid=%s error=%s",
            nodeid,
            type(exc).__name__,
        )
        return None

    logger.info(
        "agent_e2e_failure_artifacts_written path=%s nodeid=%s",
        dump_dir,
        nodeid,
    )
    return dump_dir


def session_from_funcargs(funcargs: dict[str, Any]) -> tuple[AgentAppSession, str] | None:
    """Return ``(session, fixture_name)`` from pytest item funcargs, if any."""
    for name in _SESSION_FIXTURE_NAMES:
        value = funcargs.get(name)
        if isinstance(value, AgentAppSession):
            return value, name
    return None


def _build_diagnostics(
    session: AgentAppSession,
    *,
    nodeid: str,
    exc_type: str | None,
    exc_message: str | None,
    session_fixture: str | None,
) -> dict[str, Any]:
    message = exc_message or ""
    if len(message) > MAX_EXC_MESSAGE_LENGTH:
        message = message[:MAX_EXC_MESSAGE_LENGTH] + "…"
    ui_ready: bool | None
    try:
        ui_ready = bool(session.window.is_ui_ready)
    except Exception:  # noqa: BLE001 — session may be half-torn
        ui_ready = None
    return {
        "nodeid": nodeid,
        "exc_type": exc_type,
        "exc_message": message or None,
        "session_fixture": session_fixture,
        "ui_ready": ui_ready,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

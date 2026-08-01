"""On-disk failure artifacts for agent e2e (PYPOST-860 / 875 / 876).

Writes a masked UI snapshot plus concise diagnostics when a scenario fails.
Reuse ``AgentAppSession.ui_snapshot()`` so secrets follow PYPOST-835 masking.
Direct ``AgentAppSession`` constructions dump via an optional ``__exit__``
hook installed by the agent e2e pytest plugin (PYPOST-875).
Dump I/O uses a narrowed best-effort exception tuple (PYPOST-876).
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Callable
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from pypost.agent.e2e_dump_errors import DUMP_BEST_EFFORT_ERRORS
from pypost.agent.lifecycle import AgentAppSession

logger = logging.getLogger(__name__)

DEFAULT_ARTIFACT_RELATIVE = Path("artifacts") / "agent_e2e"
ENV_ARTIFACT_ROOT = "PYPOST_AGENT_E2E_ARTIFACTS"
DIRECT_SESSION_PROVENANCE = "direct"
MAX_EXC_MESSAGE_LENGTH = 500
_SESSION_FIXTURE_NAMES = (
    "seeded_agent_e2e_session",
    "agent_e2e_session",
)

_current_failure_nodeid: ContextVar[str | None] = ContextVar(
    "agent_e2e_failure_nodeid",
    default=None,
)
_current_artifact_root: ContextVar[Path | None] = ContextVar(
    "agent_e2e_failure_artifact_root",
    default=None,
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
    session_source: str | None = None,
    artifact_root: Path | None = None,
) -> Path | None:
    """Write ``ui_snapshot.json`` + ``diagnostics.json``; return dump dir.

    Best-effort for ``DUMP_BEST_EFFORT_ERRORS`` (I/O, capture, half-torn
    reads): those are logged and return ``None`` so the original test
    failure remains the primary outcome. Other exceptions propagate.
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
            session_source=session_source,
        )
        _write_json(dump_dir / "ui_snapshot.json", snapshot)
        _write_json(dump_dir / "diagnostics.json", diagnostics)
    except DUMP_BEST_EFFORT_ERRORS as exc:
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


def set_failure_dump_context(
    *,
    nodeid: str | None,
    artifact_root: Path | None = None,
) -> None:
    """Bind pytest nodeid / root for direct-session ``__exit__`` dumps."""
    _current_failure_nodeid.set(nodeid)
    _current_artifact_root.set(artifact_root)


def clear_failure_dump_context() -> None:
    """Clear per-test dump context after the item finishes."""
    _current_failure_nodeid.set(None)
    _current_artifact_root.set(None)


def make_direct_session_failure_dump_hook() -> (
    Callable[[AgentAppSession, type[BaseException], BaseException], None]
):
    """Return a hook that dumps artifacts for direct ``AgentAppSession`` exits."""

    def _hook(
        session: AgentAppSession,
        exc_type: type[BaseException],
        exc: BaseException,
    ) -> None:
        nodeid = _current_failure_nodeid.get() or "unknown_test"
        root = _current_artifact_root.get()
        dump_agent_e2e_failure_artifacts(
            session,
            nodeid=nodeid,
            exc_type=exc_type.__name__,
            exc_message=str(exc),
            session_source=DIRECT_SESSION_PROVENANCE,
            artifact_root=root,
        )

    return _hook


def _build_diagnostics(
    session: AgentAppSession,
    *,
    nodeid: str,
    exc_type: str | None,
    exc_message: str | None,
    session_source: str | None,
) -> dict[str, Any]:
    message = exc_message or ""
    if len(message) > MAX_EXC_MESSAGE_LENGTH:
        message = message[:MAX_EXC_MESSAGE_LENGTH] + "…"
    ui_ready: bool | None
    try:
        ui_ready = bool(session.window.is_ui_ready)
    except DUMP_BEST_EFFORT_ERRORS:
        ui_ready = None
    return {
        "nodeid": nodeid,
        "exc_type": exc_type,
        "exc_message": message or None,
        "session_source": session_source,
        "ui_ready": ui_ready,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

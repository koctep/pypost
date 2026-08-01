"""PYPOST-923: lock make-install-smoke Qt/EGL apt parity with peer jobs."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "test.yml"

# Peer Qt/EGL set from jobs `test` and `agent-e2e` (full equality required).
_PEER_QT_EGL_PACKAGES: frozenset[str] = frozenset(
    {
        "libdbus-1-3",
        "libegl1",
        "libfontconfig1",
        "libfreetype6",
        "libglib2.0-0",
        "libgl1",
        "libxcb-cursor0",
        "libxkbcommon0",
    }
)

_QT_STEP_NAME = "Install Qt / EGL runtime"


def _job_block(workflow_text: str, job_id: str) -> str:
    """Return the named job YAML block (until next top-level job)."""
    marker = f"\n  {job_id}:"
    start = workflow_text.find(marker)
    if start < 0:
        alt = f"  {job_id}:"
        start = workflow_text.find(alt)
        if start < 0:
            pytest.fail(
                f"{_WORKFLOW.relative_to(_REPO_ROOT)}: missing job {job_id}"
            )
        start = workflow_text.rfind("\n", 0, start) + 1
    else:
        start += 1  # skip leading newline so block starts at "  {job_id}:"
    rest = workflow_text[start:]
    lines = rest.splitlines(keepends=True)
    collected: list[str] = [lines[0]]
    for line in lines[1:]:
        if line.startswith("  ") and not line.startswith("   "):
            if line.strip().endswith(":") and not line.strip().startswith("#"):
                key = line.strip()[:-1]
                if key and " " not in key and key != job_id:
                    break
        collected.append(line)
    return "".join(collected)


def _apt_packages_in_block(job_block: str) -> frozenset[str]:
    """Extract package names from apt-get install lines in a job block."""
    found: set[str] = set()
    for line in job_block.splitlines():
        stripped = line.strip().rstrip("\\").strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Match standalone package tokens (e.g. libegl1) on apt install lines.
        if re.fullmatch(r"[a-z0-9][a-z0-9+._-]*", stripped):
            if stripped.startswith("lib") or stripped in _PEER_QT_EGL_PACKAGES:
                found.add(stripped)
    return frozenset(found)


def test_make_install_smoke_job_exists() -> None:
    """Workflow must define the make-install-smoke job."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    _job_block(text, "make-install-smoke")


def test_make_install_smoke_has_full_peer_qt_egl_apt_set() -> None:
    """Smoke job must install the full peer Qt/EGL apt package set.

    Parity with jobs ``test`` and ``agent-e2e``: equality / full copy, not a
    subset. Without these packages, shared conftest PySide6 import fails
    collection under QT_QPA_PLATFORM=offscreen.
    """
    text = _WORKFLOW.read_text(encoding="utf-8")
    peer_block = _job_block(text, "agent-e2e")
    smoke_block = _job_block(text, "make-install-smoke")

    peer_pkgs = _apt_packages_in_block(peer_block) & _PEER_QT_EGL_PACKAGES
    assert peer_pkgs == _PEER_QT_EGL_PACKAGES, (
        f"Peer agent-e2e missing expected Qt/EGL packages: "
        f"{sorted(_PEER_QT_EGL_PACKAGES - peer_pkgs)}"
    )

    if _QT_STEP_NAME not in smoke_block:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job make-install-smoke: "
            f"missing step {_QT_STEP_NAME!r} (PySide6 headless runtime)"
        )

    smoke_pkgs = _apt_packages_in_block(smoke_block) & _PEER_QT_EGL_PACKAGES
    missing = _PEER_QT_EGL_PACKAGES - smoke_pkgs
    if missing:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job make-install-smoke: "
            f"Qt/EGL apt package set must equal peer test/agent-e2e set; "
            f"missing: {sorted(missing)}"
        )

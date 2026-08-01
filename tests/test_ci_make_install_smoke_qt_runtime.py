"""PYPOST-923/924: Qt/EGL apt parity and shared composite contract."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "test.yml"
_QT_EGL_COMPOSITE_ACTION = (
    _REPO_ROOT / ".github" / "actions" / "install-qt-egl-runtime" / "action.yml"
)
_QT_EGL_COMPOSITE_USES = "./.github/actions/install-qt-egl-runtime"
_QT_USING_JOBS = ("test", "make-install-smoke", "agent-e2e")

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


def _count_inline_libegl1_apt_install_blocks(workflow_text: str) -> int:
    """Return count of inline run blocks with apt-get install listing libegl1."""
    count = 0
    for match in re.finditer(r"run:\s*\|\s*\n((?:          .*\n)*)", workflow_text):
        block = match.group(1)
        if "sudo apt-get install" in block and "libegl1" in block:
            count += 1
    return count


def test_install_qt_egl_composite_action_exists_with_full_package_set() -> None:
    """Composite action must exist, be composite, and install the eight packages."""
    rel = _QT_EGL_COMPOSITE_ACTION.relative_to(_REPO_ROOT)
    if not _QT_EGL_COMPOSITE_ACTION.is_file():
        pytest.fail(f"Missing composite action {rel}")

    text = _QT_EGL_COMPOSITE_ACTION.read_text(encoding="utf-8")
    if "using: composite" not in text:
        pytest.fail(f"{rel}: runs.using must be composite")

    pkgs = _apt_packages_in_block(text) & _PEER_QT_EGL_PACKAGES
    missing = _PEER_QT_EGL_PACKAGES - pkgs
    extra = pkgs - _PEER_QT_EGL_PACKAGES
    if missing or extra:
        pytest.fail(
            f"{rel}: apt install must list exactly _PEER_QT_EGL_PACKAGES; "
            f"missing={sorted(missing)} extra={sorted(extra)}"
        )


def test_qt_using_jobs_reference_install_qt_egl_composite() -> None:
    """Jobs test, make-install-smoke, and agent-e2e must use the composite."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    missing_jobs: list[str] = []
    for job_id in _QT_USING_JOBS:
        block = _job_block(text, job_id)
        if _QT_EGL_COMPOSITE_USES not in block:
            missing_jobs.append(job_id)
    if missing_jobs:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)}: jobs {missing_jobs} must "
            f"contain uses: {_QT_EGL_COMPOSITE_USES!r}"
        )


def test_workflow_has_zero_inline_libegl1_apt_install_blocks() -> None:
    """test.yml must contain zero inline apt-get install blocks listing libegl1."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    count = _count_inline_libegl1_apt_install_blocks(text)
    if count != 0:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} must contain zero inline "
            f"apt-get install blocks listing libegl1; found {count}"
        )


def test_make_install_smoke_job_exists() -> None:
    """Workflow must define the make-install-smoke job."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    _job_block(text, "make-install-smoke")


def _composite_qt_egl_packages() -> frozenset[str]:
    """Return Qt/EGL package names from the shared composite action."""
    if not _QT_EGL_COMPOSITE_ACTION.is_file():
        pytest.fail(f"Missing composite action {_QT_EGL_COMPOSITE_ACTION.relative_to(_REPO_ROOT)}")
    text = _QT_EGL_COMPOSITE_ACTION.read_text(encoding="utf-8")
    return _apt_packages_in_block(text) & _PEER_QT_EGL_PACKAGES


def test_make_install_smoke_has_full_peer_qt_egl_apt_set() -> None:
    """Smoke job must use the composite with the full peer Qt/EGL apt set.

    Parity with jobs ``test`` and ``agent-e2e``: all three reference the same
    composite action whose package list equals _PEER_QT_EGL_PACKAGES. Without
    these packages, shared conftest PySide6 import fails collection under
    QT_QPA_PLATFORM=offscreen.
    """
    text = _WORKFLOW.read_text(encoding="utf-8")
    smoke_block = _job_block(text, "make-install-smoke")
    peer_block = _job_block(text, "agent-e2e")

    if _QT_EGL_COMPOSITE_USES not in smoke_block:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job make-install-smoke: "
            f"must use composite {_QT_EGL_COMPOSITE_USES!r} "
            f"(PySide6 headless runtime)"
        )

    if _QT_EGL_COMPOSITE_USES not in peer_block:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job agent-e2e: "
            f"must use composite {_QT_EGL_COMPOSITE_USES!r} for peer parity"
        )

    composite_pkgs = _composite_qt_egl_packages()
    missing = _PEER_QT_EGL_PACKAGES - composite_pkgs
    if missing:
        pytest.fail(
            f"{_QT_EGL_COMPOSITE_ACTION.relative_to(_REPO_ROOT)}: "
            f"Qt/EGL apt package set must equal peer set; "
            f"missing: {sorted(missing)}"
        )

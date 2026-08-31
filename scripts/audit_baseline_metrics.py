#!/usr/bin/env python3
"""Measure SOLID audit regression baseline metrics (PYPOST-376)."""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path

BASELINE_DATE = "2026-06-11"
REPO_ROOT = Path(__file__).resolve().parents[1]

# Audit-era snapshot from ai-tasks/PYPOST-40/30-audit-report.md (2026-03).
AUDIT_ERA_LOC: dict[str, int] = {
    "pypost/ui/main_window.py": 1040,
    "pypost/core/qt/metrics.py": 286,
    "pypost/core/template_service.py": 36,
    "pypost/core/request_service.py": 95,
    "pypost/core/request_manager.py": 201,
    "pypost/core/http_client.py": 198,
    "pypost/core/storage.py": 80,
    "pypost/core/qt/worker.py": 57,
    "pypost/core/mcp_server_impl.py": 231,
}

# Regression caps: measured 2026-06-11 + ~10% headroom (see baseline-metrics.md).
FILE_CAPS: dict[str, int] = {
    # PYPOST-1071: PYPOST-1044's multi-server persistence and lifecycle control moved to
    # pypost/ui/mcp_server_controller.py; cap re-derived from the post-extraction
    # measurement (433) rather than from the oversized pre-extraction structure.
    "pypost/ui/main_window.py": 477,
    # PYPOST-1071: extraction target for the MCP persistence and lifecycle code moved out
    # of main_window.py; capped on creation at the ~10% headroom policy (269 measured)
    # so the relocated lines stay measured instead of growing outside the guard.
    "pypost/ui/mcp_server_controller.py": 296,
    # PYPOST-987/PYPOST-989: import/export workflows remain delegated to action
    # objects; PYPOST-1025 extracted their panel assembly to collections_panel.py.
    # PYPOST-1071: accepted thin delegation — PYPOST-1005/1012/1013 added thin collection
    # action entry points and busy-cue coordination and PYPOST-1044 added the read-only
    # collection_by_id() lookup, so no action-object algorithm was absorbed here.
    # PYPOST-1194: intentional presenter growth — re-derived from measured 486 + ~10%
    # headroom (ceil(486 * 1.10) = 535).
    "pypost/ui/presenters/collections_presenter.py": 535,
    # PYPOST-1194: intentional presenter growth — re-derived from measured 1059 + ~10%
    # headroom (ceil(1059 * 1.10) = 1165). Prefer further extraction into
    # tabs_presenter_* helpers before raising again.
    "pypost/ui/presenters/tabs_presenter.py": 1165,
    # PYPOST-1071: MCP status controls, dialogs and scoped refresh routing moved to
    # pypost/ui/presenters/mcp_controls_presenter.py; cap re-derived from 392.
    "pypost/ui/presenters/env_presenter.py": 432,
    # PYPOST-1071: extraction target for the MCP controls moved out of env_presenter.py;
    # capped on creation at the ~10% headroom policy (329 measured) so the relocated
    # lines stay measured instead of growing outside the guard.
    "pypost/ui/presenters/mcp_controls_presenter.py": 362,
    # PYPOST-1146: tracking delegation split into metrics_tracking.py and
    # metrics_websocket.py; metrics.py cap re-derived from post-extraction measurement (61).
    "pypost/core/qt/metrics.py": 70,
    # PYPOST-1146: non-WebSocket explicit delegation mixin; capped at ~10% headroom (130 measured).
    "pypost/core/qt/metrics_tracking.py": 145,
    # PYPOST-1146: WebSocket explicit delegation mixin; capped at ~10% headroom (40 measured).
    "pypost/core/qt/metrics_websocket.py": 45,
    "pypost/ui/widgets/mixins.py": 411,
    # PYPOST-1111: structured template error provenance (PYPOST-143), AST enhancements
    # (PYPOST-378), and environment variable resolver (PYPOST-1118); cap re-derived
    # from measured 241 + ~10% headroom policy (ceil(241 * 1.10) = 266 -> 265).
    "pypost/core/template_service.py": 265,
    # PYPOST-1128: item dispatch extracted to collection_item_dispatch.py;
    # cap re-derived from post-extraction measurement (240) + ~10% headroom.
    "pypost/core/request_manager.py": 264,
    # PYPOST-1128: cross-collection WebSocket indexing and CRUD operations;
    # capped on creation at ~10% headroom policy (119 measured).
    "pypost/core/websocket_registry.py": 131,
    # PYPOST-1128: polymorphic collection item action dispatch extracted from request_manager.py;
    # capped on creation at ~10% headroom policy (75 measured).
    "pypost/core/collection_item_dispatch.py": 83,
    # PYPOST-1071: accepted cohesive growth — PYPOST-1037's strict integer-template
    # conversion, origin-only error logging and ExecutionError mapping stay inside
    # outbound transport preparation and failure translation.
    "pypost/core/http_client.py": 418,
    "pypost/core/storage.py": 380,
    "pypost/core/qt/worker.py": 180,
    "pypost/core/mcp_server_impl.py": 325,
}

MAIN_WINDOW_CLASS = "MainWindow"
# PYPOST-1071: re-derived from the post-extraction measurement (387).
MAIN_WINDOW_CLASS_CAP = 426


@dataclass(frozen=True)
class FileMetrics:
    path: str
    total_lines: int
    non_empty_lines: int
    class_lines: dict[str, int]
    cap: int | None
    audit_era_lines: int | None

    @property
    def violations(self) -> list[str]:
        issues: list[str] = []
        if self.cap is not None and self.total_lines > self.cap:
            issues.append(
                f"{self.path}: {self.total_lines} lines exceeds cap {self.cap}",
            )
        if self.path.endswith("main_window.py"):
            class_loc = self.class_lines.get(MAIN_WINDOW_CLASS, 0)
            if class_loc > MAIN_WINDOW_CLASS_CAP:
                issues.append(
                    f"{self.path}::{MAIN_WINDOW_CLASS}: {class_loc} lines "
                    f"exceeds cap {MAIN_WINDOW_CLASS_CAP}",
                )
        return issues


def count_file_lines(path: Path) -> tuple[int, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    total = len(lines)
    non_empty = sum(1 for line in lines if line.strip())
    return total, non_empty


def count_class_lines(path: Path) -> dict[str, int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            end = node.end_lineno or node.lineno
            result[node.name] = end - node.lineno + 1
    return result


def measure_file(relative_path: str) -> FileMetrics:
    path = REPO_ROOT / relative_path
    if not path.is_file():
        raise FileNotFoundError(relative_path)
    total, non_empty = count_file_lines(path)
    return FileMetrics(
        path=relative_path,
        total_lines=total,
        non_empty_lines=non_empty,
        class_lines=count_class_lines(path),
        cap=FILE_CAPS.get(relative_path),
        audit_era_lines=AUDIT_ERA_LOC.get(relative_path),
    )


def measure_all() -> list[FileMetrics]:
    paths = sorted(set(FILE_CAPS) | set(AUDIT_ERA_LOC))
    return [measure_file(path) for path in paths]


def check_caps() -> list[str]:
    violations: list[str] = []
    for metrics in measure_all():
        violations.extend(metrics.violations)
    return violations


def format_markdown(metrics: list[FileMetrics]) -> str:
    lines = [
        "# SOLID Audit Baseline Metrics",
        "",
        f"**Baseline date:** {BASELINE_DATE}",
        "",
        "## MainWindow regression guard",
        "",
        "| Metric | Audit era (PYPOST-40) | Baseline | Cap |",
        "| --- | ---: | ---: | ---: |",
    ]
    mw = next(m for m in metrics if m.path.endswith("main_window.py"))
    mw_class = mw.class_lines.get(MAIN_WINDOW_CLASS, 0)
    lines.extend(
        [
            f"| `main_window.py` file LOC | 1040 | {mw.total_lines} | "
            f"{mw.cap} |",
            f"| `{MAIN_WINDOW_CLASS}` class LOC | 1040 | {mw_class} | "
            f"{MAIN_WINDOW_CLASS_CAP} |",
            "",
            "## Module inventory caps",
            "",
            "| Module | Audit era LOC | Baseline LOC | Cap |",
            "| --- | ---: | ---: | ---: |",
        ],
    )
    for item in metrics:
        if item.path.endswith("main_window.py"):
            continue
        audit = item.audit_era_lines if item.audit_era_lines is not None else "—"
        cap = item.cap if item.cap is not None else "—"
        lines.append(
            f"| `{item.path}` | {audit} | {item.total_lines} | {cap} |",
        )
    lines.extend(
        [
            "",
            "Regenerate: `.venv/bin/python scripts/audit_baseline_metrics.py "
            "--markdown ai-tasks/PYPOST-376/baseline-metrics.md`",
            "",
        ],
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="Write JSON metrics snapshot")
    parser.add_argument("--markdown", type=Path, help="Write markdown report")
    parser.add_argument("--check", action="store_true", help="Exit 1 if caps exceeded")
    args = parser.parse_args(argv)

    metrics = measure_all()
    if args.json:
        payload = [
            {
                "path": m.path,
                "total_lines": m.total_lines,
                "non_empty_lines": m.non_empty_lines,
                "class_lines": m.class_lines,
                "cap": m.cap,
                "audit_era_lines": m.audit_era_lines,
            }
            for m in metrics
        ]
        args.json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(format_markdown(metrics), encoding="utf-8")

    violations = check_caps()
    if args.check and violations:
        for issue in violations:
            print(issue, file=sys.stderr)
        return 1

    if not args.json and not args.markdown and not args.check:
        print(format_markdown(metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

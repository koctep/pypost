"""Enforce test-source flake8 findings against a frozen occurrence baseline."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_NAME = "test-lint-baseline.json"
TIMEOUT_SECONDS = 60
Identity = tuple[str, str, str, str]


class GateError(ValueError):
    """An invalid baseline, tool result, or source prevents a trustworthy scan."""


@dataclass(frozen=True)
class Finding:
    path: str
    row: int
    column: int
    code: str
    message: str
    source: str

    @property
    def identity(self) -> Identity:
        message = self.message
        if self.code == "F811":
            message = re.sub(r"from line \d+", "from line <previous>", message)
        return self.path, self.code, message, self.source


def _test_path(value: Any) -> str:
    if not isinstance(value, str):
        raise GateError("test path must be a string")
    path = PurePosixPath(value)
    if ("\\" in value or path.is_absolute() or ".." in path.parts
            or len(path.parts) < 2 or path.parts[0] != "tests"
            or path.suffix != ".py" or str(path) != value):
        raise GateError(f"invalid test path: {value!r}")
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GateError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _text_parts(value: Any, field: str) -> str:
    if (not isinstance(value, list) or not value
            or any(not isinstance(part, str) or len(part) > 60 or "\n" in part or "\r" in part
                   for part in value)):
        raise GateError(f"invalid baseline {field}: expected single-line string fragments")
    return "".join(value)


def _entry_identity(entry: dict[str, Any]) -> Identity:
    code = entry["code"]
    if not isinstance(code, str) or re.fullmatch(r"[A-Z]\d{3}", code) is None:
        raise GateError("invalid baseline diagnostic code")
    message = _text_parts(entry["message"], "message")
    source = _text_parts(entry["source"], "source")
    if not message.strip() or message != message.strip() or source != source.strip():
        raise GateError("baseline message/source must be normalized")
    return _test_path(entry["path"]), code, message, source


def load_baseline(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    if (not isinstance(data, dict) or set(data) != {"version", "entries"}
            or type(data["version"]) is not int or data["version"] != 1
            or not isinstance(data["entries"], list)):
        raise GateError("invalid baseline schema/version")
    seen: set[Identity] = set()
    for entry in data["entries"]:
        if not isinstance(entry, dict) or set(entry) != {
            "path", "code", "message", "source", "count", "reason",
        }:
            raise GateError("invalid baseline entry fields")
        if type(entry["count"]) is not int or entry["count"] <= 0:
            raise GateError("baseline count must be a positive integer")
        if not isinstance(entry["reason"], str) or not entry["reason"].strip():
            raise GateError("baseline entry requires a justification")
        identity = _entry_identity(entry)
        if identity in seen:
            raise GateError("duplicate baseline identity")
        seen.add(identity)
    return data["entries"]


def parse_findings(output: str, root: Path) -> list[Finding]:
    findings: list[Finding] = []
    sources: dict[str, list[str]] = {}
    for diagnostic in output.splitlines():
        parts = diagnostic.split("\t", 4)
        if (len(parts) != 5 or re.fullmatch(r"[1-9]\d*", parts[1]) is None
                or re.fullmatch(r"[1-9]\d*", parts[2]) is None
                or re.fullmatch(r"[A-Z]\d{3}", parts[3]) is None or not parts[4].strip()):
            raise GateError(f"unrecognized flake8 output: {diagnostic!r}")
        path = _test_path(parts[0])
        row, column = int(parts[1]), int(parts[2])
        if path not in sources:
            source = root / path
            if not source.resolve().is_relative_to(root.resolve() / "tests"):
                raise GateError(f"test source escapes repository: {path}")
            sources[path] = source.read_text(encoding="utf-8").splitlines()
        lines = sources[path]
        if row > len(lines):
            raise GateError(f"invalid source row {row}: {path}")
        findings.append(Finding(path, row, column, parts[3], parts[4], lines[row - 1].strip()))
    return findings


def run_flake8(root: Path) -> list[Finding]:
    if not (root / "tests").is_dir() or not (root / ".flake8").is_file():
        raise GateError("test lint requires tests/ and repository .flake8 configuration")
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--jobs=1", "--require-plugins=flake8-print",
         "--format=%(path)s\t%(row)d\t%(col)d\t%(code)s\t%(text)s", "tests/"],
        cwd=root, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False,
    )
    if result.returncode not in (0, 1) or result.stderr:
        raise GateError(
            f"flake8 execution failed (exit {result.returncode}): "
            f"{result.stderr or result.stdout}"
        )
    findings = parse_findings(result.stdout, root)
    if (result.returncode == 0) != (not findings):
        raise GateError("flake8 exit status contradicts its diagnostic output")
    return findings


def compare(
    findings: list[Finding], entries: list[dict[str, Any]],
) -> tuple[Counter[Identity], Counter[Identity]]:
    current = Counter(finding.identity for finding in findings)
    baseline = Counter({_entry_identity(entry): entry["count"] for entry in entries})
    return current - baseline, baseline - current


def prune_baseline(path: Path, entries: list[dict[str, Any]], findings: list[Finding]) -> None:
    new, _ = compare(findings, entries)
    if new:
        raise GateError("refusing to prune while new test lint findings exist")
    current = Counter(finding.identity for finding in findings)
    retained = [dict(entry, count=current[_entry_identity(entry)])
                for entry in entries if current[_entry_identity(entry)]]
    retained.sort(key=_entry_identity)
    content = json.dumps({"version": 1, "entries": retained}, indent=2, ensure_ascii=False) + "\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False,
        ) as output:
            temporary = Path(output.name)
            output.write(content)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--prune-fixed", action="store_true")
    args = parser.parse_args(argv)
    baseline = args.baseline or args.root / BASELINE_NAME
    try:
        entries = load_baseline(baseline)
        findings = run_flake8(args.root)
        new, fixed = compare(findings, entries)
        remaining = new.copy()
        for finding in findings:
            if remaining[finding.identity]:
                print(  # noqa: T201 -- CLI diagnostics are the lint gate output.
                    f"{finding.path}:{finding.row}:{finding.column}: "
                    f"{finding.code} {finding.message}",
                )
                remaining[finding.identity] -= 1
        if new:
            return 1
        if args.prune_fixed:
            prune_baseline(baseline, entries, findings)
        elif fixed:
            for identity, count in sorted(fixed.items()):
                print(  # noqa: T201 -- Report resolved debt and the explicit prune action.
                    f"fixed baseline: {identity[0]} {identity[1]} ({count} occurrence(s))",
                )
            print("Run make lint-tests-prune to remove fixed allowances.")  # noqa: T201
            return 1
        print(f"Test lint OK ({len(findings)} accepted legacy occurrences).")  # noqa: T201
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Test lint failed: {error}", file=sys.stderr)  # noqa: T201 -- CLI failure.
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

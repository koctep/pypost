#!/usr/bin/env python3
"""Generate committed transitive production dependency license inventory (PYPOST-809)."""

from __future__ import annotations

import argparse
import logging
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REQUIREMENTS_TXT = _REPO_ROOT / "requirements.txt"
_LICENSES_DIR = _REPO_ROOT / "LICENSES"
_OUTPUT_CSV = _LICENSES_DIR / "transitive.csv"
_PKG_LINE_RE = re.compile(r"^([A-Za-z0-9_.-]+)==")
_NORMALIZE_RE = re.compile(r"[-_.]+")


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
    )


def _normalize_package_name(name: str) -> str:
    return _NORMALIZE_RE.sub("-", name).lower()


def _production_package_names(requirements_path: Path) -> set[str]:
    names: set[str] = set()
    for raw in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _PKG_LINE_RE.match(line)
        if match is None:
            continue
        names.add(_normalize_package_name(match.group(1)))
    if not names:
        msg = f"No pinned packages found in {requirements_path}"
        raise ValueError(msg)
    return names


def _pip_licenses_executable() -> Path:
    venv_bin = _REPO_ROOT / ".venv" / "bin" / "pip-licenses"
    if venv_bin.is_file():
        return venv_bin
    return Path("pip-licenses")


def _run_pip_licenses() -> str:
    proc = subprocess.run(
        [
            str(_pip_licenses_executable()),
            "--format=csv",
            "--with-urls",
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or proc.stdout.strip() or "pip-licenses failed"
        raise RuntimeError(stderr)
    return proc.stdout


def _filter_inventory(csv_text: str, production_names: set[str]) -> str:
    lines = csv_text.strip().splitlines()
    if not lines:
        raise ValueError("pip-licenses returned no output")

    header = lines[0]
    filtered: list[str] = [header]
    for line in lines[1:]:
        if not line.strip():
            continue
        name = line.split(",", 1)[0].strip().strip('"')
        if _normalize_package_name(name) in production_names:
            filtered.append(line)

    if len(filtered) == 1:
        raise ValueError("No production packages matched pip-licenses output")

    return "\n".join(filtered) + "\n"


def build_inventory_text(requirements_path: Path = _REQUIREMENTS_TXT) -> str:
    production_names = _production_package_names(requirements_path)
    csv_text = _run_pip_licenses()
    inventory = _filter_inventory(csv_text, production_names)
    matched = len(inventory.strip().splitlines()) - 1
    if matched != len(production_names):
        missing = production_names - {
            _normalize_package_name(line.split(",", 1)[0].strip().strip('"'))
            for line in inventory.strip().splitlines()[1:]
        }
        missing_list = ", ".join(sorted(missing))
        raise ValueError(
            f"requirements.txt lists {len(production_names)} packages but inventory "
            f"matched {matched}; missing: {missing_list}",
        )
    return inventory


def inventory_matches_committed(
    requirements_path: Path = _REQUIREMENTS_TXT,
    output_path: Path = _OUTPUT_CSV,
) -> bool:
    if not output_path.is_file():
        return False
    return build_inventory_text(requirements_path) == output_path.read_text(encoding="utf-8")


def write_inventory(
    requirements_path: Path = _REQUIREMENTS_TXT,
    output_path: Path = _OUTPUT_CSV,
) -> None:
    inventory = build_inventory_text(requirements_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(inventory, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate LICENSES/transitive.csv from the committed production lock "
            "(requirements.txt)."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 0 when committed LICENSES/transitive.csv matches generated inventory.",
    )
    args = parser.parse_args(argv)
    _configure_logging()

    if args.check:
        if inventory_matches_committed():
            logging.info("Committed license inventory is up to date.")
            return 0
        logging.error(
            "Committed license inventory is out of date. "
            "Run `make generate-license-inventory`.",
        )
        return 1

    write_inventory()
    logging.info("Wrote %s", _OUTPUT_CSV.relative_to(_REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

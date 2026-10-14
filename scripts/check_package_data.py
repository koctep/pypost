"""Verify built wheels against the canonical application and examples sources."""

from __future__ import annotations

import argparse
import configparser
from pathlib import Path
from zipfile import ZipFile

import yaml


def required_members(source_root: Path) -> dict[str, Path]:
    examples = source_root / "examples"
    manifest = yaml.safe_load((examples / "pypost-library.yaml").read_text(encoding="utf-8"))
    resources = {Path("pypost-library.yaml"), Path("README.md"), Path("__init__.py")}
    for collection in manifest["collections"]:
        relative = Path(collection)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"example path escapes canonical source: {collection}")
        resources.add(relative)
    resources.update(path.relative_to(examples) for path in examples.glob("environments/*.json"))
    if (examples / "builtin-collections.yaml").exists():
        resources.add(Path("builtin-collections.yaml"))
    members = {
        path.relative_to(source_root).as_posix(): path
        for path in (source_root / "pypost").rglob("__init__.py")
    }
    members.update({f"pypost/bundled_examples/{path.as_posix()}": examples / path
                    for path in resources})
    missing_sources = sorted(str(path) for path in members.values() if not path.is_file())
    if missing_sources:
        raise ValueError(f"missing canonical sources: {', '.join(missing_sources)}")
    return members


def verify_entry_points(archive: ZipFile) -> None:
    entry_point_members = [
        name for name in archive.namelist()
        if name.endswith(".dist-info/entry_points.txt")
        or name.endswith("/entry_points.txt")
        or name == "entry_points.txt"
    ]
    has_dist_info = any(".dist-info/" in name for name in archive.namelist())
    if not entry_point_members:
        if has_dist_info:
            raise ValueError("wheel missing entry_points.txt in .dist-info")
        return

    parser = configparser.ConfigParser()
    content = archive.read(entry_point_members[0]).decode("utf-8")
    parser.read_string(content)
    if not parser.has_section("console_scripts"):
        raise ValueError("wheel entry_points.txt missing [console_scripts] section")

    console_scripts = dict(parser.items("console_scripts"))
    expected_scripts = {
        "pypost": "pypost.main:main",
        "pypost-daemon": "pypost.daemon:main",
    }
    for script_name, expected_target in expected_scripts.items():
        if script_name not in console_scripts:
            raise ValueError(f"wheel missing console_script: {script_name}")
        if console_scripts[script_name] != expected_target:
            raise ValueError(
                f"wheel console_script {script_name} has unexpected target: "
                f"{console_scripts[script_name]} != {expected_target}"
            )


def inspect_wheel(wheel: Path, source_root: Path) -> list[str]:
    required = required_members(source_root)
    with ZipFile(wheel) as archive:
        missing = sorted(required.keys() - set(archive.namelist()))
        if missing:
            raise ValueError(f"wheel missing required members: {', '.join(missing)}")
        changed = sorted(member for member, source in required.items()
                         if archive.read(member) != source.read_bytes())
        if changed:
            raise ValueError(f"wheel differs from canonical sources: {', '.join(changed)}")
        verify_entry_points(archive)
    return sorted(required)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        members = inspect_wheel(args.wheel, args.source_root)
    except (OSError, ValueError) as error:
        parser.exit(1, f"check-package-data: {error}\n")
    for member in members:
        print(f"verified: {member}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

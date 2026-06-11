#!/usr/bin/env python3
"""Operator CLI for environment encryption migration (PYPOST-487)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Allow running from repo root without installing the package.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pypost.core.config_manager import ConfigManager  # noqa: E402
from pypost.core.encryption_migration import (  # noqa: E402
    EncryptionMigrationService,
    EnvironmentInventory,
    MigrationReport,
    ReencryptStats,
)
from pypost.core.storage import StorageManager  # noqa: E402

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )


def _inventory_to_dict(inventory: EnvironmentInventory) -> dict[str, Any]:
    return {
        "environment_count": inventory.environment_count,
        "hidden_value_count": inventory.hidden_value_count,
        "encrypted_envelope_count": inventory.encrypted_envelope_count,
        "v1_envelope_count": inventory.v1_envelope_count,
        "v2_envelope_count": inventory.v2_envelope_count,
        "plaintext_hidden_count": inventory.plaintext_hidden_count,
        "invalid_hidden_count": inventory.invalid_hidden_count,
        "kid_histogram": dict(inventory.kid_histogram),
        "missing_kids": sorted(inventory.missing_kids),
        "data_quality_errors": list(inventory.data_quality_errors),
    }


def _reencrypt_stats_to_dict(stats: ReencryptStats | None) -> dict[str, int] | None:
    if stats is None:
        return None
    return {
        "encrypted_count": stats.encrypted_count,
        "reused_count": stats.reused_count,
    }


def _report_to_dict(report: MigrationReport, *, command: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "command": command,
        "success": report.success,
        "dry_run": report.dry_run,
        "backup_path": str(report.backup_path) if report.backup_path else None,
        "errors": list(report.errors),
        "inventory": _inventory_to_dict(report.inventory),
    }
    stats = _reencrypt_stats_to_dict(report.reencrypt_stats)
    if stats is not None:
        payload["reencrypt_stats"] = stats
    return payload


def _format_inventory(report: MigrationReport) -> str:
    inv = report.inventory
    lines = [
        f"environments: {inv.environment_count}",
        f"hidden_values: {inv.hidden_value_count}",
        f"encrypted_envelopes: {inv.encrypted_envelope_count}",
        f"v1_envelopes: {inv.v1_envelope_count}",
        f"v2_envelopes: {inv.v2_envelope_count}",
        f"plaintext_hidden: {inv.plaintext_hidden_count}",
        f"invalid_hidden: {inv.invalid_hidden_count}",
    ]
    if inv.kid_histogram:
        lines.append("kid_histogram:")
        for kid, count in sorted(inv.kid_histogram.items()):
            lines.append(f"  {kid}: {count}")
    if inv.missing_kids:
        lines.append("missing_kids:")
        for kid in sorted(inv.missing_kids):
            lines.append(f"  {kid}")
    if report.dry_run:
        lines.append("dry_run: true")
    if report.backup_path is not None:
        lines.append(f"backup: {report.backup_path}")
    if report.reencrypt_stats is not None:
        stats = report.reencrypt_stats
        lines.append("reencrypt_stats:")
        lines.append(f"  encrypted: {stats.encrypted_count}")
        lines.append(f"  reused: {stats.reused_count}")
    return "\n".join(lines)


def _emit_report(report: MigrationReport, *, command: str, as_json: bool) -> int:
    if as_json:
        print(json.dumps(_report_to_dict(report, command=command), indent=2))
    else:
        print(_format_inventory(report))
        for error in report.errors:
            print(f"error: {error}", file=sys.stderr)
    return 0 if report.success else 1


def _add_global_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON on stdout for scripting and CI.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        metavar="PATH",
        help="Override PyPost data directory (environments.json location).",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        metavar="PATH",
        help="Override PyPost config directory (settings.json location).",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify and migrate encrypted environment storage.",
    )
    _add_global_options(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify", help="Check decrypt access for stored envelopes.")
    _add_global_options(verify)

    report = subparsers.add_parser(
        "report",
        help="Inventory kid/plaintext mix without writes.",
    )
    _add_global_options(report)

    reencrypt = subparsers.add_parser(
        "re-encrypt",
        help="Bulk re-encrypt hidden values under the active key.",
    )
    _add_global_options(reencrypt)
    reencrypt.add_argument(
        "--dry-run",
        action="store_true",
        help="Decrypt and report projected kid counts without saving.",
    )
    reencrypt.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip timestamped backup before writing.",
    )

    encrypt_plain = subparsers.add_parser(
        "encrypt-plaintext",
        help="Encrypt previously plain hidden values after enabling encryption.",
    )
    _add_global_options(encrypt_plain)
    encrypt_plain.add_argument("--dry-run", action="store_true")
    encrypt_plain.add_argument("--no-backup", action="store_true")

    upgrade_v2 = subparsers.add_parser(
        "upgrade-v2",
        help="Re-encrypt v1 hidden envelopes to v2 fernet under the active key.",
    )
    _add_global_options(upgrade_v2)
    upgrade_v2.add_argument("--dry-run", action="store_true")
    upgrade_v2.add_argument("--no-backup", action="store_true")

    return parser


def _build_storage(data_dir: Path | None) -> StorageManager:
    if data_dir is None:
        return StorageManager()
    resolved = data_dir.expanduser().resolve()
    if not resolved.is_dir():
        print(f"data directory does not exist: {resolved}", file=sys.stderr)
        raise SystemExit(1)
    return StorageManager(data_dir=resolved)


def _build_config_manager(config_dir: Path | None) -> ConfigManager:
    if config_dir is None:
        return ConfigManager()
    resolved = config_dir.expanduser().resolve()
    if not resolved.is_dir():
        print(f"config directory does not exist: {resolved}", file=sys.stderr)
        raise SystemExit(1)
    return ConfigManager(config_dir=resolved)


def main(argv: list[str] | None = None) -> int:
    _configure_logging()
    args = _build_parser().parse_args(argv)
    logger.info(
        "encryption_migrate_command_started command=%s json=%s data_dir=%s config_dir=%s",
        args.command,
        args.json,
        args.data_dir,
        args.config_dir,
    )
    settings = _build_config_manager(args.config_dir).load_config()
    service = EncryptionMigrationService(_build_storage(args.data_dir))

    if args.command == "verify":
        exit_code = _emit_report(
            service.verify_decrypt_access(settings),
            command=args.command,
            as_json=args.json,
        )
    elif args.command == "report":
        inventory = service.build_inventory(settings)
        quality_errors = inventory.data_quality_errors
        report = MigrationReport(
            inventory=inventory,
            dry_run=False,
            backup_path=None,
            errors=quality_errors,
            success=not quality_errors,
        )
        exit_code = _emit_report(report, command=args.command, as_json=args.json)
    elif args.command == "re-encrypt":
        backup = not args.no_backup
        report = service.bulk_re_encrypt(
            settings,
            dry_run=args.dry_run,
            backup=backup,
        )
        exit_code = _emit_report(report, command=args.command, as_json=args.json)
    elif args.command == "encrypt-plaintext":
        backup = not args.no_backup
        report = service.encrypt_plaintext_hidden(
            settings,
            dry_run=args.dry_run,
            backup=backup,
        )
        exit_code = _emit_report(report, command=args.command, as_json=args.json)
    elif args.command == "upgrade-v2":
        backup = not args.no_backup
        report = service.upgrade_envelopes_to_v2(
            settings,
            dry_run=args.dry_run,
            backup=backup,
        )
        exit_code = _emit_report(report, command=args.command, as_json=args.json)
    else:
        exit_code = 2

    logger.info(
        "encryption_migrate_command_completed command=%s exit_code=%d success=%s",
        args.command,
        exit_code,
        exit_code == 0,
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

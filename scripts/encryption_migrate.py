#!/usr/bin/env python3
"""Operator CLI for environment encryption migration (PYPOST-487)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Allow running from repo root without installing the package.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pypost.core.config_manager import ConfigManager  # noqa: E402
from pypost.core.encryption_migration import (  # noqa: E402
    EncryptionMigrationService,
    MigrationReport,
)
from pypost.core.storage import StorageManager  # noqa: E402

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )


def _format_inventory(report: MigrationReport) -> str:
    inv = report.inventory
    lines = [
        f"environments: {inv.environment_count}",
        f"hidden_values: {inv.hidden_value_count}",
        f"encrypted_envelopes: {inv.encrypted_envelope_count}",
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
    return "\n".join(lines)


def _emit_report(report: MigrationReport) -> int:
    print(_format_inventory(report))
    for error in report.errors:
        print(f"error: {error}", file=sys.stderr)
    return 0 if report.success else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify and migrate encrypted environment storage.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("verify", help="Check decrypt access for stored envelopes.")

    subparsers.add_parser(
        "report",
        help="Inventory kid/plaintext mix without writes.",
    )

    reencrypt = subparsers.add_parser(
        "re-encrypt",
        help="Bulk re-encrypt hidden values under the active key.",
    )
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
    encrypt_plain.add_argument("--dry-run", action="store_true")
    encrypt_plain.add_argument("--no-backup", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_logging()
    args = _build_parser().parse_args(argv)
    logger.info("encryption_migrate_command_started command=%s", args.command)
    settings = ConfigManager().load_config()
    service = EncryptionMigrationService(StorageManager())

    if args.command == "verify":
        exit_code = _emit_report(service.verify_decrypt_access(settings))
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
        exit_code = _emit_report(report)
    elif args.command == "re-encrypt":
        backup = not args.no_backup
        report = service.bulk_re_encrypt(
            settings,
            dry_run=args.dry_run,
            backup=backup,
        )
        exit_code = _emit_report(report)
    elif args.command == "encrypt-plaintext":
        backup = not args.no_backup
        report = service.encrypt_plaintext_hidden(
            settings,
            dry_run=args.dry_run,
            backup=backup,
        )
        exit_code = _emit_report(report)
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

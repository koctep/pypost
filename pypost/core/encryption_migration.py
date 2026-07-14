"""Operator migration helpers for environment encryption at rest."""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypost.core.encryption_config import build_key_provider, resolve_encryption_enabled
from pypost.core.key_provider import EnvironmentEncryptionError
from pypost.core.storage_interface import StorageInterface
from pypost.models.models import Environment
from pypost.models.settings import AppSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EnvironmentInventory:
    environment_count: int
    hidden_value_count: int
    encrypted_envelope_count: int
    v1_envelope_count: int
    v2_envelope_count: int
    plaintext_hidden_count: int
    invalid_hidden_count: int
    kid_histogram: dict[str, int]
    missing_kids: frozenset[str]
    data_quality_errors: tuple[str, ...]


@dataclass(frozen=True)
class ReencryptStats:
    encrypted_count: int
    reused_count: int


@dataclass(frozen=True)
class MigrationReport:
    inventory: EnvironmentInventory
    dry_run: bool
    backup_path: Path | None
    errors: tuple[str, ...]
    success: bool
    reencrypt_stats: ReencryptStats | None = None


def _log_inventory(event: str, inventory: EnvironmentInventory) -> None:
    logger.info(
        "%s environment_count=%d hidden_value_count=%d "
        "encrypted_envelope_count=%d v1_envelope_count=%d v2_envelope_count=%d "
        "plaintext_hidden_count=%d invalid_hidden_count=%d "
        "missing_kid_count=%d data_quality_error_count=%d",
        event,
        inventory.environment_count,
        inventory.hidden_value_count,
        inventory.encrypted_envelope_count,
        inventory.v1_envelope_count,
        inventory.v2_envelope_count,
        inventory.plaintext_hidden_count,
        inventory.invalid_hidden_count,
        len(inventory.missing_kids),
        len(inventory.data_quality_errors),
    )


def format_migration_report(report: MigrationReport, *, cli_style: bool = False) -> str:
    """Human-readable migration report for CLI stdout or Settings dialog."""
    inv = report.inventory
    if cli_style:
        lines = [
            f"environments: {inv.environment_count}",
            f"hidden_values: {inv.hidden_value_count}",
            f"encrypted_envelopes: {inv.encrypted_envelope_count}",
            f"v1_envelopes: {inv.v1_envelope_count}",
            f"v2_envelopes: {inv.v2_envelope_count}",
            f"plaintext_hidden: {inv.plaintext_hidden_count}",
            f"invalid_hidden: {inv.invalid_hidden_count}",
        ]
        kid_label = "kid_histogram:"
        missing_label = "missing_kids:"
        backup_prefix = "backup:"
        reencrypt_prefix = "reencrypt_stats:"
        encrypted_label = "  encrypted:"
        reused_label = "  reused:"
    else:
        lines = [
            f"Environments: {inv.environment_count}",
            f"Hidden values: {inv.hidden_value_count}",
            f"Encrypted envelopes: {inv.encrypted_envelope_count}",
            f"Plaintext hidden: {inv.plaintext_hidden_count}",
            f"Invalid hidden: {inv.invalid_hidden_count}",
        ]
        kid_label = "Key IDs:"
        missing_label = "Missing key IDs:"
        backup_prefix = "Backup:"
        reencrypt_prefix = None
        encrypted_label = "Re-encrypted:"
        reused_label = "Reused:"

    if inv.kid_histogram:
        lines.append(kid_label)
        for kid, count in sorted(inv.kid_histogram.items()):
            lines.append(f"  {kid}: {count}")
    if inv.missing_kids:
        lines.append(missing_label)
        for kid in sorted(inv.missing_kids):
            lines.append(f"  {kid}")
    if report.dry_run and cli_style:
        lines.append("dry_run: true")
    if report.backup_path is not None:
        lines.append(f"{backup_prefix} {report.backup_path}")
    if report.reencrypt_stats is not None:
        stats = report.reencrypt_stats
        if reencrypt_prefix is not None:
            lines.append(reencrypt_prefix)
            lines.append(f"{encrypted_label} {stats.encrypted_count}")
            lines.append(f"{reused_label} {stats.reused_count}")
        else:
            lines.append(f"{encrypted_label} {stats.encrypted_count}")
            lines.append(f"{reused_label} {stats.reused_count}")
    if report.errors and not cli_style:
        lines.append("")
        lines.append("Errors:")
        lines.extend(f"  {error}" for error in report.errors)
    return "\n".join(lines)


def backup_environments_file(path: Path) -> Path:
    """Copy environments.json to a timestamped sibling file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = path.with_name(f"{path.stem}.backup.{timestamp}{path.suffix}")
    shutil.copy2(path, backup_path)
    logger.info("environments_backup_created path=%s", backup_path)
    return backup_path


def _is_encrypted_envelope(value: Any) -> bool:
    return isinstance(value, dict) and value.get("enc") is True


def _environment_label(item: dict[str, Any]) -> str:
    name = item.get("name")
    if name:
        return str(name)
    env_id = item.get("id")
    if env_id:
        return str(env_id)
    return "unknown"


def _invalid_hidden_message(env_label: str, key: str, value: Any) -> str:
    return (
        f"{env_label}: hidden key {key} has invalid type "
        f"({type(value).__name__}, expected envelope or string)"
    )


class EncryptionMigrationService:
    """Verify decrypt access, inventory kid/plaintext mix, and bulk re-encrypt."""

    def __init__(self, storage: StorageInterface) -> None:
        self._storage = storage

    def build_inventory(self, settings: AppSettings | None) -> EnvironmentInventory:
        self._storage.apply_encryption_settings(settings)
        raw = self._read_raw_environments()
        return self._inventory_from_raw(raw, settings)

    def _inventory_from_raw(
        self,
        raw: list[dict[str, Any]],
        settings: AppSettings | None,
    ) -> EnvironmentInventory:
        inventory = self._scan_raw_environments(raw)
        missing = self._check_missing_kids(inventory.kid_histogram, settings)
        inventory = replace(inventory, missing_kids=missing)
        _log_inventory("encryption_migration_inventory_built", inventory)
        return inventory

    def verify_decrypt_access(self, settings: AppSettings | None) -> MigrationReport:
        logger.info("encryption_migration_verify_started")
        self._storage.apply_encryption_settings(settings)
        raw = self._read_raw_environments()
        inventory = self._inventory_from_raw(raw, settings)
        errors: list[str] = []
        if inventory.data_quality_errors:
            logger.error(
                "encryption_migration_data_quality_errors count=%d",
                len(inventory.data_quality_errors),
            )
            errors.extend(inventory.data_quality_errors)
        elif inventory.missing_kids:
            logger.error(
                "encryption_migration_missing_kids count=%d",
                len(inventory.missing_kids),
            )
            errors.extend(
                f"Missing key material for kid: {kid}"
                for kid in sorted(inventory.missing_kids)
            )
        else:
            _, decrypt_errors = self._deserialize_records(raw)
            if decrypt_errors:
                logger.error(
                    "encryption_migration_decrypt_failed error_count=%d",
                    len(decrypt_errors),
                )
                for detail in decrypt_errors:
                    logger.error("encryption_migration_decrypt_failed detail=%s", detail)
            errors.extend(decrypt_errors)
        success = not errors
        if success:
            logger.info("encryption_migration_verify_completed success=true")
        else:
            logger.warning(
                "encryption_migration_verify_completed success=false error_count=%d",
                len(errors),
            )
        return MigrationReport(
            inventory=inventory,
            dry_run=False,
            backup_path=None,
            errors=tuple(errors),
            success=success,
        )

    def bulk_re_encrypt(
        self,
        settings: AppSettings | None,
        *,
        dry_run: bool = False,
        backup: bool = True,
    ) -> MigrationReport:
        return self._rewrite_environments(
            settings,
            dry_run=dry_run,
            backup=backup,
            require_plaintext=False,
        )

    def encrypt_plaintext_hidden(
        self,
        settings: AppSettings | None,
        *,
        dry_run: bool = False,
        backup: bool = True,
    ) -> MigrationReport:
        return self._rewrite_environments(
            settings,
            dry_run=dry_run,
            backup=backup,
            require_plaintext=True,
        )

    def upgrade_envelopes_to_v2(
        self,
        settings: AppSettings | None,
        *,
        dry_run: bool = False,
        backup: bool = True,
    ) -> MigrationReport:
        return self._rewrite_environments(
            settings,
            dry_run=dry_run,
            backup=backup,
            require_plaintext=False,
            target_envelope_version=2,
        )

    def _rewrite_operation_name(
        self,
        *,
        require_plaintext: bool,
        target_envelope_version: int | None,
    ) -> str:
        if target_envelope_version == 2:
            return "upgrade_v2"
        if require_plaintext:
            return "encrypt_plaintext"
        return "re_encrypt"

    def _rewrite_noop_stats(self, inventory: EnvironmentInventory) -> ReencryptStats:
        return ReencryptStats(
            encrypted_count=0,
            reused_count=inventory.hidden_value_count,
        )

    def _rewrite_skip_report(
        self,
        *,
        inventory: EnvironmentInventory,
        dry_run: bool,
        operation: str,
        reason: str,
        reencrypt_stats: ReencryptStats | None = None,
        log_extra: str = "",
    ) -> MigrationReport:
        logger.info(
            "encryption_migration_operation_skipped operation=%s reason=%s%s",
            operation,
            reason,
            log_extra,
        )
        return MigrationReport(
            inventory=inventory,
            dry_run=dry_run,
            backup_path=None,
            errors=(),
            success=True,
            reencrypt_stats=reencrypt_stats,
        )

    def _rewrite_early_skip(
        self,
        *,
        settings: AppSettings | None,
        inventory: EnvironmentInventory,
        dry_run: bool,
        operation: str,
        require_plaintext: bool,
        target_envelope_version: int | None,
    ) -> MigrationReport | None:
        if require_plaintext and inventory.plaintext_hidden_count == 0:
            return self._rewrite_skip_report(
                inventory=inventory,
                dry_run=dry_run,
                operation=operation,
                reason="no_plaintext_hidden",
            )

        if (
            not require_plaintext
            and target_envelope_version != 2
            and inventory.encrypted_envelope_count == 0
        ):
            return self._rewrite_skip_report(
                inventory=inventory,
                dry_run=dry_run,
                operation=operation,
                reason="no_ciphertext_to_rotate",
                reencrypt_stats=self._rewrite_noop_stats(inventory),
            )

        if target_envelope_version == 2 and self._inventory_all_v2(inventory):
            return self._rewrite_skip_report(
                inventory=inventory,
                dry_run=dry_run,
                operation=operation,
                reason="already_v2",
                reencrypt_stats=self._rewrite_noop_stats(inventory),
            )

        if not require_plaintext and target_envelope_version != 2:
            active_kid = build_key_provider(settings).get_current_key().key_id
            if self._inventory_matches_active_kid(inventory, active_kid):
                return self._rewrite_skip_report(
                    inventory=inventory,
                    dry_run=dry_run,
                    operation=operation,
                    reason="already_on_active_kid",
                    reencrypt_stats=self._rewrite_noop_stats(inventory),
                    log_extra=f" active_kid={active_kid}",
                )
        return None

    def _rewrite_inventory_failure(
        self,
        *,
        inventory: EnvironmentInventory,
        dry_run: bool,
        operation: str,
    ) -> MigrationReport | None:
        quality_errors = inventory.data_quality_errors
        if not quality_errors and not inventory.missing_kids:
            return None
        if quality_errors:
            logger.error(
                "encryption_migration_data_quality_errors count=%d",
                len(quality_errors),
            )
        if inventory.missing_kids:
            logger.error(
                "encryption_migration_missing_kids count=%d",
                len(inventory.missing_kids),
            )
        errors = quality_errors + tuple(
            f"Missing key material for kid: {kid}" for kid in sorted(inventory.missing_kids)
        )
        logger.warning(
            "encryption_migration_operation_completed operation=%s success=false "
            "error_count=%d",
            operation,
            len(errors),
        )
        return MigrationReport(
            inventory=inventory,
            dry_run=dry_run,
            backup_path=None,
            errors=errors,
            success=False,
        )

    def _rewrite_decrypt_failure(
        self,
        *,
        inventory: EnvironmentInventory,
        decrypt_errors: tuple[str, ...],
        dry_run: bool,
        operation: str,
    ) -> MigrationReport:
        logger.error(
            "encryption_migration_decrypt_failed error_count=%d",
            len(decrypt_errors),
        )
        for detail in decrypt_errors:
            logger.error("encryption_migration_decrypt_failed detail=%s", detail)
        logger.warning(
            "encryption_migration_operation_completed operation=%s success=false "
            "error_count=%d",
            operation,
            len(decrypt_errors),
        )
        return MigrationReport(
            inventory=inventory,
            dry_run=dry_run,
            backup_path=None,
            errors=decrypt_errors,
            success=False,
        )

    def _rewrite_dry_run(
        self,
        *,
        settings: AppSettings | None,
        inventory: EnvironmentInventory,
        environments: list[Environment],
        operation: str,
        target_envelope_version: int | None,
    ) -> MigrationReport:
        active_kid = build_key_provider(settings).get_current_key().key_id
        if target_envelope_version == 2:
            projected = self._projected_inventory_after_v2_upgrade(inventory, active_kid)
        else:
            projected = self._projected_inventory_after_encrypt(inventory, active_kid)
        projected_stats = self._storage.project_save_stats(
            environments,
            target_envelope_version=target_envelope_version,
        )
        logger.info(
            "encryption_migration_dry_run_completed operation=%s "
            "projected_encrypted_count=%d projected_reused_count=%d active_kid=%s",
            operation,
            projected_stats.encrypted_count,
            projected_stats.reused_count,
            active_kid,
        )
        return MigrationReport(
            inventory=projected,
            dry_run=True,
            backup_path=None,
            errors=(),
            success=True,
            reencrypt_stats=ReencryptStats(
                encrypted_count=projected_stats.encrypted_count,
                reused_count=projected_stats.reused_count,
            ),
        )

    def _rewrite_save(
        self,
        *,
        settings: AppSettings | None,
        environments: list[Environment],
        operation: str,
        backup: bool,
        target_envelope_version: int | None,
    ) -> MigrationReport:
        backup_path = None
        if backup:
            backup_path = backup_environments_file(self._storage.environments_file)
        save_stats = self._storage.save_environments(
            environments,
            target_envelope_version=target_envelope_version,
        )
        final_inventory = self.build_inventory(settings)
        logger.info(
            "encryption_migration_save_completed operation=%s backup_path=%s "
            "environment_count=%d encrypted_count=%d reused_count=%d",
            operation,
            backup_path,
            final_inventory.environment_count,
            save_stats.encrypted_count,
            save_stats.reused_count,
        )
        logger.info(
            "encryption_migration_operation_completed operation=%s success=true dry_run=false",
            operation,
        )
        return MigrationReport(
            inventory=final_inventory,
            dry_run=False,
            backup_path=backup_path,
            errors=(),
            success=True,
            reencrypt_stats=ReencryptStats(
                encrypted_count=save_stats.encrypted_count,
                reused_count=save_stats.reused_count,
            ),
        )

    def _rewrite_environments(
        self,
        settings: AppSettings | None,
        *,
        dry_run: bool,
        backup: bool,
        require_plaintext: bool,
        target_envelope_version: int | None = None,
    ) -> MigrationReport:
        operation = self._rewrite_operation_name(
            require_plaintext=require_plaintext,
            target_envelope_version=target_envelope_version,
        )
        logger.info(
            "encryption_migration_operation_started operation=%s dry_run=%s backup=%s",
            operation,
            dry_run,
            backup,
        )
        if not resolve_encryption_enabled(settings):
            inventory = self.build_inventory(settings)
            logger.warning(
                "encryption_migration_operation_skipped operation=%s reason=encryption_disabled",
                operation,
            )
            return MigrationReport(
                inventory=inventory,
                dry_run=dry_run,
                backup_path=None,
                errors=("Encryption is not enabled.",),
                success=False,
            )

        self._storage.apply_encryption_settings(settings)
        raw = self._read_raw_environments()
        inventory = self._inventory_from_raw(raw, settings)

        early = self._rewrite_early_skip(
            settings=settings,
            inventory=inventory,
            dry_run=dry_run,
            operation=operation,
            require_plaintext=require_plaintext,
            target_envelope_version=target_envelope_version,
        )
        if early is not None:
            return early

        inventory_failure = self._rewrite_inventory_failure(
            inventory=inventory,
            dry_run=dry_run,
            operation=operation,
        )
        if inventory_failure is not None:
            return inventory_failure

        environments, decrypt_errors = self._deserialize_records(raw)
        if decrypt_errors:
            return self._rewrite_decrypt_failure(
                inventory=inventory,
                decrypt_errors=decrypt_errors,
                dry_run=dry_run,
                operation=operation,
            )

        if dry_run:
            return self._rewrite_dry_run(
                settings=settings,
                inventory=inventory,
                environments=environments,
                operation=operation,
                target_envelope_version=target_envelope_version,
            )

        return self._rewrite_save(
            settings=settings,
            environments=environments,
            operation=operation,
            backup=backup,
            target_envelope_version=target_envelope_version,
        )

    def _read_raw_environments(self) -> list[dict[str, Any]]:
        path = self._storage.environments_file
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            return []
        return data

    def _scan_raw_environments(self, raw: list[dict[str, Any]]) -> EnvironmentInventory:
        kid_histogram: dict[str, int] = {}
        hidden_value_count = 0
        encrypted_envelope_count = 0
        v1_envelope_count = 0
        v2_envelope_count = 0
        plaintext_hidden_count = 0
        invalid_hidden_count = 0
        data_quality_errors: list[str] = []

        for item in raw:
            env_label = _environment_label(item)
            hidden_keys = set(item.get("hidden_keys") or [])
            variables = item.get("variables") or {}
            for key in hidden_keys:
                value = variables.get(key)
                if value is None:
                    continue
                hidden_value_count += 1
                if _is_encrypted_envelope(value):
                    encrypted_envelope_count += 1
                    envelope_version = value.get("v", 1)
                    if envelope_version == 2:
                        v2_envelope_count += 1
                    else:
                        v1_envelope_count += 1
                    kid = str(value.get("kid", ""))
                    if kid:
                        kid_histogram[kid] = kid_histogram.get(kid, 0) + 1
                elif isinstance(value, str):
                    plaintext_hidden_count += 1
                else:
                    invalid_hidden_count += 1
                    data_quality_errors.append(
                        _invalid_hidden_message(env_label, key, value)
                    )

        return EnvironmentInventory(
            environment_count=len(raw),
            hidden_value_count=hidden_value_count,
            encrypted_envelope_count=encrypted_envelope_count,
            v1_envelope_count=v1_envelope_count,
            v2_envelope_count=v2_envelope_count,
            plaintext_hidden_count=plaintext_hidden_count,
            invalid_hidden_count=invalid_hidden_count,
            kid_histogram=kid_histogram,
            missing_kids=frozenset(),
            data_quality_errors=tuple(data_quality_errors),
        )

    def _check_missing_kids(
        self,
        kid_histogram: dict[str, int],
        settings: AppSettings | None,
    ) -> frozenset[str]:
        if not kid_histogram:
            return frozenset()
        provider = build_key_provider(settings)
        missing: set[str] = set()
        for kid in kid_histogram:
            try:
                provider.get_key_by_id(kid)
            except EnvironmentEncryptionError:
                missing.add(kid)
        return frozenset(missing)

    def _deserialize_records(
        self,
        raw: list[dict[str, Any]],
    ) -> tuple[list[Environment], tuple[str, ...]]:
        environments, failures = self._storage.deserialize_environment_records(raw)
        errors = tuple(failure.format_operator_message() for failure in failures)
        return environments, errors

    def _deserialize_all(
        self,
        settings: AppSettings | None,
    ) -> tuple[list[Environment], tuple[str, ...]]:
        self._storage.apply_encryption_settings(settings)
        raw = self._read_raw_environments()
        return self._deserialize_records(raw)

    @staticmethod
    def _inventory_all_v2(inventory: EnvironmentInventory) -> bool:
        if inventory.invalid_hidden_count > 0:
            return False
        if inventory.plaintext_hidden_count > 0:
            return False
        if inventory.v1_envelope_count > 0:
            return False
        return inventory.hidden_value_count == 0 or inventory.v2_envelope_count > 0

    @staticmethod
    def _inventory_matches_active_kid(
        inventory: EnvironmentInventory,
        active_kid: str,
    ) -> bool:
        if inventory.invalid_hidden_count > 0:
            return False
        if inventory.plaintext_hidden_count > 0:
            return False
        if inventory.encrypted_envelope_count == 0:
            return inventory.hidden_value_count == 0
        hist = inventory.kid_histogram
        return len(hist) == 1 and hist.get(active_kid) == inventory.encrypted_envelope_count

    @staticmethod
    def _projected_inventory_after_encrypt(
        inventory: EnvironmentInventory,
        active_kid: str,
    ) -> EnvironmentInventory:
        encryptable = inventory.encrypted_envelope_count + inventory.plaintext_hidden_count
        kid_histogram = {active_kid: encryptable} if encryptable else {}
        return EnvironmentInventory(
            environment_count=inventory.environment_count,
            hidden_value_count=inventory.hidden_value_count,
            encrypted_envelope_count=encryptable,
            v1_envelope_count=encryptable,
            v2_envelope_count=0,
            plaintext_hidden_count=0,
            invalid_hidden_count=inventory.invalid_hidden_count,
            kid_histogram=kid_histogram,
            missing_kids=frozenset(),
            data_quality_errors=inventory.data_quality_errors,
        )

    @staticmethod
    def _projected_inventory_after_v2_upgrade(
        inventory: EnvironmentInventory,
        active_kid: str,
    ) -> EnvironmentInventory:
        encryptable = inventory.hidden_value_count
        kid_histogram = {active_kid: encryptable} if encryptable else {}
        return EnvironmentInventory(
            environment_count=inventory.environment_count,
            hidden_value_count=inventory.hidden_value_count,
            encrypted_envelope_count=encryptable,
            v1_envelope_count=0,
            v2_envelope_count=encryptable,
            plaintext_hidden_count=0,
            invalid_hidden_count=inventory.invalid_hidden_count,
            kid_histogram=kid_histogram,
            missing_kids=frozenset(),
            data_quality_errors=inventory.data_quality_errors,
        )

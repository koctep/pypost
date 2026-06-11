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
from pypost.core.storage import StorageManager
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

    def __init__(self, storage: StorageManager) -> None:
        self._storage = storage

    def build_inventory(self, settings: AppSettings | None) -> EnvironmentInventory:
        self._storage.apply_encryption_settings(settings)
        raw = self._read_raw_environments()
        inventory = self._scan_raw_environments(raw)
        missing = self._check_missing_kids(inventory.kid_histogram, settings)
        inventory = replace(inventory, missing_kids=missing)
        _log_inventory("encryption_migration_inventory_built", inventory)
        return inventory

    def verify_decrypt_access(self, settings: AppSettings | None) -> MigrationReport:
        logger.info("encryption_migration_verify_started")
        inventory = self.build_inventory(settings)
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
            _, decrypt_errors = self._deserialize_all(settings)
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

    def _rewrite_environments(
        self,
        settings: AppSettings | None,
        *,
        dry_run: bool,
        backup: bool,
        require_plaintext: bool,
        target_envelope_version: int | None = None,
    ) -> MigrationReport:
        if target_envelope_version == 2:
            operation = "upgrade_v2"
        elif require_plaintext:
            operation = "encrypt_plaintext"
        else:
            operation = "re_encrypt"
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

        inventory = self.build_inventory(settings)
        if require_plaintext and inventory.plaintext_hidden_count == 0:
            logger.info(
                "encryption_migration_operation_skipped operation=%s reason=no_plaintext_hidden",
                operation,
            )
            return MigrationReport(
                inventory=inventory,
                dry_run=dry_run,
                backup_path=None,
                errors=(),
                success=True,
            )

        if target_envelope_version == 2 and self._inventory_all_v2(inventory):
            logger.info(
                "encryption_migration_operation_skipped operation=%s reason=already_v2",
                operation,
            )
            return MigrationReport(
                inventory=inventory,
                dry_run=dry_run,
                backup_path=None,
                errors=(),
                success=True,
                reencrypt_stats=ReencryptStats(
                    encrypted_count=0,
                    reused_count=inventory.hidden_value_count,
                ),
            )

        if not require_plaintext and target_envelope_version != 2:
            active_kid = build_key_provider(settings).get_current_key().key_id
            if self._inventory_matches_active_kid(inventory, active_kid):
                logger.info(
                    "encryption_migration_operation_skipped operation=%s "
                    "reason=already_on_active_kid active_kid=%s",
                    operation,
                    active_kid,
                )
                return MigrationReport(
                    inventory=inventory,
                    dry_run=dry_run,
                    backup_path=None,
                    errors=(),
                    success=True,
                    reencrypt_stats=ReencryptStats(
                        encrypted_count=0,
                        reused_count=inventory.hidden_value_count,
                    ),
                )

        quality_errors = inventory.data_quality_errors
        if quality_errors or inventory.missing_kids:
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

        environments, decrypt_errors = self._deserialize_all(settings)
        if decrypt_errors:
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

        backup_path = None
        if backup and not dry_run:
            backup_path = backup_environments_file(self._storage.environments_file)

        if dry_run:
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

    def _deserialize_all(
        self,
        settings: AppSettings | None,
    ) -> tuple[list[Environment], tuple[str, ...]]:
        self._storage.apply_encryption_settings(settings)
        environments, failures = self._storage.load_environments_with_errors()
        errors = tuple(failure.format_operator_message() for failure in failures)
        return environments, errors

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

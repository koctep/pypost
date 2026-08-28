from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from pypost.core.encryption_config import (
    build_key_provider,
    resolve_encryption_enabled,
    resolve_key_source,
    resolve_key_source_chain,
)
from pypost.core.environment_secrets_codec import EnvironmentSecretsCodec
from pypost.core.key_provider import EnvironmentEncryptionError
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.models.models import Environment
from pypost.models.settings import AppSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EnvironmentSerializeStats:
    encrypted_count: int = 0
    reused_count: int = 0

    def __add__(self, other: "EnvironmentSerializeStats") -> "EnvironmentSerializeStats":
        return EnvironmentSerializeStats(
            encrypted_count=self.encrypted_count + other.encrypted_count,
            reused_count=self.reused_count + other.reused_count,
        )


class EnvironmentVariablesAdapter:
    """Serializes and deserializes environment variables with optional encryption."""

    def __init__(self, metrics: MetricsTrackerProtocol | None = None) -> None:
        self._metrics = resolve_metrics(metrics)
        self._encryption_settings: AppSettings | None = None
        self._secrets_codec = EnvironmentSecretsCodec(build_key_provider(None))
        self._persisted_variables: dict[str, dict[str, Any]] = {}
        self._persisted_plaintext: dict[str, dict[str, str]] = {}

    def apply_encryption_settings(self, settings: AppSettings | None) -> None:
        self.clear_persisted_state()
        self._encryption_settings = settings
        key_source = resolve_key_source(settings)
        source_chain = resolve_key_source_chain(settings)
        self._secrets_codec = EnvironmentSecretsCodec(build_key_provider(settings))
        enabled = resolve_encryption_enabled(settings)
        policy_source = (
            "settings"
            if settings is not None and settings.env_encryption_enabled is not None
            else "env_fallback"
        )
        logger.info(
            "storage_encryption_config_applied enabled=%s key_source=%s "
            "source_chain=%s policy_source=%s",
            enabled,
            key_source,
            ",".join(source_chain),
            policy_source,
        )

    def remember_environment_state(
        self,
        env_id: str,
        raw_variables: dict[str, Any],
        plaintext_variables: dict[str, str],
    ) -> None:
        self._persisted_variables[env_id] = dict(raw_variables)
        self._persisted_plaintext[env_id] = dict(plaintext_variables)

    def clear_persisted_state(self) -> None:
        self._persisted_variables.clear()
        self._persisted_plaintext.clear()

    def serialize_environment(
        self,
        env: Environment,
        *,
        target_envelope_version: int | None = None,
    ) -> tuple[dict[str, Any], EnvironmentSerializeStats]:
        payload = env.model_dump(mode="json")
        variables: dict[str, Any] = dict(payload.get("variables", {}))
        hidden_keys = set(env.hidden_keys)
        should_encrypt = self._is_encryption_enabled()
        encrypted_count = 0
        reused_count = 0
        active_kid = self._active_key_id() if should_encrypt else None
        previous_variables = self._persisted_variables.get(env.id, {})
        previous_plaintext = self._persisted_plaintext.get(env.id, {})

        serialized_variables: dict[str, Any] = {}
        for key, value in variables.items():
            if should_encrypt and key in hidden_keys:
                current_plaintext = str(value)
                previous_payload = previous_variables.get(key)
                if self._can_reuse_encrypted_envelope(
                    current_plaintext,
                    previous_plaintext.get(key),
                    previous_payload,
                    active_kid=active_kid,
                    target_envelope_version=target_envelope_version,
                ):
                    serialized_variables[key] = previous_payload
                    reused_count += 1
                    continue
                try:
                    if target_envelope_version == 1:
                        envelope = self._secrets_codec.encrypt_v1(current_plaintext)
                    else:
                        envelope = self._secrets_codec.encrypt(current_plaintext)
                    serialized_variables[key] = envelope.to_json()
                    encrypted_count += 1
                    self._metrics.track_environment_value_encryption()
                except EnvironmentEncryptionError as exc:
                    self._metrics.track_environment_encryption_error(
                        "save",
                        "encrypt_failed",
                    )
                    logger.error(
                        "environment_value_encrypt_failed env_name=%s key=%s error=%s",
                        env.name,
                        key,
                        exc,
                    )
                    raise
            else:
                serialized_variables[key] = str(value)

        payload["variables"] = serialized_variables
        logger.info(
            "environment_serialized env_name=%s encryption_enabled=%s encrypted_count=%d "
            "reused_count=%d total_variables=%d",
            env.name,
            should_encrypt,
            encrypted_count,
            reused_count,
            len(serialized_variables),
        )
        return payload, EnvironmentSerializeStats(
            encrypted_count=encrypted_count,
            reused_count=reused_count,
        )

    def deserialize_environment(self, raw_env: dict[str, Any]) -> Environment:
        variables_raw: dict[str, Any] = dict(raw_env.get("variables", {}))
        decoded_variables: dict[str, str] = {}
        decrypted_count = 0
        for key, value in variables_raw.items():
            decoded_value, decrypted = self._decode_variable_value(key, value)
            decoded_variables[str(key)] = decoded_value
            if decrypted:
                decrypted_count += 1

        normalized = dict(raw_env)
        normalized["variables"] = decoded_variables
        logger.info(
            "environment_deserialized env_name=%s decrypted_count=%d total_variables=%d",
            normalized.get("name", "unknown"),
            decrypted_count,
            len(decoded_variables),
        )
        return Environment(**normalized)

    def _is_encryption_enabled(self) -> bool:
        return resolve_encryption_enabled(self._encryption_settings)

    def _active_key_id(self) -> str | None:
        try:
            return self._secrets_codec._key_provider.get_current_key().key_id
        except EnvironmentEncryptionError:
            return None

    @staticmethod
    def _can_reuse_encrypted_envelope(
        current_plaintext: str,
        previous_plaintext: str | None,
        previous_payload: Any,
        *,
        active_kid: str | None = None,
        target_envelope_version: int | None = None,
    ) -> bool:
        if previous_plaintext != current_plaintext:
            return False
        if not isinstance(previous_payload, dict):
            return False
        if previous_payload.get("enc") is not True:
            return False
        if target_envelope_version is not None:
            previous_version = previous_payload.get("v", 1)
            if previous_version != target_envelope_version:
                return False
        if active_kid is not None:
            return str(previous_payload.get("kid", "")) == active_kid
        return True

    def _decode_variable_value(self, key: str, value: Any) -> tuple[str, bool]:
        if isinstance(value, str):
            return value, False
        if isinstance(value, dict) and value.get("enc") is True:
            try:
                decoded = self._secrets_codec.decrypt(value)
                self._metrics.track_environment_value_decryption()
                return decoded, True
            except EnvironmentEncryptionError as exc:
                self._metrics.track_environment_encryption_error(
                    "load",
                    "decrypt_failed",
                )
                raise EnvironmentEncryptionError(
                    f"Failed to decrypt environment variable '{key}': {exc}"
                ) from exc
        self._metrics.track_environment_encryption_error(
            "load",
            "unsupported_format",
        )
        raise EnvironmentEncryptionError(
            f"Unsupported value format for environment variable '{key}'."
        )

import logging
from typing import TYPE_CHECKING, Any

from pypost.core.encryption_config import (
    build_key_provider,
    resolve_encryption_enabled,
    resolve_key_source,
    resolve_key_source_chain,
)
from pypost.core.environment_secrets_codec import EnvironmentSecretsCodec
from pypost.core.key_provider import EnvironmentEncryptionError
from pypost.models.models import Environment
from pypost.models.settings import AppSettings

if TYPE_CHECKING:
    from pypost.core.metrics import MetricsManager

logger = logging.getLogger(__name__)


class EnvironmentVariablesAdapter:
    """Serializes and deserializes environment variables with optional encryption."""

    def __init__(self, metrics: "MetricsManager | None" = None) -> None:
        self._metrics = metrics
        self._encryption_settings: AppSettings | None = None
        self._secrets_codec = EnvironmentSecretsCodec(build_key_provider(None))

    def apply_encryption_settings(self, settings: AppSettings | None) -> None:
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

    def serialize_environment(self, env: Environment) -> dict[str, Any]:
        payload = env.model_dump(mode="json")
        variables: dict[str, Any] = dict(payload.get("variables", {}))
        hidden_keys = set(env.hidden_keys)
        should_encrypt = self._is_encryption_enabled()
        encrypted_count = 0

        serialized_variables: dict[str, Any] = {}
        for key, value in variables.items():
            if should_encrypt and key in hidden_keys:
                try:
                    envelope = self._secrets_codec.encrypt(str(value))
                    serialized_variables[key] = envelope.to_json()
                    encrypted_count += 1
                    if self._metrics:
                        self._metrics.track_environment_value_encryption()
                except EnvironmentEncryptionError as exc:
                    if self._metrics:
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
            "total_variables=%d",
            env.name,
            should_encrypt,
            encrypted_count,
            len(serialized_variables),
        )
        return payload

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

    def _decode_variable_value(self, key: str, value: Any) -> tuple[str, bool]:
        if isinstance(value, str):
            return value, False
        if isinstance(value, dict) and value.get("enc") is True:
            try:
                decoded = self._secrets_codec.decrypt(value)
                if self._metrics:
                    self._metrics.track_environment_value_decryption()
                return decoded, True
            except EnvironmentEncryptionError as exc:
                if self._metrics:
                    self._metrics.track_environment_encryption_error(
                        "load",
                        "decrypt_failed",
                    )
                raise EnvironmentEncryptionError(
                    f"Failed to decrypt environment variable '{key}': {exc}"
                ) from exc
        if self._metrics:
            self._metrics.track_environment_encryption_error(
                "load",
                "unsupported_format",
            )
        raise EnvironmentEncryptionError(
            f"Unsupported value format for environment variable '{key}'."
        )

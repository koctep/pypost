import os
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, List
from platformdirs import user_data_dir

from pypost.core.environment_secrets_codec import EnvironmentSecretsCodec
from pypost.core.key_provider import EnvironmentEncryptionError, LocalKeyProvider
from pypost.models.models import Collection, Environment

if TYPE_CHECKING:
    from pypost.core.metrics import MetricsManager

logger = logging.getLogger(__name__)


class StorageManager:
    ENCRYPTION_FLAG_ENV = "PYPOST_ENV_ENCRYPTION_ENABLED"

    def __init__(
        self,
        app_name: str = "pypost",
        app_author=None,
        metrics: "MetricsManager | None" = None,
    ):
        self.data_dir = Path(user_data_dir(app_name, app_author))
        self.collections_path = self.data_dir / "collections"
        self.environments_file = self.data_dir / "environments.json"
        self._metrics = metrics
        self._codec = EnvironmentSecretsCodec(LocalKeyProvider())
        self._ensure_paths()

    def _ensure_paths(self):
        if not self.data_dir.exists():
            try:
                self.data_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error("storage_data_dir_create_failed path=%s error=%s", self.data_dir, e)

        if not self.collections_path.exists():
            try:
                self.collections_path.mkdir(exist_ok=True)
            except Exception as e:
                logger.error(
                    "storage_collections_dir_create_failed path=%s error=%s",
                    self.collections_path,
                    e,
                )

        if not self.environments_file.exists():
            try:
                with open(self.environments_file, 'w') as f:
                    json.dump([], f)
            except Exception as e:
                logger.error(
                    "storage_environments_file_create_failed path=%s error=%s",
                    self.environments_file,
                    e,
                )

    def save_collection(self, collection: Collection):
        # Ensure collections directory exists before saving (in case it was deleted)
        if not self.collections_path.exists():
            self.collections_path.mkdir(exist_ok=True, parents=True)

        # Simplification: using collection name as filename.
        file_path = self.collections_path / f"{collection.name}.json"
        with open(file_path, 'w') as f:
            f.write(collection.model_dump_json(indent=2))

    def delete_collection(self, collection_name: str):
        file_path = self.collections_path / f"{collection_name}.json"
        if file_path.exists():
            file_path.unlink()

    def load_collections(self) -> List[Collection]:
        collections = []
        if not self.collections_path.exists():
            return collections

        for filename in os.listdir(self.collections_path):
            if filename.endswith(".json"):
                try:
                    with open(self.collections_path / filename, 'r') as f:
                        data = json.load(f)
                        collections.append(Collection(**data))
                except Exception as e:
                    logger.warning(
                        "storage_collection_load_failed filename=%s error=%s",
                        filename,
                        e,
                    )
        return collections

    def save_environments(self, environments: List[Environment]):
        data = [self._serialize_environment(env) for env in environments]
        tmp_file = self.environments_file.with_suffix(".json.tmp")
        with open(tmp_file, 'w') as f:
            json.dump(data, f, indent=2)
        try:
            os.replace(tmp_file, self.environments_file)
        except Exception as e:
            logger.error(
                "save_environments_replace_failed src=%s dst=%s error=%s",
                tmp_file,
                self.environments_file,
                e,
            )
            if tmp_file.exists():
                tmp_file.unlink(missing_ok=True)
            raise
        logger.info(
            "save_environments_completed count=%d file=%s",
            len(environments),
            self.environments_file,
        )

    def load_environments(self) -> List[Environment]:
        if not self.environments_file.exists():
            return []
        try:
            with open(self.environments_file, 'r') as f:
                data = json.load(f)
                environments = [self._deserialize_environment(item) for item in data]
                logger.info(
                    "load_environments_completed count=%d file=%s",
                    len(environments),
                    self.environments_file,
                )
                return environments
        except Exception as e:
            logger.error(
                "load_environments_failed file=%s error=%s",
                self.environments_file,
                e,
            )
            return []

    @classmethod
    def _is_encryption_enabled(cls) -> bool:
        value = os.getenv(cls.ENCRYPTION_FLAG_ENV, "").strip().lower()
        return value in {"1", "true", "yes", "on"}

    def _serialize_environment(self, env: Environment) -> dict[str, Any]:
        payload = env.model_dump(mode="json")
        variables: dict[str, Any] = dict(payload.get("variables", {}))
        hidden_keys = set(env.hidden_keys)
        should_encrypt = self._is_encryption_enabled()
        encrypted_count = 0

        serialized_variables: dict[str, Any] = {}
        for key, value in variables.items():
            if should_encrypt and key in hidden_keys:
                try:
                    envelope = self._codec.encrypt(str(value))
                    serialized_variables[key] = envelope.to_json()
                    encrypted_count += 1
                    if self._metrics:
                        self._metrics.track_environment_value_encryption()
                except EnvironmentEncryptionError as exc:
                    if self._metrics:
                        self._metrics.track_environment_encryption_error(
                            "save", "encrypt_failed",
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

    def _deserialize_environment(self, raw_env: dict[str, Any]) -> Environment:
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

    def _decode_variable_value(self, key: str, value: Any) -> tuple[str, bool]:
        if isinstance(value, str):
            return value, False
        if isinstance(value, dict) and value.get("enc") is True:
            try:
                decoded = self._codec.decrypt(value)
                if self._metrics:
                    self._metrics.track_environment_value_decryption()
                return decoded, True
            except EnvironmentEncryptionError as exc:
                if self._metrics:
                    self._metrics.track_environment_encryption_error(
                        "load", "decrypt_failed",
                    )
                raise EnvironmentEncryptionError(
                    f"Failed to decrypt environment variable '{key}': {exc}"
                ) from exc
        if self._metrics:
            self._metrics.track_environment_encryption_error(
                "load", "unsupported_format",
            )
        raise EnvironmentEncryptionError(
            f"Unsupported value format for environment variable '{key}'."
        )

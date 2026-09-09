from __future__ import annotations

import errno
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from platformdirs import user_config_dir

from pypost.core.settings_secrets import parse_settings_from_disk, serialize_settings_for_disk
from pypost.models.settings import AppSettings

logger = logging.getLogger(__name__)


class StrictConfigError(Exception):
    def __init__(self, path: Path, category: str) -> None:
        self.path = path
        self.category = category
        super().__init__(f"settings failure path={path} category={category}")


class ConfigPersistenceError(Exception):
    """A settings write that did not replace the authoritative file."""

    def __init__(self, path: Path, operation: str) -> None:
        self.path = path
        self.operation = operation
        super().__init__(f"Could not save settings ({operation}) to {path}")


@dataclass(frozen=True)
class ConfigRecoveryNotice:
    """Describes recovery from a settings file that could not be parsed."""

    original_path: Path
    quarantine_path: Path | None
    category: str


class ConfigManager:
    """Serialized, crash-safe access to the single settings JSON document."""

    def __init__(
        self,
        app_name="pypost",
        app_author=None,
        *,
        config_dir: Path | str | None = None,
    ):
        if config_dir is not None:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(user_config_dir(app_name, app_author))
        self.config_path = self.config_dir / "settings.json"
        self.recovery_notice: ConfigRecoveryNotice | None = None
        self._write_lock = RLock()
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        if not self.config_dir.exists():
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                logger.error(
                    "config_directory_create_failed path=%s error=%s",
                    self.config_dir,
                    exc,
                )

    def load_config(self) -> AppSettings:
        """Load settings, quarantining malformed content before using defaults."""
        self.recovery_notice = None
        try:
            return self.load_config_strict()
        except StrictConfigError as exc:
            quarantine_path = None
            if exc.category in {"malformed_json", "invalid_root", "invalid_settings"}:
                quarantine_path = self._quarantine_corrupt_config()
            self.recovery_notice = ConfigRecoveryNotice(
                original_path=self.config_path,
                quarantine_path=quarantine_path,
                category=exc.category,
            )
            logger.error(
                "config_load_failed path=%s category=%s quarantine_path=%s",
                self.config_path,
                exc.category,
                quarantine_path,
            )
            return AppSettings()

    def load_config_strict(self) -> AppSettings:
        if not self.config_path.exists():
            return AppSettings()
        try:
            with open(self.config_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                raise StrictConfigError(self.config_path, "invalid_root")
            return parse_settings_from_disk(data)
        except StrictConfigError:
            raise
        except json.JSONDecodeError as exc:
            raise StrictConfigError(self.config_path, "malformed_json") from exc
        except OSError as exc:
            raise StrictConfigError(self.config_path, "unreadable") from exc
        except Exception as exc:
            raise StrictConfigError(self.config_path, "invalid_settings") from exc

    def save_config(self, settings: AppSettings) -> None:
        """Atomically persist a revision without mutating it on failed writes."""
        with self._write_lock:
            persisted = settings.model_copy(deep=True)
            persisted.revision = settings.revision + 1
            temporary_path: Path | None = None
            operation = "create_temporary_file"
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
                descriptor, raw_path = tempfile.mkstemp(
                    prefix=f".{self.config_path.name}.",
                    suffix=".tmp",
                    dir=self.config_dir,
                )
                temporary_path = Path(raw_path)
                operation = "write_temporary_file"
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    json.dump(serialize_settings_for_disk(persisted), handle, indent=4)
                    handle.flush()
                    os.fsync(handle.fileno())
                operation = "replace_settings_file"
                os.replace(temporary_path, self.config_path)
                temporary_path = None
                self._fsync_config_directory()
            except Exception as exc:
                if temporary_path is not None:
                    try:
                        temporary_path.unlink(missing_ok=True)
                    except OSError:
                        logger.warning(
                            "config_temporary_cleanup_failed path=%s",
                            temporary_path,
                            exc_info=True,
                        )
                logger.error(
                    "config_save_failed path=%s operation=%s error=%s",
                    self.config_path,
                    operation,
                    exc,
                )
                raise ConfigPersistenceError(self.config_path, operation) from exc
            settings.revision = persisted.revision

    def _fsync_config_directory(self) -> None:
        """Persist the rename when the platform supports directory fsync."""
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        try:
            descriptor = os.open(self.config_dir, flags)
        except OSError as exc:
            if exc.errno in {errno.EINVAL, errno.ENOTSUP, errno.EOPNOTSUPP}:
                return
            logger.warning(
                "config_directory_fsync_open_failed path=%s error=%s",
                self.config_dir,
                exc,
            )
            return
        try:
            os.fsync(descriptor)
        except OSError as exc:
            if exc.errno not in {errno.EINVAL, errno.ENOTSUP, errno.EOPNOTSUPP}:
                logger.warning(
                    "config_directory_fsync_failed path=%s error=%s",
                    self.config_dir,
                    exc,
                )
        finally:
            os.close(descriptor)

    def _quarantine_corrupt_config(self) -> Path | None:
        if not self.config_path.exists():
            return None
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        destination = self.config_path.with_name(
            f"{self.config_path.name}.corrupt-{timestamp}"
        )
        try:
            os.replace(self.config_path, destination)
        except OSError as exc:
            logger.error(
                "config_quarantine_failed path=%s destination=%s error=%s",
                self.config_path,
                destination,
                exc,
            )
            return None
        logger.warning(
            "config_quarantined path=%s destination=%s",
            self.config_path,
            destination,
        )
        return destination

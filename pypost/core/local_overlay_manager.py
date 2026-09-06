"""Local secret and variable overlay persistence manager (PYPOST-1221).

Manages user-local overlays stored under ~/.pypost/libraries_data/<library-id>/overlay.json,
providing secure file permissions (0o600 / 0o700) and atomic writes.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import shutil
from typing import TYPE_CHECKING, Any, Optional
import uuid

from pypost.models.library_manifest import LocalLibraryOverlay

if TYPE_CHECKING:
    from pypost.core.environment_secrets_codec import EnvironmentSecretsCodec

logger = logging.getLogger(__name__)

__all__ = ["LocalOverlayManager"]


class LocalOverlayManager:
    """Manages persistent local configuration and secret overlays for collection libraries."""

    def __init__(
        self,
        base_dir: Optional[Path | str] = None,
        secrets_codec: Optional[EnvironmentSecretsCodec] = None,
    ) -> None:
        """Initialize LocalOverlayManager with a base storage directory and optional secrets codec.

        Args:
            base_dir: Root directory for library overlays. Defaults to ~/.pypost/libraries_data.
            secrets_codec: Optional codec for encrypting sensitive secrets at rest.
        """
        if base_dir is not None:
            self.base_dir = Path(base_dir).expanduser().resolve()
        else:
            self.base_dir = (Path.home() / ".pypost" / "libraries_data").resolve()
        self.secrets_codec = secrets_codec

    def _library_dir(self, library_id: str) -> Path:
        """Get the directory path for a library's local overlay."""
        return self.base_dir / library_id

    def _overlay_path(self, library_id: str) -> Path:
        """Get the overlay.json file path for a library."""
        return self._library_dir(library_id) / "overlay.json"

    def get_overlay(self, library_id: str) -> LocalLibraryOverlay:
        """Load the local overlay for a library ID, returning default overlay if none exists."""
        path = self._overlay_path(library_id)
        if not path.is_file():
            logger.debug(
                "overlay_not_found library_id=%s path=%s default_used=true",
                library_id,
                path,
            )
            return LocalLibraryOverlay(library_id=library_id)

        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
            if not isinstance(data, dict):
                logger.warning(
                    "overlay_invalid_root library_id=%s path=%s type=%s",
                    library_id,
                    path,
                    type(data).__name__,
                )
                return LocalLibraryOverlay(library_id=library_id)
            raw_secrets = data.get("secrets", {})
            if isinstance(raw_secrets, dict) and self.secrets_codec is not None:
                decrypted_secrets: dict[str, Any] = {}
                for key, val in raw_secrets.items():
                    if isinstance(val, dict) and val.get("enc") is True:
                        try:
                            decrypted_secrets[key] = self.secrets_codec.decrypt(val)
                        except Exception as exc:
                            logger.warning(
                                "overlay_secret_decrypt_failed library_id=%s key=%s reason=%s",
                                library_id,
                                key,
                                exc,
                            )
                            decrypted_secrets[key] = val
                    else:
                        decrypted_secrets[key] = val
                data["secrets"] = decrypted_secrets

            overlay = LocalLibraryOverlay(**data)
            logger.info(
                "overlay_loaded library_id=%s path=%s secrets_count=%d "
                "overrides_count=%d active_profile=%s",
                library_id,
                path,
                len(overlay.secrets),
                len(overlay.overrides),
                overlay.active_profile,
            )
            return overlay
        except Exception as exc:
            logger.warning(
                "overlay_load_failed library_id=%s path=%s reason=%s",
                library_id,
                path,
                exc,
            )
            return LocalLibraryOverlay(library_id=library_id)

    def load_overlay(self, library_id: str) -> LocalLibraryOverlay:
        """Alias for get_overlay."""
        return self.get_overlay(library_id)

    def save_overlay(self, overlay: LocalLibraryOverlay) -> Path:
        """Atomically persist a LocalLibraryOverlay with restricted 0o600 file permissions.

        Args:
            overlay: The overlay instance to persist.

        Returns:
            Path: The path to the saved overlay.json file.
        """
        target_dir = self._library_dir(overlay.library_id)
        target_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name == "posix":
            try:
                os.chmod(target_dir, 0o700)
                logger.debug(
                    "overlay_directory_permissions_applied path=%s mode=0o700",
                    target_dir,
                )
            except OSError as exc:
                logger.debug(
                    "overlay_chmod_failed path=%s reason=%s",
                    target_dir,
                    exc,
                )

        target_file = self._overlay_path(overlay.library_id)
        tmp_file = target_dir / f"overlay.json.tmp.{uuid.uuid4().hex}"

        payload = overlay.model_dump()
        if self.secrets_codec is not None and isinstance(overlay.secrets, dict):
            encrypted_secrets: dict[str, Any] = {}
            for key, val in overlay.secrets.items():
                if isinstance(val, dict) and val.get("enc") is True:
                    encrypted_secrets[key] = val
                elif isinstance(val, str):
                    try:
                        encrypted_secrets[key] = self.secrets_codec.encrypt(val).to_json()
                    except Exception as exc:
                        logger.warning(
                            "overlay_secret_encrypt_failed library_id=%s key=%s reason=%s",
                            overlay.library_id,
                            key,
                            exc,
                        )
                        encrypted_secrets[key] = val
                else:
                    encrypted_secrets[key] = val
            payload["secrets"] = encrypted_secrets

        content = json.dumps(payload, indent=2)

        try:
            if os.name == "posix":
                flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
                fd = os.open(tmp_file, flags, 0o600)
                with open(fd, "w", encoding="utf-8") as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                os.chmod(tmp_file, 0o600)
            else:
                with open(tmp_file, "w", encoding="utf-8") as f:
                    f.write(content)
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except OSError:
                        pass

            os.replace(tmp_file, target_file)
            try:
                directory_fd = os.open(target_dir, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                pass
            if os.name == "posix":
                try:
                    os.chmod(target_file, 0o600)
                    logger.debug(
                        "overlay_file_permissions_applied path=%s mode=0o600",
                        target_file,
                    )
                except OSError as exc:
                    logger.debug(
                        "overlay_chmod_failed path=%s reason=%s",
                        target_file,
                        exc,
                    )
        finally:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except OSError:
                    pass

        logger.info(
            "overlay_saved library_id=%s path=%s secrets_count=%d overrides_count=%d",
            overlay.library_id,
            target_file,
            len(overlay.secrets),
            len(overlay.overrides),
        )
        return target_file

    def set_active_profile(
        self, library_id: str, profile_name: Optional[str]
    ) -> LocalLibraryOverlay:
        """Set or update the active preset profile in the library's local overlay."""
        overlay = self.get_overlay(library_id)
        overlay.active_profile = profile_name
        self.save_overlay(overlay)
        logger.debug(
            "overlay_active_profile_updated library_id=%s profile=%s",
            library_id,
            profile_name,
        )
        return overlay

    def set_secret(
        self, library_id: str, key: str, value: Any
    ) -> LocalLibraryOverlay:
        """Set a secret credential in the library's local overlay."""
        overlay = self.get_overlay(library_id)
        overlay.secrets[key] = value
        self.save_overlay(overlay)
        logger.debug(
            "overlay_secret_updated library_id=%s key=%s",
            library_id,
            key,
        )
        return overlay

    def set_override(
        self, library_id: str, key: str, value: Any
    ) -> LocalLibraryOverlay:
        """Set a local non-secret variable override in the library's local overlay."""
        overlay = self.get_overlay(library_id)
        overlay.overrides[key] = value
        self.save_overlay(overlay)
        logger.debug(
            "overlay_override_updated library_id=%s key=%s",
            library_id,
            key,
        )
        return overlay

    def set_variable_override(
        self, library_id: str, name: str, value: Any, is_secret: bool = False
    ) -> LocalLibraryOverlay:
        """Set a variable override or secret depending on is_secret flag."""
        if is_secret:
            return self.set_secret(library_id, name, value)
        return self.set_override(library_id, name, value)

    def get_variable_override(
        self, library_id: str, name: str
    ) -> Optional[Any]:
        """Get an override or secret value from the overlay."""
        overlay = self.get_overlay(library_id)
        if name in overlay.secrets:
            return overlay.secrets[name]
        return overlay.overrides.get(name)

    def remove_secret(self, library_id: str, key: str) -> LocalLibraryOverlay:
        """Remove a secret from the library's local overlay."""
        overlay = self.get_overlay(library_id)
        if key in overlay.secrets:
            del overlay.secrets[key]
            self.save_overlay(overlay)
            logger.debug(
                "overlay_secret_removed library_id=%s key=%s",
                library_id,
                key,
            )
        return overlay

    def remove_override(self, library_id: str, key: str) -> LocalLibraryOverlay:
        """Remove a variable override from the library's local overlay."""
        overlay = self.get_overlay(library_id)
        if key in overlay.overrides:
            del overlay.overrides[key]
            self.save_overlay(overlay)
            logger.debug(
                "overlay_override_removed library_id=%s key=%s",
                library_id,
                key,
            )
        return overlay

    def delete_overlay(self, library_id: str) -> bool:
        """Delete a library's local overlay storage directory from disk."""
        target_dir = self._library_dir(library_id)
        if not target_dir.exists():
            logger.debug(
                "overlay_delete_skipped_not_found library_id=%s path=%s",
                library_id,
                target_dir,
            )
            return False

        try:
            shutil.rmtree(target_dir)
            logger.info("overlay_deleted library_id=%s path=%s", library_id, target_dir)
            return True
        except OSError as exc:
            logger.warning(
                "overlay_delete_failed library_id=%s path=%s reason=%s",
                library_id,
                target_dir,
                exc,
            )
            return False

    def list_library_overlays(self) -> list[str]:
        """List all library IDs with existing overlay configurations."""
        if not self.base_dir.is_dir():
            return []

        library_ids: list[str] = []
        for entry in self.base_dir.iterdir():
            if entry.is_dir() and (entry / "overlay.json").is_file():
                library_ids.append(entry.name)
        return library_ids

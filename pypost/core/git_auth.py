"""Transient hybrid Git authentication environment manager (PYPOST-1222).

Provides credential isolation and non-interactive process environment configuration
for Git operations supporting system SSH agent, Personal Access Tokens (via GIT_ASKPASS),
and custom SSH private keys (via GIT_SSH_COMMAND).
"""
from __future__ import annotations

import logging
import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Generator, Optional

from pypost.models.git_library import GitAuthConfig, GitAuthMode

logger = logging.getLogger(__name__)

__all__ = [
    "GitAuthEnvironmentManager",
    "transient_git_auth_env",
]


class GitAuthEnvironmentManager:
    """Manages ephemeral subprocess environment variables and credential helpers for Git."""

    def __init__(self) -> None:
        pass

    def build_env(
        self, config: Optional[GitAuthConfig] = None
    ) -> tuple[dict[str, str], Optional[Callable[[], None]]]:
        """Build an isolated environment dictionary for Git subprocess execution.

        Args:
            config: Optional authentication configuration.

        Returns:
            tuple[dict[str, str], Optional[Callable[[], None]]]:
                The environment dict and an optional cleanup callback.
        """
        env = dict(os.environ)
        # Always enforce non-interactive terminal prompt and immediate stream flush
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_FLUSH"] = "1"

        if config is None or config.mode == GitAuthMode.SSH_AGENT:
            logger.debug("git_auth_mode_configured mode=SSH_AGENT")
            return env, None

        cleanup_callbacks: list[Callable[[], None]] = []

        if config.mode == GitAuthMode.PAT:
            temp_dir = tempfile.mkdtemp(prefix="pypost_askpass_")
            script_path = Path(temp_dir) / "askpass.py"
            # Create executable Python askpass script
            python_bin = sys.executable
            script_content = f"""#!{python_bin}
import os
import sys

prompt = sys.argv[1] if len(sys.argv) > 1 else ""
prompt_lower = prompt.lower()
if "username" in prompt_lower:
    print(os.environ.get("PYPOST_GIT_ASKPASS_USERNAME", ""))
else:
    print(os.environ.get("PYPOST_GIT_ASKPASS_TOKEN", ""))
"""
            script_path.write_text(script_content, encoding="utf-8")
            os.chmod(script_path, 0o700)
            logger.debug("git_auth_askpass_created mode=PAT path=%s", script_path)

            env["GIT_ASKPASS"] = str(script_path)
            if config.token:
                env["PYPOST_GIT_ASKPASS_TOKEN"] = config.token
            if config.username:
                env["PYPOST_GIT_ASKPASS_USERNAME"] = config.username

            def cleanup_pat() -> None:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.debug("git_auth_askpass_cleaned mode=PAT path=%s", temp_dir)

            cleanup_callbacks.append(cleanup_pat)
            logger.debug(
                "git_auth_mode_configured mode=PAT username=%s has_token=%s",
                config.username or "none",
                bool(config.token),
            )

        elif config.mode == GitAuthMode.CUSTOM_SSH_KEY:
            ssh_opts = ["-o IdentitiesOnly=yes"]
            if config.strict_host_checking:
                ssh_opts.append("-o StrictHostKeyChecking=accept-new")
            else:
                ssh_opts.append("-o StrictHostKeyChecking=no")

            if config.key_path:
                key_path = Path(config.key_path).expanduser().resolve()
                ssh_opts.insert(0, f"-i {key_path}")

            if config.passphrase:
                # Setup askpass for SSH passphrase if needed
                temp_dir = tempfile.mkdtemp(prefix="pypost_ssh_askpass_")
                script_path = Path(temp_dir) / "ssh_askpass.py"
                python_bin = sys.executable
                script_content = f"""#!{python_bin}
import os
print(os.environ.get("PYPOST_GIT_SSH_PASSPHRASE", ""))
"""
                script_path.write_text(script_content, encoding="utf-8")
                os.chmod(script_path, 0o700)
                logger.debug(
                    "git_auth_askpass_created mode=CUSTOM_SSH_KEY path=%s has_passphrase=True",
                    script_path,
                )
                env["SSH_ASKPASS"] = str(script_path)
                env["GIT_ASKPASS"] = str(script_path)
                env["SSH_ASKPASS_REQUIRE"] = "force"
                env["PYPOST_GIT_SSH_PASSPHRASE"] = config.passphrase

                def cleanup_ssh() -> None:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        logger.debug(
                            "git_auth_askpass_cleaned mode=CUSTOM_SSH_KEY path=%s",
                            temp_dir,
                        )

                cleanup_callbacks.append(cleanup_ssh)

            ssh_command = f"ssh {' '.join(ssh_opts)}"
            env["GIT_SSH_COMMAND"] = ssh_command
            logger.debug(
                "git_auth_mode_configured mode=CUSTOM_SSH_KEY key_path=%s "
                "strict_host_checking=%s has_passphrase=%s",
                config.key_path,
                config.strict_host_checking,
                bool(config.passphrase),
            )

        def combined_cleanup() -> None:
            for cb in cleanup_callbacks:
                try:
                    cb()
                except Exception as exc:
                    logger.warning("git_auth_cleanup_failed error=%s", exc)

        return env, (combined_cleanup if cleanup_callbacks else None)


@contextmanager
def transient_git_auth_env(
    config: Optional[GitAuthConfig] = None,
) -> Generator[dict[str, str], None, None]:
    """Context manager for obtaining an isolated Git authentication environment.

    Args:
        config: Optional GitAuthConfig.

    Yields:
        dict[str, str]: Process environment variables for subprocess execution.
    """
    mode_str = config.mode.value if config and config.mode else "NONE"
    logger.debug("transient_git_auth_env_entered mode=%s", mode_str)
    manager = GitAuthEnvironmentManager()
    env, cleanup = manager.build_env(config)
    try:
        yield env
    finally:
        if cleanup:
            cleanup()
        logger.debug("transient_git_auth_env_exited mode=%s", mode_str)

"""Staged workspace environment creation owned by EnvPresenter."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import uuid4

from pypost.core.environment_creation import EnvironmentCreationCompletion
from pypost.models.models import Environment

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pypost.ui.presenters.env_presenter import EnvPresenter


def create_workspace_environment(
    presenter: EnvPresenter, candidate: Environment, completion: EnvironmentCreationCompletion
) -> bool:
    """Admit one copy and publish it only after its own durable save succeeds."""
    with presenter._lifecycle_lock:
        reason = (
            "teardown" if presenter._admission_closed() else
            "copy_pending" if presenter._staged_environment is not None else
            "storage_busy" if presenter._storage_gateway.has_pending_work() else None
        )
        if reason is not None:
            logger.info("workspace_environment_creation_rejected reason=%s", reason)
            return False
        candidate = candidate.model_copy(deep=True)
        ids = {env.id for env in presenter._environments}
        while candidate.id in ids:
            candidate.id = str(uuid4())
        names = {env.name for env in presenter._environments}
        base = candidate.name
        suffix = 2
        while candidate.name in names:
            candidate.name = f"{base} ({suffix})"
            suffix += 1
        presenter._staged_environment = candidate
        presenter._creation_completion = completion
        presenter._creation_sequence -= 1
        logger.info(
            "workspace_environment_creation_admitted env_id=%s sequence=%d existing_count=%d",
            candidate.id, presenter._creation_sequence, len(presenter._environments),
        )
        try:
            admitted = presenter._save_environments(
                update_sequences=(
                    (presenter._creation_sequence,) if presenter._encryption_enabled() else ()
                )
            )
        except Exception:
            presenter._finish_environment_creation("failed")
            return True
        if not admitted:
            presenter._staged_environment = None
            presenter._creation_completion = None
            return False
        if not presenter._encryption_enabled():
            presenter._finish_environment_creation("persisted")
        return True


def finish_environment_creation(presenter: EnvPresenter, outcome: str) -> None:
    candidate = presenter._staged_environment
    completion = presenter._creation_completion
    if candidate is None or completion is None:
        return
    presenter._staged_environment = None
    presenter._creation_completion = None
    if outcome == "persisted":
        presenter._environments.append(candidate)
        if not presenter._admission_closed():
            presenter._env_selector.addItem(candidate.name, candidate)
        logger.info(
            "workspace_environment_creation_succeeded env_id=%s sequence=%d count=%d",
            candidate.id, presenter._creation_sequence, len(presenter._environments),
        )
        completion(candidate, None)
    else:
        # Replace a staged queued snapshot before the gateway dispatches it.
        # Preserve the request-update sequences already associated with that save.
        presenter._storage_gateway.discard_pending_environment(candidate.id)
        logger.warning(
            "workspace_environment_creation_failed env_id=%s sequence=%d reason=%s",
            candidate.id, presenter._creation_sequence, outcome,
        )
        completion(None, "Could not save the paired environment. Please retry.")

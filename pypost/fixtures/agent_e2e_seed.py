"""Builders and writer for the agent e2e seeded workspace (PYPOST-857)."""

from __future__ import annotations

import logging
from pathlib import Path

from pypost.core.storage import StorageManager
from pypost.models.models import Collection, Environment, RequestData

logger = logging.getLogger(__name__)

SEED_COLLECTION_ID = "agent-e2e-seed-collection"
SEED_COLLECTION_NAME = "Agent E2E Seed"
SEED_ENV_ID = "agent-e2e-seed-env"
SEED_ENV_NAME = "Agent E2E"
SEED_GET_REQUEST_ID = "agent-e2e-seed-get"
SEED_GET_REQUEST_NAME = "Seed GET"
SEED_POST_REQUEST_ID = "agent-e2e-seed-post"
SEED_POST_REQUEST_NAME = "Seed POST"
SEED_BASE_URL_KEY = "base_url"
SEED_BASE_URL_VALUE = "https://example.test"
SEED_GET_URL = "{{base_url}}/get"
SEED_POST_URL = "{{base_url}}/post"
SEED_POST_BODY = '{"ping": true}'


def build_agent_e2e_seed_collection() -> Collection:
    """Return the documented agent e2e seed collection (GET + POST samples)."""
    return Collection(
        id=SEED_COLLECTION_ID,
        name=SEED_COLLECTION_NAME,
        requests=[
            RequestData(
                id=SEED_GET_REQUEST_ID,
                name=SEED_GET_REQUEST_NAME,
                method="GET",
                url=SEED_GET_URL,
            ),
            RequestData(
                id=SEED_POST_REQUEST_ID,
                name=SEED_POST_REQUEST_NAME,
                method="POST",
                url=SEED_POST_URL,
                body=SEED_POST_BODY,
                body_type="json",
            ),
        ],
    )


def build_agent_e2e_seed_environments() -> list[Environment]:
    """Return the documented agent e2e seed environments (plaintext vars only)."""
    return [
        Environment(
            id=SEED_ENV_ID,
            name=SEED_ENV_NAME,
            variables={SEED_BASE_URL_KEY: SEED_BASE_URL_VALUE},
        ),
    ]


def write_agent_e2e_seed(data_dir: Path) -> None:
    """Persist the documented seed into ``data_dir`` via StorageManager.

    Call before ``AgentAppSession.start()`` so startup load surfaces the seed
    when the UI becomes ready. Caller owns ``data_dir`` lifetime when injecting
    it into the session.
    """
    collection = build_agent_e2e_seed_collection()
    environments = build_agent_e2e_seed_environments()
    try:
        storage = StorageManager(data_dir=data_dir)
        storage.save_collection(collection)
        storage.save_environments(environments)
    except Exception:
        logger.exception(
            "agent_e2e_seed_failed data_dir=%s",
            data_dir,
        )
        raise
    logger.info(
        "agent_e2e_seed_completed data_dir=%s collection_id=%s "
        "collections=%d requests=%d env_id=%s envs=%d",
        data_dir,
        collection.id,
        1,
        len(collection.requests),
        environments[0].id if environments else "",
        len(environments),
    )

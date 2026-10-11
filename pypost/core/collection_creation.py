"""Synchronous workspace creation contract and independent copy preparation."""
from collections.abc import Callable
from uuid import uuid4

from pypost.core.collection_import import CollectionImportPlanResult, plan_collection_import
from pypost.models.models import Collection

CreateWorkspaceCollection = Callable[[Collection], Collection | None]


def prepare_workspace_collection(
    source: Collection, existing: list[Collection]
) -> CollectionImportPlanResult:
    """Plan one detached copy without touching the source or canonical workspace."""
    candidate = source.model_copy(deep=True)
    taken_ids = {col.id for col in existing} | {source.id}
    candidate.id = str(uuid4())
    while candidate.id in taken_ids:
        candidate.id = str(uuid4())
    candidate.library_link = None
    names = {col.name for col in existing}
    base = f"{source.name} (copy)"
    candidate.name = base
    suffix = 2
    while candidate.name in names:
        candidate.name = f"{base} ({suffix})"
        suffix += 1
    # The existing planner reserves request and WebSocket IDs. MCP profile IDs
    # need the same reservation here without changing generic import semantics.
    profile_ids = {profile.id for col in existing for profile in col.mcp_clients}
    for profile in candidate.mcp_clients:
        while profile.id in profile_ids:
            profile.id = str(uuid4())
        profile_ids.add(profile.id)
    return plan_collection_import(existing, [candidate])

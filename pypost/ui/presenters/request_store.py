"""Where a request goes when it is saved, and what that does to stored state.

The presenter owns the dialogs: what to ask and what the answer looks like. This
owns everything that follows from the answer -- which collection receives the
request, creating one if the user named a new one, persisting it, expanding the
collection that just gained a request, and recording the action.
"""
import logging
import uuid
from typing import List, Optional, Tuple

from pypost.core.metrics import MetricsManager
from pypost.core.request_manager import RequestManager
from pypost.core.state_manager import StateManager
from pypost.models.models import Collection, RequestData

logger = logging.getLogger(__name__)


class RequestStore:
    def __init__(
        self,
        request_manager: RequestManager,
        state_manager: StateManager,
        metrics: MetricsManager | None = None,
    ) -> None:
        self._request_manager = request_manager
        self._state_manager = state_manager
        self._metrics = metrics

    def collections(self) -> List[Collection]:
        """The collections a save can target."""
        return self._request_manager.get_collections()

    def find_existing(
        self, request_id: str,
    ) -> Optional[Tuple[RequestData, Collection]]:
        """The stored request under this id, and the collection holding it."""
        return self._request_manager.find_request(request_id)

    def resolve_target(
        self,
        selected_collection_id: str | None,
        new_collection_name: str | None,
    ) -> str | None:
        """Turn the answer into a collection id, creating one if it names a new one.

        Returns None when the answer identifies no collection at all, which the
        caller should treat as a save that cannot proceed.
        """
        if selected_collection_id:
            return selected_collection_id
        if new_collection_name:
            return self._request_manager.create_collection(new_collection_name).id
        return None

    def overwrite(self, request_data: RequestData, collection_id: str) -> None:
        """Replace the stored request in the collection that already holds it."""
        self._request_manager.save_request(request_data, collection_id)
        logger.info(
            "save_request_overwrite_succeeded request_id=%s collection_id=%s",
            request_data.id, collection_id,
        )
        self._track("overwrite")

    def store(self, request_data: RequestData, collection_id: str) -> None:
        """Add the request to a collection it is not in yet."""
        self._request_manager.save_request(request_data, collection_id)
        logger.info(
            "save_request_new_succeeded request_id=%s name=%s collection_id=%s",
            request_data.id, request_data.name, collection_id,
        )
        self._track("new")
        self._expand(collection_id)

    def store_copy(
        self, request_data: RequestData, collection_id: str, name: str,
    ) -> RequestData:
        """Store an independent copy under a new id, and return it."""
        new_request = request_data.model_copy(
            deep=True,
            update={"id": str(uuid.uuid4()), "name": name},
        )
        self._request_manager.save_request(new_request, collection_id)
        logger.info(
            "save_as_flow_completed source_request_id=%s new_request_id=%s"
            " target_collection_id=%s",
            request_data.id, new_request.id, collection_id,
        )
        self._expand(collection_id)
        return new_request

    def _expand(self, collection_id: str) -> None:
        """A collection that just gained a request should be showing it."""
        expanded = self._state_manager.get_expanded_collections()
        if collection_id not in expanded:
            expanded.append(collection_id)
            self._state_manager.set_expanded_collections(expanded)

    def _track(self, source: str) -> None:
        if self._metrics:
            self._metrics.track_gui_save_action(source)

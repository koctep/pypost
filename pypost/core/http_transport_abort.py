"""HTTP transport abort and session teardown support (PYPOST-1454).

Provides active socket shutdown and session closure registration with
CancellationTokenSource for immediate cancellation of in-flight remote HTTP
transfers.
"""
from __future__ import annotations

import contextvars
import logging
import socket
from typing import Any, Callable, List, Set

import requests
from requests.adapters import HTTPAdapter

from pypost.core.cancellation import (
    CancellationToken,
    OperationCancelledError,
)

logger = logging.getLogger(__name__)

_active_connections_context: contextvars.ContextVar[Set[Any] | None] = (
    contextvars.ContextVar("_active_connections_context", default=None)
)


def _instrument_pool(pool: Any) -> None:
    """Patch pool._get_conn and pool._put_conn to track in-flight connections."""
    if getattr(pool, "_abortable_instrumented", False):
        return
    pool._abortable_instrumented = True
    orig_get_conn = pool._get_conn
    orig_put_conn = pool._put_conn

    def _instrumented_get_conn(*args: Any, **kwargs: Any) -> Any:
        conn = orig_get_conn(*args, **kwargs)
        active = _active_connections_context.get(None)
        if active is not None:
            active.add(conn)
        return conn

    def _instrumented_put_conn(conn: Any) -> Any:
        active = _active_connections_context.get(None)
        if active is not None:
            active.discard(conn)
        return orig_put_conn(conn)

    pool._get_conn = _instrumented_get_conn
    pool._put_conn = _instrumented_put_conn


class AbortableHTTPAdapter(HTTPAdapter):
    """HTTPAdapter tracking in-flight connections for prompt transport abort."""

    def get_connection(self, url: str, proxies: Any = None) -> Any:
        conn_pool = super().get_connection(url, proxies)
        _instrument_pool(conn_pool)
        return conn_pool

    def get_connection_with_tls_context(
        self,
        request: Any,
        verify: Any,
        proxies: Any = None,
        cert: Any = None,
    ) -> Any:
        conn_pool = super().get_connection_with_tls_context(
            request, verify, proxies=proxies, cert=cert
        )
        _instrument_pool(conn_pool)
        return conn_pool


def mount_abortable_adapter(session: requests.Session) -> None:
    """Mount AbortableHTTPAdapter on http:// and https:// prefixes of session."""
    adapter = AbortableHTTPAdapter()
    session.mount("http://", adapter)
    session.mount("https://", adapter)


def create_abortable_session() -> requests.Session:
    """Create a new requests.Session with AbortableHTTPAdapter mounted."""
    session = requests.Session()
    mount_abortable_adapter(session)
    return session


class TransportAbortGuard:
    """Context manager registering active transport abort with a CancellationToken."""

    def __init__(
        self,
        client: Any,
        session: requests.Session,
        cancellation_token: CancellationToken | None,
    ) -> None:
        self._client = client
        self._session = session
        self._cancellation_token = cancellation_token
        self._active_connections: Set[Any] = set()
        self._active_response: List[Any] = [None]
        self._aborted = False
        self._unregister: Callable[[], None] | None = None
        self._ctx_token: Any = None

    def set_active_response(self, response: Any) -> None:
        """Attach active response for socket and stream teardown upon abort."""
        self._active_response[0] = response

    def _abort(self) -> None:
        if self._aborted:
            return
        self._aborted = True
        logger.info(
            "http_transport_abort_triggered active_connections=%d has_response=%s",
            len(self._active_connections),
            self._active_response[0] is not None,
        )
        try:
            self._session.close()
            logger.debug("http_transport_session_closed")
        except Exception as exc:
            logger.debug("http_transport_session_close_failed reason=%s", exc)

        sockets_closed = 0
        for conn in list(self._active_connections):
            try:
                sock = getattr(conn, "sock", None)
                if sock is not None:
                    try:
                        sock.shutdown(socket.SHUT_RDWR)
                    except Exception as exc:
                        logger.debug("http_transport_socket_shutdown_failed reason=%s", exc)
                    try:
                        sock.close()
                        sockets_closed += 1
                    except Exception as exc:
                        logger.debug("http_transport_socket_close_failed reason=%s", exc)
                conn.close()
            except Exception as exc:
                logger.debug("http_transport_connection_close_failed reason=%s", exc)

        logger.debug("http_transport_sockets_aborted count=%d", sockets_closed)

        resp = self._active_response[0]
        if resp is not None:
            try:
                resp.close()
            except Exception as exc:
                logger.debug("http_transport_response_close_failed reason=%s", exc)
            raw = getattr(resp, "raw", None)
            if raw is not None:
                try:
                    raw.close()
                except Exception:
                    pass
                fp = getattr(raw, "_fp", None)
                if fp is not None and hasattr(fp, "close"):
                    try:
                        fp.close()
                    except Exception:
                        pass
            logger.debug("http_transport_response_closed")

    def __enter__(self) -> TransportAbortGuard:
        if self._cancellation_token is not None:
            if self._cancellation_token.is_cancellation_requested:
                logger.info(
                    "http_transport_pre_cancelled reason=%s",
                    self._cancellation_token.cancellation_reason or "pre-cancelled",
                )
            self._cancellation_token.throw_if_cancellation_requested()
            self._unregister = self._cancellation_token.register_callback(self._abort)
        self._ctx_token = _active_connections_context.set(self._active_connections)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self._ctx_token is not None:
            _active_connections_context.reset(self._ctx_token)
        if self._unregister is not None:
            self._unregister()
        if self._aborted:
            if (
                type(self._client.session) is requests.Session
                or self._client.session is self._session
            ):
                self._client.session = create_abortable_session()
                logger.info(
                    "http_transport_session_recreated client_id=%d",
                    id(self._client),
                )

        if exc_val is not None and self._cancellation_token is not None:
            if self._cancellation_token.is_cancellation_requested:
                logger.info(
                    "http_transport_aborted_by_cancellation reason=%s",
                    self._cancellation_token.cancellation_reason
                    or "Request transport was cancelled.",
                )
                raise OperationCancelledError(
                    self._cancellation_token.cancellation_reason
                    or "Request transport was cancelled."
                ) from exc_val

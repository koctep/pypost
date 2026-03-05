import threading
import asyncio
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from prometheus_client import make_asgi_app, CollectorRegistry, Counter, generate_latest
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Resource, TextResourceContents


class MetricsManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MetricsManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.registry = CollectorRegistry()
        self.server_instance = None
        self.thread = None
        self.server_lock = threading.Lock()

        # Define metrics
        self._init_metrics()

        # Initialize MCP Server
        self.mcp_server = Server("pypost-metrics")
        self.mcp_server.list_resources()(self.list_resources)
        self.mcp_server.read_resource()(self.read_resource)

    def _init_metrics(self):
        """Initialize all Prometheus metrics."""
        self.gui_send_clicks = Counter(
            'gui_send_clicks_total',
            'Number of times Send button was clicked',
            registry=self.registry
        )

        self.gui_save_actions = Counter(
            'gui_save_actions_total',
            'Number of times Save action was triggered in GUI',
            ['source'],
            registry=self.registry
        )
        self.gui_save_as_actions = Counter(
            'gui_save_as_actions_total',
            'Number of times Save As action was triggered in GUI',
            ['source'],
            registry=self.registry
        )
        self.gui_new_tab_actions = Counter(
            'gui_new_tab_actions_total',
            'Number of times New Tab action was triggered in GUI',
            ['source'],
            registry=self.registry
        )
        self.gui_collection_delete_actions = Counter(
            'gui_collection_delete_actions_total',
            'Number of delete actions from collection context menu',
            ['item_type', 'status'],
            registry=self.registry
        )

        self.requests_sent = Counter(
            'requests_sent_total',
            'Number of HTTP requests sent',
            ['method'],
            registry=self.registry
        )

        self.responses_received = Counter(
            'responses_received_total',
            'Number of HTTP responses received',
            ['method', 'status_code'],
            registry=self.registry
        )

        self.mcp_requests_received = Counter(
            'mcp_requests_received_total',
            'Number of requests received by MCP server',
            ['method'],
            registry=self.registry
        )

        self.mcp_responses_sent = Counter(
            'mcp_responses_sent_total',
            'Number of responses sent by MCP server',
            ['method', 'status'],
            registry=self.registry
        )

    # MCP Resource Handlers
    async def list_resources(self) -> list[Resource]:
        return [Resource(
            uri="metrics://all",
            name="All Metrics",
            description="Prometheus metrics in text format",
            mimeType="text/plain"
        )]

    async def read_resource(self, uri: str) -> list[TextResourceContents]:
        if uri == "metrics://all":
            # Track access via existing metric
            self.track_mcp_request_received("read_resource:metrics")
            try:
                data = generate_latest(self.registry).decode('utf-8')
                self.track_mcp_response_sent("read_resource:metrics", "success")
                return [TextResourceContents(
                    uri=uri,
                    mimeType="text/plain",
                    text=data
                )]
            except Exception:
                self.track_mcp_response_sent("read_resource:metrics", "error")
                raise

        raise ValueError(f"Resource {uri} not found")

    def _create_app(self) -> Starlette:
        # 1. Prometheus app
        prometheus_app = make_asgi_app(registry=self.registry)

        # 2. MCP Transport setup (SSE)
        sse = SseServerTransport("/messages")

        class SSEEndpoint:
            def __init__(self, server, sse_transport):
                self.server = server
                self.sse_transport = sse_transport

            async def __call__(self, scope, receive, send):
                async with self.sse_transport.connect_sse(scope, receive, send) as streams:
                    init_opts = self.server.create_initialization_options()
                    await self.server.run(streams[0], streams[1], init_opts)

        class MessagesEndpoint:
            def __init__(self, sse_transport):
                self.sse_transport = sse_transport

            async def __call__(self, scope, receive, send):
                # Ensure we only handle POST requests if it's HTTP
                if scope["type"] == "http" and scope["method"] != "POST":
                    # Manually send 405 Method Not Allowed
                    await self._send_response(send, 405, b"Method Not Allowed")
                    return
                await self.sse_transport.handle_post_message(scope, receive, send)

            async def _send_response(self, send, status, body):
                await send({
                    "type": "http.response.start",
                    "status": status,
                    "headers": [(b"content-type", b"text/plain")],
                })
                await send({
                    "type": "http.response.body",
                    "body": body,
                })

        # 3. Combine in Starlette
        return Starlette(routes=[
            Mount("/metrics", app=prometheus_app),
            Mount("/sse", app=SSEEndpoint(self.mcp_server, sse)),
            Mount("/messages", app=MessagesEndpoint(sse))
        ])

    def start_server(self, host: str, port: int):
        """Start the metrics server (Prometheus + MCP)."""
        with self.server_lock:
            if self.thread and self.thread.is_alive():
                self.stop_server()

            self._current_host = host
            self._current_port = port

            self.thread = threading.Thread(target=self._run_uvicorn, daemon=True)
            self.thread.start()
            print(f"Metrics server started on {host}:{port}")

    def _run_uvicorn(self):
        app = self._create_app()
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        config = uvicorn.Config(
            app=app,
            host=self._current_host,
            port=self._current_port,
            loop="asyncio",
            log_level="warning",
        )
        self.server_instance = uvicorn.Server(config)

        # Override signal handlers to avoid main thread conflict
        self.server_instance.install_signal_handlers = lambda: None

        loop.run_until_complete(self.server_instance.serve())

    def stop_server(self):
        """Stop the metrics server."""
        with self.server_lock:
            if self.server_instance:
                self.server_instance.should_exit = True

            if self.thread:
                self.thread.join(timeout=2.0)
                self.thread = None
                self.server_instance = None
                print("Metrics server stopped")

    def restart_server(self, host: str, port: int):
        """Restart the metrics server with new settings."""
        self.stop_server()
        self.start_server(host, port)

    # Tracking methods
    def track_gui_send_click(self):
        self.gui_send_clicks.inc()

    def track_gui_save_action(self, source: str):
        self.gui_save_actions.labels(source=source).inc()

    def track_gui_save_as_action(self, source: str):
        self.gui_save_as_actions.labels(source=source).inc()

    def track_gui_new_tab_action(self, source: str):
        self.gui_new_tab_actions.labels(source=source).inc()

    def track_gui_collection_delete_action(self, item_type: str, status: str):
        self.gui_collection_delete_actions.labels(item_type=item_type, status=status).inc()

    def track_request_sent(self, method: str):
        self.requests_sent.labels(method=method).inc()

    def track_response_received(self, method: str, status_code: str):
        self.responses_received.labels(method=method, status_code=status_code).inc()

    def track_mcp_request_received(self, method: str):
        self.mcp_requests_received.labels(method=method).inc()

    def track_mcp_response_sent(self, method: str, status: str):
        self.mcp_responses_sent.labels(method=method, status=status).inc()

import hashlib
import logging
from collections import Counter
from typing import Any, Dict, List, Set

import jinja2
from jinja2 import nodes
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response
from starlette.routing import Mount, Route

from pypost.core.metrics import MetricsManager
from pypost.core.request_service import RequestService
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData


logger = logging.getLogger(__name__)


class MCPServerImpl:
    def __init__(self, name: str = "pypost-server", metrics: MetricsManager | None = None,
                 template_service: TemplateService | None = None,
                 request_timeout: float = 30.0):
        self.server = Server(name)
        self.tools_map: Dict[str, RequestData] = {}
        self._metrics = metrics
        self._template_service = template_service
        if template_service is not None:
            logger.debug(
                "MCPServerImpl: using injected TemplateService id=%d",
                id(template_service),
            )
        self.request_service = RequestService(metrics=self._metrics,
                                              template_service=self._template_service,
                                              request_timeout=request_timeout)

        # Register handlers
        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)

    def set_request_timeout(self, request_timeout: float) -> None:
        self.request_service.set_request_timeout(request_timeout)

    async def list_tools(self) -> List[Tool]:
        tools = []
        for name, req in self.tools_map.items():
            schema = self._generate_schema(req)
            tools.append(Tool(
                name=name,
                description=req.name or "No description",
                inputSchema=schema
            ))
        return tools

    async def call_tool(self, name: str, arguments: dict) -> List[Any]:
        if name not in self.tools_map:
            raise ValueError(f"Tool {name} not found")

        request_data = self.tools_map[name]

        # Track MCP request
        if self._metrics:
            self._metrics.track_mcp_request_received(request_data.method)

        # Execute request in threadpool since RequestService is synchronous
        try:
            result = await run_in_threadpool(
                self._execute_request_sync, request_data, arguments
            )

            # Format output
            output_text = result.response.body

            # Append script logs if any (helpful for debugging)
            if result.script_logs:
                logs_str = "\n".join(result.script_logs)
                output_text += "\n\n--- Script Logs ---\n" + logs_str

            if result.script_error:
                err = result.script_error
                output_text += "\n\n--- Script Error ---\n" + err

            # Track MCP response success
            if self._metrics:
                self._metrics.track_mcp_response_sent(
                    request_data.method, "success"
                )

            return [TextContent(type="text", text=output_text)]
        except Exception as e:
            # Track MCP response error
            if self._metrics:
                self._metrics.track_mcp_response_sent(
                    request_data.method, "error"
                )
            return [TextContent(
                type="text", text=f"Error executing request: {str(e)}"
            )]

    def _execute_request_sync(self, request_data: RequestData, args: dict):
        # Prepare context
        context = {"mcp": {"request": args}}

        return self.request_service.execute(request_data, context)

    def register_tools(self, requests: List[RequestData]):
        """Replace the exposed tool list.

        The new map is built to one side and swapped in, so a list_tools call
        running on the server thread iterates one map or the other and never a
        half-built one.
        """
        mapping: Dict[str, RequestData] = {}
        exposed = [req for req in requests if req.expose_as_mcp]
        normalized = [self._normalize_name(req.name) for req in exposed]
        name_counts = Counter(normalized)

        for req, base_name in zip(exposed, normalized):
            tool_name = base_name
            if name_counts[base_name] > 1:
                suffix = hashlib.sha256(req.id.encode("utf-8")).hexdigest()[:8]
                tool_name = f"{base_name}_{suffix}"

            candidate = tool_name
            discriminator = 2
            while candidate in mapping:
                candidate = f"{tool_name}_{discriminator}"
                discriminator += 1
            mapping[candidate] = req

        self.tools_map = mapping

    def _normalize_name(self, name: str) -> str:
        # Lowercase, spaces->underscores, remove non-alnum
        normalized = "".join(c if c.isalnum() else "_" for c in name.lower())
        return normalized or "request"

    def _generate_schema(self, req: RequestData) -> dict:
        # Parse {{ mcp.request.x }} variables
        variables = self._extract_mcp_variables(req)

        properties = {}
        required = []

        for var in variables:
            properties[var] = {"type": "string"}
            required.append(var)

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    def _extract_mcp_variables(self, req: RequestData) -> Set[str]:
        vars_found = set()

        # Combine all potentially templated fields
        content_to_scan = [
            req.url,
            req.body,
        ]
        content_to_scan.extend(req.headers.values())
        content_to_scan.extend(req.params.values())

        for content in content_to_scan:
            if not content:
                continue
            try:
                if self._template_service is not None:
                    ast = self._template_service.parse(content)
                else:
                    ast = jinja2.Environment().parse(content)
                for node in ast.find_all((nodes.Getattr, nodes.Getitem)):
                    parent = node.node
                    is_mcp_request = (
                        isinstance(parent, nodes.Getattr)
                        and parent.attr == "request"
                        and isinstance(parent.node, nodes.Name)
                        and parent.node.name == "mcp"
                    )
                    if not is_mcp_request:
                        continue
                    if isinstance(node, nodes.Getattr):
                        vars_found.add(node.attr)
                    elif (
                        isinstance(node.arg, nodes.Const)
                        and isinstance(node.arg.value, str)
                    ):
                        vars_found.add(node.arg.value)
            except Exception:
                logger.warning("mcp_schema_template_parse_failed", exc_info=True)

        return vars_found

    def create_app(self) -> Starlette:
        sse = SseServerTransport("/messages")

        class SSEEndpoint:
            def __init__(self, server, sse_transport):
                self.server = server
                self.sse_transport = sse_transport

            async def __call__(self, scope, receive, send):
                if scope.get("method") != "GET":
                    await send({
                        "type": "http.response.start",
                        "status": 405,
                        "headers": [(b"content-type", b"text/plain")],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": b"Method Not Allowed",
                    })
                    return
                async with self.sse_transport.connect_sse(
                    scope, receive, send
                ) as streams:
                    opts = self.server.create_initialization_options()
                    await self.server.run(streams[0], streams[1], opts)

        class MessagesEndpoint:
            def __init__(self, sse_transport):
                self.sse_transport = sse_transport

            async def __call__(self, scope, receive, send):
                # Ensure we only handle POST requests if it's HTTP
                if scope["type"] == "http" and scope["method"] != "POST":
                    await self._send_response(
                        send, 405, b"Method Not Allowed"
                    )
                    return
                await self.sse_transport.handle_post_message(
                    scope, receive, send
                )

            async def _send_response(self, send, status, body):
                await send({
                    "type": "http.response.start",
                    "status": status,
                    "headers": [
                        (b"content-type", b"text/plain"),
                    ],
                })
                await send({
                    "type": "http.response.body",
                    "body": body,
                })

        # MCP client POSTs to /sse/messages (root_path + endpoint).
        # Both under Mount("/sse") so scope["root_path"]="/sse".
        async def handle_sse_get(request):
            ep = SSEEndpoint(self.server, sse)
            await ep(request.scope, request.receive, request._send)
            return Response()

        sse_app = Starlette(
            debug=True,
            routes=[
                Mount("/messages", app=MessagesEndpoint(sse)),
                Route("/", endpoint=handle_sse_get, methods=["GET"]),
            ],
        )
        return Starlette(
            debug=True,
            routes=[Mount("/sse", app=sse_app)],
        )

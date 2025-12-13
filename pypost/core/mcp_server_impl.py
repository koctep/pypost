from typing import List, Dict, Any, Set
from starlette.applications import Starlette
from starlette.routing import Route
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from pypost.models.models import RequestData
import jinja2
from jinja2 import Environment
import json
from starlette.concurrency import run_in_threadpool
from pypost.core.request_service import RequestService

class MCPServerImpl:
    def __init__(self, name: str = "pypost-server"):
        self.server = Server(name)
        self.tools_map: Dict[str, RequestData] = {}
        self.env = Environment() # Jinja2 environment for parsing
        self.request_service = RequestService()
        
        # Register handlers
        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)

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
                output_text += f"\n\n--- Script Logs ---\n{logs_str}"
            
            if result.script_error:
                output_text += f"\n\n--- Script Error ---\n{result.script_error}"

            return [TextContent(type="text", text=output_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error executing request: {str(e)}")]

    def _execute_request_sync(self, request_data: RequestData, args: dict):
        # Prepare context
        context = {"mcp": {"request": args}}
        
        return self.request_service.execute(request_data, context)

    def register_tools(self, requests: List[RequestData]):
        self.tools_map.clear()
        for req in requests:
            if req.expose_as_mcp:
                tool_name = self._normalize_name(req.name)
                self.tools_map[tool_name] = req

    def _normalize_name(self, name: str) -> str:
        # Simple normalization: lowercase, replace spaces with underscores, remove non-alnum
        return "".join(c if c.isalnum() else "_" for c in name.lower())

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
                ast = self.env.parse(content)
                meta_vars = jinja2.meta.find_undeclared_variables(ast)
                for var in meta_vars:
                    # check for mcp.request.x pattern
                    # Jinja2 parses "mcp.request.x" as variable "mcp" with attributes
                    # But find_undeclared_variables returns just "mcp".
                    # We need to manually scan for the full path or trust that "mcp" implies it.
                    # Wait, find_undeclared_variables returns top-level names.
                    # If the template is {{ mcp.request.foo }}, it returns 'mcp'.
                    # This is not specific enough to know 'foo'.
                    
                    # Alternative: Regex scan might be more robust for this specific pattern
                    # since we specifically look for {{ mcp.request.VAR }}
                    pass
            except:
                pass

        # Regex fallback for deep variable extraction
        import re
        # Pattern: {{ mcp.request.VAR_NAME }} or {{ mcp.request['VAR_NAME'] }}
        # Simple dot notation support
        pattern = re.compile(r"\{\{\s*mcp\.request\.([a-zA-Z0-9_]+)\s*\}\}")
        
        for content in content_to_scan:
            if not content:
                continue
            matches = pattern.findall(content)
            vars_found.update(matches)
            
        return vars_found

    def create_app(self) -> Starlette:
        sse = SseServerTransport("/messages")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await self.server.run(streams[0], streams[1], sse.create_initialization_options())

        async def handle_messages(request):
            await sse.handle_post_message(request.scope, request.receive, request._send)

        return Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ],
        )

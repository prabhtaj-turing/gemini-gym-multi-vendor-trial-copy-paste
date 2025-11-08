

import os
import json
import importlib
import uvicorn
import logging
import inspect
import psutil
import signal
from pathlib import Path
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response

try:
    import mcp.types as types
    from mcp.server.lowlevel import Server
    from mcp.server.sse import SseServerTransport
except ImportError:
    raise ImportError("MCP libraries not found. Please install with 'pip install \"mcp[cli]\" uvicorn starlette psutil'")

# Use a dedicated logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def _get_service_port_mapping():
    """Scans the APIs directory to create a port mapping for each service."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    apis_dir = os.path.join(project_root, 'APIs')
    port_mapping = {}
    port = 10001
    if os.path.isdir(apis_dir):
        for service_name in sorted(os.listdir(apis_dir)):
            if os.path.isdir(os.path.join(apis_dir, service_name)) and not service_name.startswith("__"):
                port_mapping[service_name] = port
                port += 1
    return port_mapping

SERVICE_PORT_MAPPING = _get_service_port_mapping()

def _kill_process_on_port(port: int):
    """Finds and terminates any process running on the specified port."""
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    logger.info(f"Found process {proc.info['name']} (PID {proc.info['pid']}) using port {port}. Terminating it.")
                    os.kill(proc.info['pid'], signal.SIGTERM)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

class MCPServerManager:
    """
    A helper class to initialize and run a production-ready MCP server for a given service.
    It dynamically loads the service's function map and tool definitions.
    """

    def __init__(self, service_name: str, host: str = "127.0.0.1", update_mcp_config: bool = False):
        """
        Initializes the MCPServerManager.

        Args:
            service_name: The name of the service (e.g., 'clock').
            host: The host to run the server on.
            update_mcp_config: If True, automatically updates .cursor/mcp.json. 
                               If False, prints the required config to the console.
        """
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self._validate_service(service_name)
        
        self.service_name = service_name
        self.host = host
        self.port = SERVICE_PORT_MAPPING.get(service_name)
        if not self.port:
            raise ValueError(f"Port for service '{service_name}' not found in mapping.")
        self.update_mcp_config = update_mcp_config
        
        self.function_map = self._load_function_map()
        self.tool_definitions = self._load_tool_definitions()

        self.app = Server(
            name=f"{self.service_name.capitalize()}MCPServer",
            version="1.0.0"
        )
        self._setup_mcp_handlers()

    def _validate_service(self, service_name: str):
        """Validates that the service exists and is a valid package."""
        service_path = os.path.join(self.project_root, 'APIs', service_name)
        if not os.path.isdir(service_path):
            raise ValueError(f"Service '{service_name}' not found at '{service_path}'")
        
        init_file = os.path.join(service_path, '__init__.py')
        if not os.path.exists(init_file):
            raise ValueError(f"Service '{service_name}' is not a valid package (missing __init__.py)")

    def _load_function_map(self) -> dict:
        """Loads the _function_map from the service's __init__.py file."""
        try:
            service_module = importlib.import_module(f"{self.service_name}")
            function_map = getattr(service_module, "_function_map", None)
            if function_map is None:
                raise AttributeError(f"_function_map not found in service '{self.service_name}'")
            return function_map
        except ImportError as e:
            raise ImportError(f"Could not import service module '{self.service_name}': {e}")

    def _load_tool_definitions(self) -> list:
        """Loads tool definitions from the service's schema JSON file."""
        schema_path = os.path.join(self.project_root, "Schemas", f"{self.service_name}.json")
        if not os.path.exists(schema_path):
            raise FileNotFoundError(
                f"Schema file not found for service '{self.service_name}' at '{schema_path}'.\n"
                f"To generate the schema, run: python Scripts/FCSpec.py {self.service_name}"
            )
        
        with open(schema_path, 'r') as f:
            schema_data = json.load(f)
        
        if not isinstance(schema_data, list):
            raise ValueError("Schema file is not a list of tool definitions.")

        tool_defs = []
        for tool in schema_data:
            if 'parameters' in tool:
                tool['inputSchema'] = tool.pop('parameters')
            tool_defs.append(tool)
        return tool_defs

    def _import_function_from_string(self, fqn: str) -> callable:
        """Imports a function from a fully qualified name string."""
        try:
            full_fqn = f"{fqn}"
            module_path, func_name = full_fqn.rsplit('.', 1)
            module = importlib.import_module(module_path)
            return getattr(module, func_name)
        except (ImportError, AttributeError, ValueError):
            try:
                module_path = f"{self.service_name}"
                module = importlib.import_module(module_path)
                return getattr(module, fqn.split('.')[-1])
            except (ImportError, AttributeError) as e:
                 raise ImportError(f"Could not import function '{fqn}': {e}")

    def _setup_mcp_handlers(self):
        """Sets up the list_tools and call_tool handlers for the MCP server."""
        @self.app.list_tools()
        async def list_tools() -> list[types.Tool]:
            return [types.Tool.model_validate(td) for td in self.tool_definitions]

        @self.app.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
            if name not in self.function_map:
                raise ValueError(f"Unknown tool: '{name}'")
            
            handler_fqn = self.function_map[name]
            handler = self._import_function_from_string(handler_fqn)
            
            logger.info(f"Calling tool '{name}' with arguments: {arguments}")
            
            try:
                if inspect.iscoroutinefunction(handler):
                    result_dict = await handler(**arguments)
                else:
                    result_dict = handler(**arguments)
                
                result_text = json.dumps(result_dict, indent=2)
                return [types.TextContent(type="text", text=result_text)]
            except Exception as e:
                logger.error(f"Error calling tool '{name}': {e}", exc_info=True)
                error_content = {
                    "error": type(e).__name__,
                    "message": str(e)
                }
                return [types.TextContent(type="text", text=json.dumps(error_content, indent=2))]

    def _get_mcp_config_path(self) -> Path:
        """Determines the OS-specific path for .cursor/mcp.json."""
        home = Path.home()
        return home / ".cursor" / "mcp.json"

    def _handle_mcp_config(self):
        """
        Handles the MCP configuration based on the update_mcp_config flag.

        The service config is added/updated in the 'mcpServers' field of mcp.json as:
        "service_name": {
            "url": "http://host:port/sse"
        }
        """
        config_path = self._get_mcp_config_path()
        service_config_key = self.service_name
        mcp_server_config = {
            "url": f"http://{self.host}:{self.port}/sse"
        }

        if self.update_mcp_config:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {}
            if config_path.exists():
                with open(config_path, 'r') as f:
                    try:
                        config = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not decode existing MCP config at {config_path}. A new one will be created.")
                        config = {}

            # Ensure mcpServers exists and is a dict
            if "mcpServers" not in config or not isinstance(config.get("mcpServers"), dict):
                config["mcpServers"] = {}

            config["mcpServers"][service_config_key] = mcp_server_config

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"MCP configuration updated for service '{self.service_name}' in '{config_path}'.")
            logger.info(f"Added/Updated configuration in mcpServers:\n{json.dumps({service_config_key: mcp_server_config}, indent=2)}")
        else:
            # Just print the info
            print("-" * 80)
            print("MCP Server Configuration Information:")
            print(f"To use this service with Cursor, please ensure the following configuration is present in your mcp.json file.")
            print(f"File path: {config_path}")
            print("\nAdd or update the following in the 'mcpServers' field:")
            print(json.dumps({service_config_key: mcp_server_config}, indent=2))
            print("\nIf you make changes to this file, you may need to restart Cursor for them to take effect.")
            print("-" * 80)

    def run(self, run_in_background: bool = False):
        """
        Starts the MCP server and handles MCP config.

        Args:
            run_in_background (bool): If True, runs the server in a background thread (non-blocking).
                                      If False (default), runs in the foreground (blocking).
        """
        import threading

        # Kill any process already using the port
        _kill_process_on_port(self.port)

        self._handle_mcp_config()
        
        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await self.app.run(
                    streams[0],
                    streams[1],
                    self.app.create_initialization_options()
                )
            return Response()

        # Expose starlette_app as an attribute for uvicorn command-line usage
        global starlette_app
        starlette_app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )
        logger.info(f"Starting MCP server for '{self.service_name}' on http://{self.host}:{self.port}")

        def _run_uvicorn():
            uvicorn.run(starlette_app, host=self.host, port=self.port)

        if run_in_background:
            thread = threading.Thread(target=_run_uvicorn, daemon=True)
            thread.start()
            logger.info("MCP server started in background thread.")
            return thread
        else:
            _run_uvicorn()

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .tools import tool_registry

app = Server("lightdash")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    tool_definitions = []
    for _tool_name, tool_module in tool_registry.items():
        tool_def = tool_module.TOOL_DEFINITION
        tool_definitions.append(
            Tool(
                name=tool_def.name,
                description=tool_def.description,
                inputSchema=tool_def.input_schema.dict(by_alias=True)
            )
        )
    return tool_definitions

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name not in tool_registry:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
        tool_module = tool_registry[name]
        result = tool_module.run(**arguments)
        
        if isinstance(result, (dict, list)):
            result_text = json.dumps(result, indent=2)
        else:
            result_text = str(result)
            
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def run():
    """Entry point for CLI."""
    asyncio.run(main())


if __name__ == "__main__":
    run()

from typing import Any

from .. import lightdash_client
from .base_tool import ToolDefinition

TOOL_DEFINITION = ToolDefinition(
    name="list-projects",
    description="""List all projects in your Lightdash organization.
            
Returns project information including:
- Project UUID (required for other API calls)
- Project name and type
- Database connection details (warehouse type)
- Creation and update timestamps

**When to use:** Start here to discover available projects or to find the UUID of a project you want to work with. If LIGHTDASH_PROJECT_UUID environment variable is set, most other tools will use that project automatically.""",
    inputSchema={
        "properties": {}
    }
)

def run() -> list[dict[str, Any]]:
    """Run the list projects tool"""
    response = lightdash_client.get("/api/v1/org/projects")
    projects = response.get("results", [])
    
    result = []
    for project in projects:
        result.append({
            "projectUuid": project.get("projectUuid"),
            "name": project.get("name"),
            "type": project.get("type"),
            "warehouseConnection": {
                "type": project.get("warehouseConnection", {}).get("type", "")
            },
            "createdAt": project.get("createdAt", ""),
            "updatedAt": project.get("updatedAt", "")
        })
            
    return result

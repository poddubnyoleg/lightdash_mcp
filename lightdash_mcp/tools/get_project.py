import os
from typing import Any, Optional

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter

TOOL_DEFINITION = ToolDefinition(
    name="get-project",
    description="""Get detailed information about a specific project.

Returns comprehensive project details including:
- Project configuration and settings
- Warehouse connection information
- dbt integration details
- Project metadata

**When to use:** When you need detailed configuration information about a specific project, such as its warehouse connection, dbt settings, or other metadata.

**Parameters:**
- project_uuid: Optional. If not provided, uses the current/default project.""",
    inputSchema={
        "properties": {
            "project_uuid": ToolParameter(
                type="string",
                description="Optional: UUID of the project. If not provided, uses current project from LIGHTDASH_PROJECT_UUID env var or first available project."
            )
        }
    }
)

def get_project_uuid() -> str:
    """Get project UUID from env var or default to the first project"""
    project_uuid = os.getenv("LIGHTDASH_PROJECT_UUID")
    if project_uuid:
        return project_uuid

    response = lightdash_client.get("/api/v1/org/projects")
    projects = response.get("results", [])
    if not projects:
        raise ValueError("No projects found in this Lightdash instance.")
    
    return projects[0]["projectUuid"]

def run(project_uuid: Optional[str] = None) -> dict[str, Any]:
    """Run the get project tool"""
    if not project_uuid:
        project_uuid = get_project_uuid()
    
    response = lightdash_client.get(f"/api/v1/projects/{project_uuid}")
    return response.get("results", {})

from typing import Any, Optional

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="list-dashboards",
    description="""List all dashboards in the Lightdash project.

Returns dashboard metadata including:
- Dashboard UUID and name
- Description
- Space (folder) the dashboard belongs to
- View and update timestamps

**When to use:** 
- To discover available dashboards
- To find a dashboard UUID for other operations
- To get an overview of dashboard organization

**Next steps:** Use get-dashboard-tiles to see what's on a dashboard, or get-dashboard-code to get the complete configuration.""",
    inputSchema={
        "properties": {
             "project_uuid": ToolParameter(
                type="string",
                description="Optional: UUID of the project. If not provided, uses current project."
            )
        }
    }
)

def run(project_uuid: Optional[str] = None) -> list[dict[str, Any]]:
    """Run the list dashboards tool"""
    if not project_uuid:
        project_uuid = get_project_uuid()
    
    response = lightdash_client.get(f"/api/v1/projects/{project_uuid}/dashboards")
    dashboards = response.get("results", [])

    result = []
    for dash in dashboards:
        result.append({
            "uuid": dash.get("uuid"),
            "name": dash.get("name"),
            "description": dash.get("description", "")
        })
    
    return result

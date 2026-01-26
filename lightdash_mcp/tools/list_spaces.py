from typing import Any

from .. import lightdash_client
from .base_tool import ToolDefinition
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="list-spaces",
    description="""List all spaces (folders) in the Lightdash project.

Spaces are organizational folders that contain charts and dashboards.

**Returns for each space:**
- UUID and name
- Whether it's private (restricted access)
- Count of charts in the space
- Count of dashboards in the space

**When to use:** 
- To discover organizational structure of content
- To find space UUIDs for creating charts
- To get an overview of content organization
- Before creating new spaces to avoid duplicates

**Space types:**
- Public spaces: Visible to all project users
- Private spaces: Restricted to specific users/groups""",
    inputSchema={
        "properties": {}
    }
)

def run() -> list[dict[str, Any]]:
    """Run the list spaces tool"""
    project_uuid = get_project_uuid()
    response = lightdash_client.get(f"/api/v1/projects/{project_uuid}/spaces")
    spaces = response.get("results", [])
    
    result = []
    for space in spaces:
        result.append({
            "uuid": space.get("uuid"),
            "name": space.get("name"),
            "isPrivate": space.get("isPrivate", False),
            "chartCount": len(space.get("queries", [])),
            "dashboardCount": len(space.get("dashboards", []))
        })
        
    return result

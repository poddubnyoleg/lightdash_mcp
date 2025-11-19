from typing import Any, Optional

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="list-explores",
    description="""List all available explores (tables) in the project.

Returns a simplified list of explores with their names, labels, and descriptions.
Use this to discover available data models before using `get-explore-schema` to get detailed field information.

**When to use:**
- To find out what tables/explores are available to query
- As a lightweight alternative to `get-catalog`
- When you don't know the exact name of the table you want to query
""",
    inputSchema={
        "properties": {
            "project_uuid": ToolParameter(
                type="string",
                description="Optional: UUID of the project. If not provided, uses current project."
            )
        }
    }
)

def run(project_uuid: Optional[str] = None) -> dict[str, Any]:
    """Run the list explores tool"""
    if not project_uuid:
        project_uuid = get_project_uuid()
    
    # We use the catalog endpoint but filter the results to be lightweight
    response = lightdash_client.get(f"/api/v1/projects/{project_uuid}/catalog")
    catalog = response.get("results", {})
    
    explores = []
    
    # Handle if catalog is a dict (explore_name -> explore_data) or list
    if isinstance(catalog, dict):
        for name, data in catalog.items():
            explores.append({
                "name": name,
                "label": data.get("label", name),
                "description": data.get("description", ""),
                "type": data.get("type", "explore")
            })
    elif isinstance(catalog, list):
        for item in catalog:
            explores.append({
                "name": item.get("name", ""),
                "label": item.get("label", ""),
                "description": item.get("description", ""),
                "type": item.get("type", "explore")
            })
            
    return {
        "explores": explores,
        "count": len(explores)
    }

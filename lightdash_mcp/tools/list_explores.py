from typing import Any, Optional

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="list-explores",
    description="""List all available explores/tables in the project catalog.

Returns a catalog of all tables/explores organized by project and dataset:
- Explore/table names
- Table descriptions  
- SQL table references

**When to use:** 
- To discover what tables/explores are available in the project
- To browse the data catalog and find relevant tables by description
- Before using get-explore-schema to get detailed field information

**Best practice:** Use this for initial discovery to find table names, then use get-explore-schema for detailed dimensions, metrics, and joins.

**Note:** This can return large amounts of data for projects with many explores.""",
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
    
    response = lightdash_client.get(f"/api/v1/projects/{project_uuid}/catalog")
    return response.get("results", {})

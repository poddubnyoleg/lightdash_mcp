from typing import Any, Optional

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="get-catalog",
    description="""Get the complete data catalog for a project.

The data catalog provides a comprehensive view of all available data including:
- All explores (data models) with their tables
- All dimensions and metrics available in each table
- Field types, descriptions, and metadata
- Table relationships and joins

**When to use:** 
- To discover what data is available in the project
- To understand the structure of your data models
- Before building queries or charts to find the right fields
- As an alternative to get-explore-schema when you want to see everything at once

**Best practice:** Use this for initial discovery, then use get-explore-schema for detailed information about specific tables.

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
    """Run the get catalog tool"""
    if not project_uuid:
        project_uuid = get_project_uuid()
    
    response = lightdash_client.get(f"/api/v1/projects/{project_uuid}/catalog")
    return response.get("results", {})

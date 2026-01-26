from typing import Any, Optional

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="list-charts",
    description="""List all saved charts in the Lightdash project.

Returns chart information including:
- Chart UUID and name
- Space (folder) the chart belongs to
- Description
- Last updated timestamp

**When to use:** 
- To discover available charts in the project
- To find a chart UUID for adding to dashboards or querying
- To get an overview of what visualizations exist
- To filter charts by name before getting details

**Optional search_term:** Filters the list to only charts matching the search term in their name.""",
    inputSchema={
        "properties": {
            "search_term": ToolParameter(
                type="string",
                description="Optional: Filter charts by name (case-insensitive partial match). Example: 'revenue' will match 'Monthly Revenue Chart'"
            )
        }
    }
)

def run(search_term: Optional[str] = None) -> list[dict[str, Any]]:
    """Run the list charts tool"""
    project_uuid = get_project_uuid()
    response = lightdash_client.get(f"/api/v1/projects/{project_uuid}/charts")
    charts = response.get("results", [])
    
    if search_term:
        charts = [c for c in charts if search_term.lower() in c.get("name", "").lower()]
            
    result = []
    for chart in charts:
        result.append({
            "uuid": chart.get("uuid"),
            "name": chart.get("name"),
            "space": chart.get("spaceName", ""),
            "description": chart.get("description", ""),
            "updatedAt": chart.get("updatedAt", "")
        })
            
    return result

import json

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_dashboard_tiles import get_dashboard
from .get_project import get_project_uuid
from .list_dashboards import run as list_dashboards

TOOL_DEFINITION = ToolDefinition(
    name="update-dashboard-filters",
    description="""Update dashboard-level filters that apply to all tiles.

Dashboard filters allow users to:
- Filter all charts on a dashboard at once
- Create interactive dashboards where users can change filters
- Implement global date ranges or category filters

**Filter configuration structure:**
Filters use the same structure as chart filters with:
- Field references (fieldId)
- Operators (equals, notEquals, contains, greaterThan, etc.)
- Values or value ranges
- Time-based filters (inThePast, inTheNext, etc.)

**When to use:** 
- To add global date range selectors
- To create region/category filters that apply to all charts
- To update filter options or defaults
- To remove filters that are no longer needed

**Important:** Changes apply immediately to all dashboard viewers.

**Testing:** Use run-dashboard-chart after updating to verify filters work as expected.""",
    inputSchema={
        "properties": {
            "dashboard_name": ToolParameter(
                type="string",
                description="Name of the dashboard (supports partial matching)"
            ),
            "filters": ToolParameter(
                type="string",
                description="JSON string of filter configuration. Use same structure as chart filters. Example: {\"dimensions\": {\"id\": \"root\", \"and\": [{\"id\": \"filter1\", \"target\": {\"fieldId\": \"table_field\"}, \"operator\": \"equals\", \"values\": [\"value\"]}]}}"
            )
        },
        "required": ["dashboard_name", "filters"]
    }
)

def run(dashboard_name: str, filters: str) -> str:
    """Run the update dashboard filters tool"""
    try:
        filters_data = json.loads(filters)
    except json.JSONDecodeError as e:
        return f"Error parsing filters JSON: {str(e)}"

    project_uuid = get_project_uuid()
    dashboards = list_dashboards(project_uuid)
    
    dashboard_uuid = None
    for dash in dashboards:
        if dash.get("name", "").lower() == dashboard_name.lower():
            dashboard_uuid = dash.get("uuid")
            break
            
    if not dashboard_uuid:
        raise ValueError(f"Dashboard '{dashboard_name}' not found")
        
    dashboard = get_dashboard(dashboard_uuid)
    
    update_payload = {
        "name": dashboard.get("name"),
        "tiles": dashboard.get("tiles", []),
        "filters": filters_data,
        "tabs": dashboard.get("tabs", [])
    }
    
    lightdash_client.patch(f"/api/v1/dashboards/{dashboard_uuid}", data=update_payload)
    
    return f"Successfully updated filters on dashboard '{dashboard_name}'"

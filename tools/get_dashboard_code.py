from typing import Any

from .base_tool import ToolDefinition, ToolParameter
from .get_dashboard_tiles import get_dashboard
from .get_project import get_project_uuid
from .list_dashboards import run as list_dashboards

TOOL_DEFINITION = ToolDefinition(
    name="get-dashboard-code",
    description="""Get the complete dashboard configuration including full tile definitions.

Returns the raw dashboard configuration as code, including:
- All tile definitions with complete properties
- Tab configuration
- Filter configuration
- Layout information
- Chart references

**When to use:** 
- To export a dashboard for version control
- To understand the complete structure of a complex dashboard
- Before programmatically duplicating a dashboard
- To backup dashboard configurations
- To debug dashboard issues

**Use cases:**
- **Backup:** Save dashboard configs before making changes
- **Version control:** Track dashboard changes over time
- **Migration:** Move dashboards between projects/environments
- **Templates:** Create reusable dashboard templates

**Alternative:** Use duplicate-dashboard for a simpler way to copy dashboards.""",
    inputSchema={
        "properties": {
            "dashboard_name": ToolParameter(
                type="string",
                description="Name of the dashboard (supports partial matching)"
            )
        },
        "required": ["dashboard_name"]
    }
)

def run(dashboard_name: str) -> dict[str, Any]:
    """Run the get dashboard code tool"""
    project_uuid = get_project_uuid()
    dashboards = list_dashboards(project_uuid)
    
    dashboard_uuid = None
    for dash in dashboards:
        if dash.get("name", "").lower() == dashboard_name.lower():
            dashboard_uuid = dash.get("uuid")
            break
            
    if not dashboard_uuid:
        raise ValueError(f"Dashboard '{dashboard_name}' not found")
        
    return get_dashboard(dashboard_uuid)

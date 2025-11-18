from typing import Any

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_dashboard_tiles import get_dashboard
from .get_project import get_project_uuid
from .list_charts import run as list_charts
from .list_dashboards import run as list_dashboards

TOOL_DEFINITION = ToolDefinition(
    name="run-dashboard-chart",
    description="""Run a chart with dashboard context and filters applied.

This executes a chart query with dashboard-level filters applied, simulating how the chart would appear when viewed on a specific dashboard.

**Why use this instead of run-chart-query?**
- Dashboards can have filters that apply to all tiles
- This shows you the data as users see it on the dashboard
- Essential for verifying dashboard filter behavior

**When to use:** 
- To see chart results with dashboard filters applied
- To verify that dashboard filters are working correctly
- To debug discrepancies between chart and dashboard views
- To preview filtered data before modifying dashboard

**Returns:** Complete query results with dashboard context applied.""",
    inputSchema={
        "properties": {
            "dashboard_name": ToolParameter(
                type="string",
                description="Name of the dashboard for context (supports partial matching)"
            ),
            "chart_identifier": ToolParameter(
                type="string",
                description="Chart name (exact match) or UUID to execute with dashboard context"
            )
        },
        "required": ["dashboard_name", "chart_identifier"]
    }
)

def run(dashboard_name: str, chart_identifier: str) -> dict[str, Any]:
    """Run the run dashboard chart tool"""
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
    dashboard_filters = dashboard.get("filters", {})
    
    charts = list_charts()
    chart_uuid = None
    for chart in charts:
        if chart.get("uuid") == chart_identifier or chart.get("name", "").lower() == chart_identifier.lower():
            chart_uuid = chart.get("uuid")
            break
            
    if not chart_uuid:
        # Fallback: If identifier looks like a UUID (36 chars), try to use it directly
        # This handles charts that exist (e.g. dashboard-specific) but aren't in the main list
        if len(chart_identifier) == 36:
            chart_uuid = chart_identifier
        else:
            raise ValueError(f"Chart '{chart_identifier}' not found")
        
    url = f"/api/v1/saved/{chart_uuid}/results?dashboardUuid={dashboard_uuid}"    
    payload = {
        "filters": dashboard_filters
    }
    
    response = lightdash_client.post(url, data=payload)
    return response.get("results", {})

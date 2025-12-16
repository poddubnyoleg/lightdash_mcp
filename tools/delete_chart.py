from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .list_charts import run as list_charts

TOOL_DEFINITION = ToolDefinition(
    name="delete-chart",
    description="""Delete a saved chart from the project.

**Warning:** This is a destructive operation and cannot be undone.

**When to use:** 
- To remove outdated or incorrect charts
- To clean up test/development charts
- Before recreating a chart with the same name (delete old, create new)

**Important notes:**
- Charts still referenced on dashboards will show as broken/missing after deletion
- Consider checking which dashboards use this chart before deleting (use get-dashboard-tiles)
- For modifying existing charts, use update-chart instead of delete + recreate

**Accepts:** Either chart UUID or chart name (will search for exact match)""",
    inputSchema={
        "properties": {
            "chart_identifier": ToolParameter(
                type="string",
                description="Chart name (exact match) or UUID to delete"
            )
        },
        "required": ["chart_identifier"]
    }
)

def run(chart_identifier: str) -> str:
    """Run the delete chart tool"""
    charts = list_charts()
    
    chart_uuid = None
    chart_name = ""
    for chart in charts:
        if chart.get("uuid") == chart_identifier or chart.get("name", "").lower() == chart_identifier.lower():
            chart_uuid = chart.get("uuid")
            chart_name = chart.get("name")
            break
            
    if not chart_uuid:
        raise ValueError(f"Chart '{chart_identifier}' not found")
        
    lightdash_client.delete(f"/api/v1/saved/{chart_uuid}")
    
    return f"Successfully deleted chart '{chart_name}'"

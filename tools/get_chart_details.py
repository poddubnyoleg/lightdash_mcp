from typing import Any

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .list_charts import run as list_charts

TOOL_DEFINITION = ToolDefinition(
    name="get-chart-details",
    description="""Get detailed information about a specific saved chart.

Returns complete chart configuration including:
- Chart type and visualization settings (eChartsConfig)
- Metric query configuration (dimensions, metrics, filters, sorts)
- Table configuration (column order, conditional formatting)
- Metadata (name, description, space, timestamps)

**When to use:** 
- Before modifying or duplicating a chart
- To understand how a chart is configured
- To extract query logic for reuse
- To debug chart issues

**Accepts:** Either chart UUID or chart name (will search for exact match)""",
    inputSchema={
        "properties": {
            "chart_identifier": ToolParameter(
                type="string",
                description="Chart name (exact match) or UUID to look up"
            )
        },
        "required": ["chart_identifier"]
    }
)

def get_chart(chart_uuid: str) -> dict[str, Any]:
    response = lightdash_client.get(f"/api/v1/saved/{chart_uuid}")
    return response.get("results", {})

def run(chart_identifier: str) -> dict[str, Any]:
    """Run the get chart details tool"""
    charts = list_charts()
    
    chart_uuid = None
    for chart in charts:
        if chart.get("uuid") == chart_identifier:
            chart_uuid = chart_identifier
            break
            
    if not chart_uuid:
        for chart in charts:
            if chart.get("name", "").lower() == chart_identifier.lower():
                chart_uuid = chart.get("uuid")
                break
                
    if not chart_uuid:
        raise ValueError(f"Chart '{chart_identifier}' not found. Use list-charts to see available charts.")
        
    return get_chart(chart_uuid)

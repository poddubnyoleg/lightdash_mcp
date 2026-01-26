from typing import Any

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid
from .list_dashboards import run as list_dashboards

TOOL_DEFINITION = ToolDefinition(
    name="get-dashboard-tiles",
    description="""Get all tiles from a specific dashboard.

Returns a list of all tiles on the dashboard with their:
- UUID (unique identifier)
- Type (saved_chart, markdown, loom, etc.)
- Title or chart name
- savedChartUuid (for chart tiles)
- Position and size (x, y, h, w)
- OPTIONAL: Full chart configuration if include_full_config=true

**When to use:** 
- To see what content is on a dashboard before modifying it
- To find a tile's UUID for update or delete operations
- To understand the layout of a dashboard
- To find which charts are used on a dashboard
- To get full configuration of dashboard-only charts

**Search behavior:** Matches dashboard names case-insensitively with partial matching.""",
    inputSchema={
        "properties": {
            "dashboard_name": ToolParameter(
                type="string",
                description="Name of the dashboard (supports partial matching, e.g., 'Scale' will match 'Scale Dashboard')"
            ),
            "include_full_config": ToolParameter(
                type="boolean",
                description="Optional: If true, includes complete chart configuration for each tile (including dashboard-only charts). Default: false"
            )
        },
        "required": ["dashboard_name"]
    }
)

def get_dashboard(dashboard_uuid: str) -> dict[str, Any]:
    response = lightdash_client.get(f"/api/v1/dashboards/{dashboard_uuid}")
    return response.get("results", {})

def run(dashboard_name: str, include_full_config: bool = False) -> list[dict[str, Any]]:
    """Run the get dashboard tiles tool"""
    project_uuid = get_project_uuid()
    dashboards = list_dashboards(project_uuid)
    
    dashboard_uuid = None
    for dash in dashboards:
        if dash.get("name", "").lower() == dashboard_name.lower():
            dashboard_uuid = dash.get("uuid")
            break
    
    if not dashboard_uuid:
        for dash in dashboards:
            if dashboard_name.lower() in dash.get("name", "").lower():
                dashboard_uuid = dash.get("uuid")
                break
    
    if not dashboard_uuid:
        raise ValueError(f"Dashboard '{dashboard_name}' not found. Available dashboards: {[d.get('name') for d in dashboards]}")
    
    dashboard = get_dashboard(dashboard_uuid)
    tiles = dashboard.get("tiles", [])
    
    result = []
    for tile in tiles:
        tile_info = {
            "uuid": tile.get("uuid"),
            "type": tile.get("type"),
            "position": {
                "x": tile.get("x"),
                "y": tile.get("y"),
                "w": tile.get("w"),
                "h": tile.get("h")
            }
        }
        
        props = tile.get("properties", {})
        tile_info["title"] = props.get("title", "") or props.get("chartName", "")
        
        if tile.get("type") == "saved_chart":
            if "savedChartUuid" in props:
                tile_info["savedChartUuid"] = props["savedChartUuid"]
            elif "chartUuid" in props:
                tile_info["savedChartUuid"] = props["chartUuid"]
        
        if include_full_config:
            if "belongsToChart" in tile:
                chart_config = tile["belongsToChart"]
                tile_info["chart_configuration"] = {
                    "type": "dashboard_only",
                    "uuid": chart_config.get("uuid"),
                    "name": chart_config.get("name"),
                    "tableName": chart_config.get("tableName"),
                    "metricQuery": chart_config.get("metricQuery"),
                    "chartConfig": chart_config.get("chartConfig"),
                    "tableConfig": chart_config.get("tableConfig"),
                    "pivotConfig": chart_config.get("pivotConfig"),
                    "updatedAt": chart_config.get("updatedAt")
                }
            elif tile.get("type") == "saved_chart" and tile_info.get("savedChartUuid"):
                tile_info["chart_configuration"] = {
                    "type": "saved_chart_reference",
                    "savedChartUuid": tile_info["savedChartUuid"]
                }
        
        result.append(tile_info)
        
    return result

from typing import Any

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_dashboard_tiles import get_dashboard
from .get_project import get_project_uuid
from .list_dashboards import run as list_dashboards


def get_chart(chart_uuid: str) -> dict[str, Any]:
    response = lightdash_client.get(f"/api/v1/saved/{chart_uuid}")
    return response.get("results", {})

TOOL_DEFINITION = ToolDefinition(
    name="get-dashboard-tile-chart-config",
    description="""Get the complete chart configuration for a dashboard tile, including dashboard-only charts.

Dashboard-only charts store their full configuration (metric query, chart config, visualization settings) 
directly in the dashboard tile structure. This tool extracts that complete configuration.

**Returns:**
- Complete chart configuration including:
  - metricQuery: The query configuration (dimensions, metrics, filters, sorts)
  - chartConfig: Visualization configuration (chart type, axes, series)
  - tableConfig: Table column configuration
  - pivotConfig: Pivot configuration if applicable
- For saved charts: retrieves the chart via the savedChartUuid reference
- For dashboard-only charts: extracts from tile's belongsToChart property

**When to use:**
- To get full details of a a chart visible on a dashboard
- To understand the configuration of dashboard-only charts
- To export or duplicate dashboard-only chart configurations
- Before modifying a dashboard tile's chart

**Parameters:**
- dashboard_name: Name of the dashboard (supports partial matching)
- tile_identifier: Title of the tile or partial match""",
    inputSchema={
        "properties": {
            "dashboard_name": ToolParameter(
                type="string",
                description="Name of the dashboard (supports partial matching)"
            ),
            "tile_identifier": ToolParameter(
                type="string",
                description="Title of the tile or partial match to identify which tile"
            )
        },
        "required": ["dashboard_name", "tile_identifier"]
    }
)

def run(dashboard_name: str, tile_identifier: str) -> dict[str, Any]:
    """Run the get dashboard tile chart config tool"""
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
        raise ValueError(f"Dashboard '{dashboard_name}' not found")

    dashboard = get_dashboard(dashboard_uuid)
    tiles = dashboard.get("tiles", [])
    
    target_tile = None
    for tile in tiles:
        props = tile.get("properties", {})
        title = props.get("title", "") or props.get("chartName", "")
        
        if tile_identifier.lower() in title.lower():
            target_tile = tile
            break
            
    if not target_tile:
        available_tiles = []
        for tile in tiles:
            props = tile.get("properties", {})
            title = props.get("title", "") or props.get("chartName", "")
            if title:
                available_tiles.append(title)
        
        raise ValueError(f"Tile '{tile_identifier}' not found on dashboard. Available tiles: {available_tiles}")

    tile_type = target_tile.get("type")
    props = target_tile.get("properties", {})
    
    result = {
        "tile_uuid": target_tile.get("uuid"),
        "tile_type": tile_type,
        "title": props.get("title", "") or props.get("chartName", ""),
        "position": {
            "x": target_tile.get("x"),
            "y": target_tile.get("y"),
            "w": target_tile.get("w"),
            "h": target_tile.get("h")
        }
    }
    
    if tile_type == "saved_chart":
        if "belongsToChart" in target_tile:
            chart_config = target_tile["belongsToChart"]
            result["chart_type"] = "dashboard_only"
            result["configuration"] = {
                "uuid": chart_config.get("uuid"),
                "name": chart_config.get("name"),
                "tableName": chart_config.get("tableName"),
                "metricQuery": chart_config.get("metricQuery"),
                "chartConfig": chart_config.get("chartConfig"),
                "tableConfig": chart_config.get("tableConfig"),
                "pivotConfig": chart_config.get("pivotConfig"),
                "updatedAt": chart_config.get("updatedAt"),
                "updatedByUser": chart_config.get("updatedByUser")
            }
        elif "savedChartUuid" in props or "chartUuid" in props:
            chart_uuid = props.get("savedChartUuid") or props.get("chartUuid")
            result["chart_type"] = "saved_chart_reference"
            result["savedChartUuid"] = chart_uuid
            
            try:
                chart = get_chart(chart_uuid)
                result["configuration"] = {
                    "uuid": chart.get("uuid"),
                    "name": chart.get("name"),
                    "tableName": chart.get("tableName"),
                    "metricQuery": chart.get("metricQuery"),
                    "chartConfig": chart.get("chartConfig"),
                    "tableConfig": chart.get("tableConfig"),
                    "pivotConfig": chart.get("pivotConfig"),
                    "spaceUuid": chart.get("spaceUuid"),
                    "updatedAt": chart.get("updatedAt")
                }
            except Exception as e:
                result["error"] = f"Could not fetch saved chart: {str(e)}"
    elif tile_type == "markdown":
        result["chart_type"] = "markdown"
        result["configuration"] = {
            "content": props.get("content", ""),
            "title": props.get("title", "")
        }
    elif tile_type == "loom":
        result["chart_type"] = "loom"
        result["configuration"] = {
            "url": props.get("url", ""),
            "title": props.get("title", "")
        }
    elif tile_type == "sql_chart":
        result["chart_type"] = "sql_chart"
        result["configuration"] = {
            "note": "SQL charts are not fully supported via API. Configuration details may be limited."
        }
        if "belongsToChart" in target_tile:
            result["configuration"]["raw_data"] = target_tile["belongsToChart"]
    else:
        result["chart_type"] = "unknown"
        result["raw_properties"] = props
        
    return result

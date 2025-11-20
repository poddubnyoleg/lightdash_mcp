from typing import Any, Dict, List
import json

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .list_dashboards import run as list_dashboards
from .get_project import get_project_uuid
from .run_raw_query import run as run_metric_query
from .utils import flatten_rows

TOOL_DEFINITION = ToolDefinition(
    name="run-dashboard-tile",
    description="""Run any dashboard tile (saved chart OR dashboard-only chart) with filters.

This is the **primary tool** for getting data from a dashboard. It handles:
1.  **Saved Charts**: Executes the saved chart with dashboard filters applied.
2.  **Dashboard-Only Charts**: Merges dashboard filters with the chart's query and executes it.

**When to use:**
- When you want "the data for this tile" regardless of how it was created.

**Input:**
- `dashboard_name`: Name of the dashboard.
- `tile_uuid`: UUID of the tile to execute.

**Returns:**
- Query results (rows) with dashboard filters applied.
""",
    inputSchema={
        "properties": {
            "dashboard_name": ToolParameter(
                type="string",
                description="Name of the dashboard (supports partial matching)"
            ),
            "tile_uuid": ToolParameter(
                type="string",
                description="UUID of the tile to execute"
            )
        },
        "required": ["dashboard_name", "tile_uuid"]
    }
)

def _get_dashboard_by_name(dashboard_name: str) -> dict[str, Any]:
    """Helper to find and fetch full dashboard object by name"""
    project_uuid = get_project_uuid()
    dashboards = list_dashboards(project_uuid)
    
    dashboard_uuid = None
    # Exact match first
    for dash in dashboards:
        if dash.get("name", "").lower() == dashboard_name.lower():
            dashboard_uuid = dash.get("uuid")
            break
    
    # Partial match fallback
    if not dashboard_uuid:
        for dash in dashboards:
            if dashboard_name.lower() in dash.get("name", "").lower():
                dashboard_uuid = dash.get("uuid")
                break
                
    if not dashboard_uuid:
        raise ValueError(f"Dashboard '{dashboard_name}' not found")

    response = lightdash_client.get(f"/api/v1/dashboards/{dashboard_uuid}")
    return response.get("results", {})

def _merge_filters(chart_filters: Dict[str, Any], dashboard_filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge dashboard filters into chart filters.
    Strategy: Create a new root 'and' group containing the original chart filters and the dashboard filters.
    """
    if not dashboard_filters:
        return chart_filters
    
    if not chart_filters:
        return {"dimensions": dashboard_filters.get("dimensions", {}), "metrics": dashboard_filters.get("metrics", {})}

    merged = {"dimensions": {}, "metrics": {}}
    
    def merge_group(type_key):
        c_group = chart_filters.get(type_key, {})
        d_group = dashboard_filters.get(type_key, {})
        
        if not c_group and not d_group:
            return {}
        if not c_group:
            return d_group
        if not d_group:
            return c_group
            
        return {
            "id": "merged_root",
            "and": [
                c_group,
                d_group
            ]
        }

    merged["dimensions"] = merge_group("dimensions")
    merged["metrics"] = merge_group("metrics")
    
    return merged

def run(dashboard_name: str, tile_uuid: str) -> dict[str, Any]:
    """Run the run dashboard tile tool"""
    
    # 1. Fetch full dashboard (includes tiles and filters)
    dashboard = _get_dashboard_by_name(dashboard_name)
    dashboard_uuid = dashboard.get("uuid")
    dashboard_filters = dashboard.get("filters", {})
    tiles = dashboard.get("tiles", [])

    # 2. Find target tile
    target_tile = None
    
    for tile in tiles:
        if tile.get("uuid") == tile_uuid:
            target_tile = tile
            break
            
    if not target_tile:
        raise ValueError(f"Tile '{tile_uuid}' not found on dashboard '{dashboard_name}'")

    # 3. Determine execution strategy
    # Note: The tile structure from GET /dashboards/{uuid} might differ slightly from get_dashboard_tiles tool output
    # but generally contains 'properties' and 'type'.
    # For saved charts, properties has 'savedChartUuid'.
    # Actually, GET /dashboards/{uuid} returns tiles. If it's a saved chart, it has properties.savedChartUuid.
    # If it's a dashboard-only chart, the chart config is usually in properties or at the top level?
    # Let's inspect the tile structure handling.
    
    tile_type = target_tile.get("type")
    props = target_tile.get("properties", {})

    if tile_type == "saved_chart":
        saved_chart_uuid = props.get("savedChartUuid") or props.get("chartUuid")
        if not saved_chart_uuid:
             raise ValueError("Saved chart tile missing UUID")
             
        print(f"Executing saved chart {saved_chart_uuid}")
        
        # Execute saved chart with dashboard filters
        url = f"/api/v1/saved/{saved_chart_uuid}/results?dashboardUuid={dashboard_uuid}"    
        payload = {
            "filters": dashboard_filters
        }
        response = lightdash_client.post(url, data=payload)
        results = response.get("results", {})
        return {
            "rows": flatten_rows(results.get("rows", [])),
            "row_count": len(results.get("rows", [])),
            "fields": results.get("fields", {})
        }

    elif tile_type == "chart": # Dashboard-only charts are sometimes type 'chart' or have specific props
        # In some versions, dashboard-only charts might be type 'saved_chart' but without a savedChartUuid? 
        # Or type 'chart'? 
        # Based on get_dashboard_tiles.py, we looked for 'belongsToChart'.
        # 'belongsToChart' is usually hydrated by the backend when fetching the dashboard.
        
        # If the tile object from the API has 'properties' with 'chartName' but no 'savedChartUuid', 
        # it might be a dashboard-only chart.
        # However, the 'metricQuery' and 'tableName' are needed.
        # In the raw dashboard response, these might be in `properties` or `properties.chartConfig`?
        # Actually, looking at get_dashboard_tiles.py, it checks `if "belongsToChart" in tile:`.
        # This implies the raw API response includes `belongsToChart` for dashboard-only charts.
        
        chart_config = target_tile.get("properties", {})
        # If belongsToChart is at top level
        if "belongsToChart" in target_tile:
             chart_config = target_tile["belongsToChart"]
        
        metric_query = chart_config.get("metricQuery")
        if not metric_query:
             # Try looking deeper if structure varies
             if "chartConfig" in props and "metricQuery" in props:
                 metric_query = props.get("metricQuery")
                 explore_name = props.get("tableName")
             else:
                 raise ValueError(f"Could not find metric query for tile '{tile_uuid}'")
        else:
             explore_name = chart_config.get("tableName")

        title = props.get("title", "Untitled")
        print(f"Executing dashboard-only chart for tile '{title}'")
        
        # Merge filters
        original_filters = metric_query.get("filters", {})
        merged_filters = _merge_filters(original_filters, dashboard_filters)
        metric_query["filters"] = merged_filters
        
        return run_metric_query(explore_name, metric_query)

    else:
        # Fallback: It might be a markdown tile or other type
        raise ValueError(f"Tile '{tile_uuid}' is of type '{tile_type}' and cannot be executed as a chart.")

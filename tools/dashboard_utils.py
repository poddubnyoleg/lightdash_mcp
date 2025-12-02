from typing import Any, Dict, List
from .. import lightdash_client
from .get_project import get_project_uuid
from .list_dashboards import run as list_dashboards
from .run_raw_query import run as run_metric_query
from .utils import flatten_rows

def get_dashboard_by_name(dashboard_name: str) -> dict[str, Any]:
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

def execute_dashboard_tile(tile: dict[str, Any], dashboard_filters: dict[str, Any], dashboard_uuid: str) -> dict[str, Any]:
    """Execute a single dashboard tile with filters"""
    tile_uuid = tile.get("uuid")
    tile_type = tile.get("type")
    props = tile.get("properties", {})

    if tile_type == "saved_chart":
        saved_chart_uuid = props.get("savedChartUuid") or props.get("chartUuid")
        if not saved_chart_uuid:
             raise ValueError(f"Saved chart tile {tile_uuid} missing UUID")
        
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

    elif tile_type == "chart": 
        # Dashboard-only chart
        chart_config = tile.get("properties", {})
        if "belongsToChart" in tile:
             chart_config = tile["belongsToChart"]
        
        metric_query = chart_config.get("metricQuery")
        if not metric_query:
             if "chartConfig" in props and "metricQuery" in props:
                 metric_query = props.get("metricQuery")
                 explore_name = props.get("tableName")
             else:
                 raise ValueError(f"Could not find metric query for tile '{tile_uuid}'")
        else:
             explore_name = chart_config.get("tableName")

        title = props.get("title", "Untitled")
        
        # Merge filters
        original_filters = metric_query.get("filters", {})
        merged_filters = _merge_filters(original_filters, dashboard_filters)
        metric_query["filters"] = merged_filters
        
        return run_metric_query(explore_name, metric_query)

    else:
        raise ValueError(f"Tile '{tile_uuid}' is of type '{tile_type}' and cannot be executed as a chart.")

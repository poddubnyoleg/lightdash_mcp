import time
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

def _resolve_tile_targets(filters: List[Dict[str, Any]], tile_uuid: str) -> List[Dict[str, Any]]:
    """
    Resolve tileTargets for a specific tile.
    The UI pre-resolves the 'target' field using tileTargets[tileUuid] before sending to the API.
    
    If tileTargets[tile_uuid] is False, the filter doesn't apply to this tile and is skipped.
    """
    resolved = []
    for f in filters:
        tile_targets = f.get("tileTargets", {})
        
        # Determine the target for this tile
        if tile_uuid in tile_targets:
            tile_target = tile_targets[tile_uuid]
            # If tileTarget is False, this filter doesn't apply to this tile - skip it
            if tile_target is False:
                continue
            target = tile_target
        else:
            target = f.get("target", {})
            # If there's no tileTarget and no default target, skip this filter
            if not target:
                continue
        
        # Build a clean filter object with only the required fields
        # Handle null labels - convert to empty string
        label = f.get("label")
        if label is None:
            label = ""
        
        resolved_filter = {
            "id": f.get("id"),
            "label": label,
            "target": target,
            "values": f.get("values", []),
            "disabled": f.get("disabled", False),
            "operator": f.get("operator"),
            "settings": f.get("settings", {}),
            "tileTargets": tile_targets
        }
        
        # Add optional fields if present
        if "required" in f:
            resolved_filter["required"] = f["required"]
        if "singleValue" in f:
            resolved_filter["singleValue"] = f["singleValue"]
        
        resolved.append(resolved_filter)
    return resolved


def execute_dashboard_tile(tile: dict[str, Any], dashboard_filters: dict[str, Any], dashboard_uuid: str) -> dict[str, Any]:
    """Execute a single dashboard tile with filters using v2 API"""
    tile_uuid = tile.get("uuid")
    tile_type = tile.get("type")
    props = tile.get("properties", {})

    if tile_type == "saved_chart":
        saved_chart_uuid = props.get("savedChartUuid") or props.get("chartUuid")
        if not saved_chart_uuid:
             raise ValueError(f"Saved chart tile {tile_uuid} missing UUID")
        
        # Use v2 endpoint which properly handles dashboard filters with tileTargets
        # See: https://docs.lightdash.com/api-reference/query/execute-dashboard-chart
        project_uuid = get_project_uuid()
        url = f"/api/v2/projects/{project_uuid}/query/dashboard-chart"
        
        # Resolve tileTargets - the UI pre-resolves target using tileTargets[tileUuid]
        # before sending to the API. We must do the same.
        resolved_filters = {
            "dimensions": _resolve_tile_targets(dashboard_filters.get("dimensions", []), tile_uuid),
            "metrics": _resolve_tile_targets(dashboard_filters.get("metrics", []), tile_uuid),
            "tableCalculations": _resolve_tile_targets(dashboard_filters.get("tableCalculations", []), tile_uuid)
        }
        
        payload = {
            "context": "mcp",
            "chartUuid": saved_chart_uuid,
            "dashboardUuid": dashboard_uuid,
            "dashboardFilters": resolved_filters,
            "dashboardSorts": [],
            "dateZoom": {},
            "invalidateCache": False,
            "parameters": {},
            "pivotResults": False
        }
        
        # Step 1: Execute the query (async) - returns queryUuid
        response = lightdash_client.post(url, data=payload)
        results = response.get("results", {})
        query_uuid = results.get("queryUuid")
        fields = results.get("fields", {})
        
        if not query_uuid:
            raise ValueError("No queryUuid returned from dashboard-chart endpoint")
        
        # Step 2: Fetch the actual rows using the queryUuid (with polling)
        results_url = f"/api/v2/projects/{project_uuid}/query/{query_uuid}"
        
        max_attempts = 30
        for attempt in range(max_attempts):
            results_response = lightdash_client.get(results_url)
            query_results = results_response.get("results", {})
            status = query_results.get("status", "")
            
            if status == "ready":
                break
            elif status in ("error", "failed"):
                raise ValueError(f"Query failed with status: {status}")
            
            # Query still running, wait and retry
            time.sleep(0.5)
        
        rows = query_results.get("rows", [])
        
        return {
            "rows": flatten_rows(rows),
            "row_count": len(rows),
            "fields": fields
        }

    elif tile_type == "sql_chart":
        # SQL chart - uses savedSqlUuid
        saved_sql_uuid = props.get("savedSqlUuid")
        if not saved_sql_uuid:
            raise ValueError(f"SQL chart tile {tile_uuid} missing savedSqlUuid")
        
        project_uuid = get_project_uuid()
        url = f"/api/v2/projects/{project_uuid}/query/sql-chart"
        
        payload = {
            "savedSqlUuid": saved_sql_uuid,
            "context": "dashboardView",
            "invalidateCache": False
        }
        
        # Step 1: Execute the query (async) - returns queryUuid
        response = lightdash_client.post(url, data=payload)
        results = response.get("results", {})
        query_uuid = results.get("queryUuid")
        
        if not query_uuid:
            raise ValueError("No queryUuid returned from sql-chart endpoint")
        
        # Step 2: Fetch the actual rows using the queryUuid (with polling)
        results_url = f"/api/v2/projects/{project_uuid}/query/{query_uuid}"
        
        max_attempts = 30
        for attempt in range(max_attempts):
            results_response = lightdash_client.get(results_url)
            query_results = results_response.get("results", {})
            status = query_results.get("status", "")
            
            if status == "ready":
                break
            elif status in ("error", "failed"):
                raise ValueError(f"Query failed with status: {status}")
            
            # Query still running, wait and retry
            time.sleep(0.5)
        
        rows = query_results.get("rows", [])
        
        return {
            "rows": flatten_rows(rows),
            "row_count": len(rows),
            "fields": query_results.get("columns", {})
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
        
        # Merge filters
        original_filters = metric_query.get("filters", {})
        merged_filters = _merge_filters(original_filters, dashboard_filters)
        metric_query["filters"] = merged_filters
        
        return run_metric_query(explore_name, metric_query)

    else:
        raise ValueError(f"Tile '{tile_uuid}' is of type '{tile_type}' and cannot be executed as a chart.")

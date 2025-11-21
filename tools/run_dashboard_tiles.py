from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from .base_tool import ToolDefinition, ToolParameter
from .dashboard_utils import get_dashboard_by_name, execute_dashboard_tile
from .utils import format_as_csv

TOOL_DEFINITION = ToolDefinition(
    name="run-dashboard-tiles",
    description="""Run one or multiple dashboard tiles (or all tiles) concurrently.

This tool fetches the dashboard configuration once and then executes the selected tiles in parallel.

**When to use:**
- To download the entire dashboard data.
- To get data from multiple specific tiles at once (or from single tile).

**Returns:**
- A dictionary where keys are tile UUIDs and values contain:
  - `title`: Tile title
  - `status`: "success" or "error"
  - `csv_data`: CSV-formatted string with headers, data rows, and metadata (for successful tiles)
  - `error`: Error message (for failed tiles)
- Each CSV data includes a metadata comment line with row count and field information
- If a tile fails to execute, the value will contain an error message.
""",
    inputSchema={
        "properties": {
            "dashboard_name": ToolParameter(
                type="string",
                description="Name of the dashboard (supports partial matching)"
            ),
            "tile_uuids": ToolParameter(
                type="array",
                items={"type": "string"},
                description="Optional: List of tile UUIDs to execute. If omitted or empty, ALL chart tiles on the dashboard will be executed."
            )
        },
        "required": ["dashboard_name"]
    }
)

def run(dashboard_name: str, tile_uuids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run multiple dashboard tiles concurrently"""
    
    # 1. Fetch dashboard
    try:
        dashboard = get_dashboard_by_name(dashboard_name)
    except Exception as e:
        raise ValueError(f"Failed to fetch dashboard: {str(e)}")

    dashboard_uuid = dashboard.get("uuid")
    dashboard_filters = dashboard.get("filters", {})
    all_tiles = dashboard.get("tiles", [])
    
    # 2. Filter tiles to execute
    tiles_to_run = []
    if tile_uuids:
        # Create a map for O(1) lookup
        target_uuids = set(tile_uuids)
        for tile in all_tiles:
            if tile.get("uuid") in target_uuids:
                tiles_to_run.append(tile)
    else:
        # Run all chart tiles (saved_chart or chart)
        for tile in all_tiles:
            if tile.get("type") in ["saved_chart", "chart"]:
                tiles_to_run.append(tile)
                
    if not tiles_to_run:
        return {"results": {}, "message": "No matching chart tiles found to execute."}
        
    print(f"Executing {len(tiles_to_run)} tiles for dashboard '{dashboard.get('name')}'...")
    
    results = {}
    
    # 3. Execute in parallel
    # Limit max_workers to avoid overwhelming the API or Warehouse
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_tile = {
            executor.submit(execute_dashboard_tile, tile, dashboard_filters, dashboard_uuid): tile 
            for tile in tiles_to_run
        }
        
        for future in as_completed(future_to_tile):
            tile = future_to_tile[future]
            tile_uuid = tile.get("uuid")
            tile_title = tile.get("properties", {}).get("title") or tile.get("properties", {}).get("chartName") or "Untitled"
            
            try:
                data = future.result()
                # Convert rows to CSV format
                rows = data.get("rows", [])
                metadata = {
                    "row_count": data.get("row_count", len(rows)),
                    "fields": data.get("fields", {})
                }
                csv_data = format_as_csv(rows, metadata)
                
                results[tile_uuid] = {
                    "title": tile_title,
                    "status": "success",
                    "csv_data": csv_data
                }
            except Exception as e:
                results[tile_uuid] = {
                    "title": tile_title,
                    "status": "error",
                    "error": str(e)
                }
                
    return results

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_dashboard_tiles import get_dashboard
from .get_project import get_project_uuid
from .list_dashboards import run as list_dashboards

TOOL_DEFINITION = ToolDefinition(
    name="delete-dashboard-tile",
    description="""Delete a tile from a dashboard.

This permanently removes a tile from the dashboard. The operation cannot be undone.

**When to use:** 
- To remove outdated or unwanted tiles from a dashboard
- To clean up dashboards during reorganization
- To remove tiles before replacing them with updated versions

**Important notes:**
- This is a destructive operation - the tile cannot be recovered after deletion
- If the tile displays a saved chart, the chart itself is NOT deleted (only the tile reference)
- Dashboard-only charts (charts that exist only in the tile) will be permanently lost
- You should save the dashboard after deletion (this is done automatically)

**Search behavior:** Matches tile titles case-insensitively with partial matching.""",
    inputSchema={
        "properties": {
            "dashboard_name": ToolParameter(
                type="string",
                description="Name of the dashboard (supports partial matching)"
            ),
            "tile_identifier": ToolParameter(
                type="string",
                description="Title of the tile or partial match to identify which tile to delete (e.g., 'active users' will match 'Daily Active Users Chart')"
            )
        },
        "required": ["dashboard_name", "tile_identifier"]
    }
)

def run(dashboard_name: str, tile_identifier: str) -> str:
    """Run the delete dashboard tile tool"""
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
    
    tile_found = False
    deleted_tile_title = ""
    deleted_tile_uuid = ""
    
    tile_index_to_delete = -1
    
    for i, tile in enumerate(tiles):
        props = tile.get("properties", {})
        title = str(props.get("title") or props.get("chartName") or "")
        
        if tile_identifier.lower() in title.lower():
            tile_found = True
            tile_index_to_delete = i
            deleted_tile_title = title
            deleted_tile_uuid = tile.get('uuid')
            break
            
    if not tile_found:
        raise ValueError(f"Tile matching '{tile_identifier}' not found on dashboard '{dashboard_name}'")

    tiles.pop(tile_index_to_delete)
    
    update_payload = {
        "name": dashboard.get("name"),
        "tiles": tiles,
        "filters": dashboard.get("filters", {}),
        "tabs": dashboard.get("tabs", [])
    }
    
    lightdash_client.patch(f"/api/v1/dashboards/{dashboard_uuid}", data=update_payload)
    
    return f"Successfully deleted tile '{deleted_tile_title}' (UUID: {deleted_tile_uuid}) from dashboard '{dashboard_name}'"

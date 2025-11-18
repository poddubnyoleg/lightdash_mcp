from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_dashboard_tiles import get_dashboard
from .get_project import get_project_uuid
from .list_dashboards import run as list_dashboards

TOOL_DEFINITION = ToolDefinition(
    name="rename-dashboard-tile",
    description="""Rename a tile on a dashboard by updating its title property.

This is a convenience tool for the common operation of changing a tile's display name.

**When to use:** 
- To change the title of a markdown tile
- To override the display name of a chart tile
- Quick title updates without modifying other properties

**For more complex updates:** Use update-dashboard-tile to change multiple properties at once.""",
    inputSchema={
        "properties": {
            "dashboard_name": ToolParameter(
                type="string",
                description="Name of the dashboard (supports partial matching)"
            ),
            "tile_identifier": ToolParameter(
                type="string",
                description="Current title of the tile or partial match (e.g., 'active users' will match 'Daily Active Users Chart')"
            ),
            "new_title": ToolParameter(
                type="string",
                description="New title for the tile"
            )
        },
        "required": ["dashboard_name", "tile_identifier", "new_title"]
    }
)

def run(dashboard_name: str, tile_identifier: str, new_title: str) -> str:
    """Run the rename dashboard tile tool"""
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
    old_title = ""
    
    for i, tile in enumerate(tiles):
        props = tile.get("properties", {})
        title = props.get("title", "") or props.get("chartName", "")
        
        if tile_identifier.lower() in title.lower():
            tile_found = True
            old_title = title
            
            if "title" in props or not props.get("chartName"):
                tiles[i]["properties"]["title"] = new_title
            else:
                tiles[i]["properties"]["chartName"] = new_title
            break
            
    if not tile_found:
        raise ValueError(f"Tile matching '{tile_identifier}' not found on dashboard '{dashboard_name}'")

    update_payload = {
        "name": dashboard.get("name"),
        "tiles": tiles,
        "filters": dashboard.get("filters", {}),
        "tabs": dashboard.get("tabs", [])
    }
    
    lightdash_client.patch(f"/api/v1/dashboards/{dashboard_uuid}", data=update_payload)
    
    return f"Successfully renamed tile from '{old_title}' to '{new_title}' on dashboard '{dashboard_name}'"

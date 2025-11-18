import json

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_dashboard_tiles import get_dashboard
from .get_project import get_project_uuid
from .list_dashboards import run as list_dashboards

TOOL_DEFINITION = ToolDefinition(
    name="update-dashboard-tile",
    description="""Update any properties of a tile on a dashboard.

You can modify multiple tile properties in a single operation:

**Position properties** (at tile level):
- `x`, `y`: Change tile position
- `h`, `w`: Resize tile

**Display properties** (in properties object):
- `title`: Change display name
- `content`: Update markdown content
- `savedChartUuid`: Change which chart is displayed (for saved_chart tiles)
- Any other tile-specific properties

**CRITICAL - Grid System:**
Lightdash uses a **36-column grid** horizontally:
- For 2 tiles per row: `w: 18` each (x: 0 and x: 18)
- For 3 tiles per row: `w: 12` each (x: 0, x: 12, x: 24)
- For full-width tile: `w: 36`

**When to use:** 
- To reposition or resize tiles on a dashboard
- To update multiple tile properties at once
- To change content of markdown tiles
- To swap which chart is displayed in a chart tile

**Example properties_update values:**
- Two tiles per row: `{"x": 0, "y": 0, "h": 6, "w": 18}` and `{"x": 18, "y": 0, "h": 6, "w": 18}`
- Full width: `{"x": 0, "w": 36, "h": 6}`
- Reposition: `{"x": 0, "y": 10}`""",
    inputSchema={
        "properties": {
            "dashboard_name": ToolParameter(
                type="string",
                description="Name of the dashboard (supports partial matching)"
            ),
            "tile_identifier": ToolParameter(
                type="string",
                description="Current title of the tile or partial match to identify which tile to update"
            ),
            "properties_update": ToolParameter(
                type="string",
                description="JSON object string of properties to update. Position properties (x, y, h, w) go at tile level. Other properties go in properties object. Example: {\"x\": 0, \"y\": 5, \"title\": \"New Title\", \"w\": 12}"
            )
        },
        "required": ["dashboard_name", "tile_identifier", "properties_update"]
    }
)

def run(dashboard_name: str, tile_identifier: str, properties_update: str) -> str:
    """Run the update dashboard tile tool"""
    try:
        properties_update_data = json.loads(properties_update)
    except json.JSONDecodeError as e:
        return f"Error parsing properties_update JSON: {str(e)}"

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
    
    for i, tile in enumerate(tiles):
        props = tile.get("properties", {})
        title = props.get("title", "") or props.get("chartName", "")
        
        if tile_identifier.lower() in title.lower():
            tile_found = True
            
            position_props = {"x", "y", "h", "w"}
            for key, value in properties_update_data.items():
                if key in position_props:
                    tiles[i][key] = value
                else:
                    tiles[i]["properties"][key] = value
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
    
    return f"Successfully updated tile '{tile_identifier}' on dashboard '{dashboard_name}' with properties: {json.dumps(properties_update_data)}"

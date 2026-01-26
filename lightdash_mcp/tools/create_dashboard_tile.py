import json
import uuid

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_dashboard_tiles import get_dashboard
from .get_project import get_project_uuid
from .list_dashboards import run as list_dashboards

TOOL_DEFINITION = ToolDefinition(
    name="create-dashboard-tile",
    description="""Create a new tile and add it to an existing dashboard.

**Required for all tiles:**
- Position and size: `x`, `y`, `h`, `w` (in the properties JSON)
- Tile type: One of 'saved_chart', 'markdown', 'loom'

**Tile-specific requirements:**

*saved_chart tiles:*
- `savedChartUuid`: UUID of the chart to display (use list-charts to find)
- Optional: `title` to override the chart's name

*markdown tiles:*
- `title`: Display title
- `content`: Markdown content to display

*loom tiles:*
- `url`: Loom video URL
- Optional: `title`

**CRITICAL - Grid system:**
- Dashboard is **36 columns wide** (not 12!)
- `x` ranges from 0-35 (column position)
- `y` is row position (grows downward)
- `w` is width in columns (1-36)
- `h` is height in grid units
- For 2 tiles per row: use `w: 18` each
- For 3 tiles per row: use `w: 12` each
- For full width: use `w: 36`

**When to use:** 
- To add charts to a dashboard
- To add markdown documentation/headers
- To embed Loom videos for context

**Best practice:** Use get-dashboard-tiles first to see existing layout and find an empty position.""",
    inputSchema={
        "properties": {
            "dashboard_name": ToolParameter(
                type="string",
                description="Name of the dashboard (supports partial matching)"
            ),
            "tile_type": ToolParameter(
                type="string",
                description="Type of tile: 'saved_chart' (for charts), 'markdown' (for text), or 'loom' (for videos)"
            ),
            "properties": ToolParameter(
                type="string",
                description="JSON object string with tile properties. MUST include x, y, h, w for positioning. Example for chart: {\"x\": 0, \"y\": 0, \"h\": 6, \"w\": 18, \"savedChartUuid\": \"uuid-here\"}"
            ),
            "tab_uuid": ToolParameter(
                type="string",
                description="Optional: UUID of the tab to add the tile to. Leave empty to use the first tab (or no tab if dashboard has no tabs)."
            )
        },
        "required": ["dashboard_name", "tile_type", "properties"]
    }
)

def run(dashboard_name: str, tile_type: str, properties: str, tab_uuid: str = None) -> str:
    """Run the create dashboard tile tool"""
    try:
        properties_data = json.loads(properties)
    except json.JSONDecodeError as e:
        return f"Error parsing properties JSON: {str(e)}"

    required_props = ["x", "y", "h", "w"]
    missing_props = [p for p in required_props if p not in properties_data]
    if missing_props:
        raise ValueError(f"Missing required properties: {missing_props}. All tiles need x, y, h, w properties.")

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
    
    x = properties_data.pop("x")
    y = properties_data.pop("y")
    h = properties_data.pop("h")
    w = properties_data.pop("w")
    
    new_tile = {
        "uuid": str(uuid.uuid4()),
        "x": x,
        "y": y,
        "h": h,
        "w": w,
        "type": tile_type,
        "properties": properties_data,
        "tabUuid": None
    }
    
    if tab_uuid:
        new_tile["tabUuid"] = tab_uuid
    elif dashboard.get("tabs"):
        new_tile["tabUuid"] = dashboard["tabs"][0].get("uuid")
        
    tiles.append(new_tile)
    
    update_payload = {
        "name": dashboard.get("name"),
        "tiles": tiles,
        "filters": dashboard.get("filters", {}),
        "tabs": dashboard.get("tabs", [])
    }
    
    lightdash_client.patch(f"/api/v1/dashboards/{dashboard_uuid}", data=update_payload)
    
    return f"Successfully created new tile of type '{tile_type}' on dashboard '{dashboard_name}' with UUID: {new_tile['uuid']}"

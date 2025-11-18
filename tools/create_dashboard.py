import json

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="create-dashboard",
    description="""Create a new dashboard in the Lightdash project.

You can create an empty dashboard (just name and description) or a fully configured dashboard with tiles and tabs.

**Tile Types:**
- `saved_chart`: Display a saved chart (requires savedChartUuid in properties)
- `markdown`: Text/markdown content (requires title and content in properties)
- `loom`: Embedded Loom video (requires url in properties)

**Tile Position Properties (required for each tile):**
- `x`: Column position (0-indexed, grid is 12 columns wide)
- `y`: Row position (0-indexed)
- `h`: Height in grid units
- `w`: Width in grid units (max 12)

**When to use:** 
- To create a new empty dashboard that you'll populate later
- To create a fully configured dashboard from a template or copy
- Use duplicate-dashboard if you want to copy an existing dashboard

**Best practice:** Start with an empty dashboard, then use create-dashboard-tile to add content.""",
    inputSchema={
        "properties": {
            "name": ToolParameter(
                type="string",
                description="Name of the dashboard (must be unique within the project)"
            ),
            "description": ToolParameter(
                type="string",
                description="Optional: Description explaining the purpose of this dashboard"
            ),
            "tiles": ToolParameter(
                type="string",
                description="Optional: JSON string array of tiles to add to the dashboard. Each tile needs type, properties with x/y/h/w positioning. Example: [{\"uuid\": \"uuid1\", \"type\": \"markdown\", \"properties\": {\"title\": \"Welcome\", \"content\": \"# Hello\"}, \"x\": 0, \"y\": 0, \"h\": 4, \"w\": 12}]"
            ),
            "tabs": ToolParameter(
                type="string",
                description="Optional: JSON string array of tabs for organizing tiles. Example: [{\"uuid\": \"tab-uuid\", \"name\": \"Overview\", \"order\": 0}]"
            )
        },
        "required": ["name"]
    }
)

def run(name: str, description: str = "", tiles: str = "[]", tabs: str = "[]") -> str:
    """Run the create dashboard tool"""
    try:
        tiles_data = json.loads(tiles)
        tabs_data = json.loads(tabs)
    except json.JSONDecodeError as e:
        return f"Error parsing tiles or tabs JSON: {str(e)}"

    dashboard_payload = {
        "name": name,
        "description": description,
        "tiles": tiles_data,
        "tabs": tabs_data
    }
    
    project_uuid = get_project_uuid()
    response = lightdash_client.post(f"/api/v1/projects/{project_uuid}/dashboards", data=dashboard_payload)
    
    dashboard_uuid = response.get("results", {}).get("uuid", "")
    
    return f"Successfully created dashboard '{name}' with UUID: {dashboard_uuid}. Dashboard has {len(tiles_data)} tiles and {len(tabs_data)} tabs."

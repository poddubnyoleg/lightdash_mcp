import uuid

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_dashboard_tiles import get_dashboard
from .get_project import get_project_uuid
from .list_dashboards import run as list_dashboards

TOOL_DEFINITION = ToolDefinition(
    name="duplicate-dashboard",
    description="""Create a complete copy of an existing dashboard with a new name.

This copies everything from the source dashboard:
- All tiles with their positions and configurations
- All tabs (if the dashboard has tabs)
- Dashboard-level filters
- Layout and styling

**What gets regenerated:**
- Dashboard UUID (new unique ID)
- Tile UUIDs (new IDs for each tile)
- Tab UUIDs (new IDs for each tab)

**What stays the same:**
- Chart references (tiles still point to the same charts)
- Content and configuration
- Layout and positioning

**When to use:** 
- To create dashboard variants for different teams/regions
- To create a test version before modifying production dashboards
- To use an existing dashboard as a template
- To create regional/customer-specific versions

**Best practice:** Use descriptive names to distinguish the copy from the original.""",
    inputSchema={
        "properties": {
            "source_dashboard_name": ToolParameter(
                type="string",
                description="Name of the dashboard to copy (supports partial matching)"
            ),
            "new_dashboard_name": ToolParameter(
                type="string",
                description="Name for the new dashboard copy. Must be unique in the project."
            ),
            "new_description": ToolParameter(
                type="string",
                description="Optional: Description for the new dashboard. If omitted, copies the source dashboard's description."
            )
        },
        "required": ["source_dashboard_name", "new_dashboard_name"]
    }
)

def run(source_dashboard_name: str, new_dashboard_name: str, new_description: str = "") -> str:
    """Run the duplicate dashboard tool"""
    project_uuid = get_project_uuid()
    dashboards = list_dashboards(project_uuid)
    
    source_uuid = None
    for dash in dashboards:
        if dash.get("name", "").lower() == source_dashboard_name.lower():
            source_uuid = dash.get("uuid")
            break
            
    if not source_uuid:
        raise ValueError(f"Source dashboard '{source_dashboard_name}' not found")
        
    source_dashboard = get_dashboard(source_uuid)
    
    new_dashboard_data = {
        "name": new_dashboard_name,
        "description": new_description if new_description else source_dashboard.get("description", ""),
        "tiles": source_dashboard.get("tiles", []),
        "filters": source_dashboard.get("filters", {}),
        "tabs": source_dashboard.get("tabs", [])
    }
    
    for tile in new_dashboard_data["tiles"]:
        if "uuid" in tile:
            tile["uuid"] = str(uuid.uuid4())
            
    for tab in new_dashboard_data["tabs"]:
        if "uuid" in tab:
            old_uuid = tab["uuid"]
            new_uuid = str(uuid.uuid4())
            tab["uuid"] = new_uuid
            for tile in new_dashboard_data["tiles"]:
                if tile.get("tabUuid") == old_uuid:
                    tile["tabUuid"] = new_uuid
                    
    result = lightdash_client.post(f"/api/v1/projects/{project_uuid}/dashboards", data=new_dashboard_data)
    new_uuid = result.get("results", {}).get("uuid", "")
    
    return f"Successfully duplicated dashboard '{source_dashboard_name}' to '{new_dashboard_name}' with UUID: {new_uuid}"

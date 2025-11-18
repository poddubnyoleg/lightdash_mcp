from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .list_spaces import run as list_spaces

TOOL_DEFINITION = ToolDefinition(
    name="delete-space",
    description="""Delete a space (folder).

**Important constraints:**
- Cannot delete spaces that contain charts or dashboards
- Must move or delete all content from the space first
- This is a permanent operation

**When to use:** 
- To remove empty, unused spaces
- To clean up organizational structure
- After moving all content to other spaces

**Steps to delete a space with content:**
1. List charts and dashboards in the space
2. Move them to other spaces or delete them
3. Delete the now-empty space

**Accepts:** Either space UUID or space name (will search for exact match)""",
    inputSchema={
        "properties": {
            "space_identifier": ToolParameter(
                type="string",
                description="Space name (exact match) or UUID to delete. Space must be empty (no charts or dashboards)."
            )
        },
        "required": ["space_identifier"]
    }
)

def run(space_identifier: str) -> str:
    """Run the delete space tool"""
    spaces = list_spaces()
    
    space_uuid = None
    space_name = ""
    for space in spaces:
        if space.get("uuid") == space_identifier or space.get("name", "").lower() == space_identifier.lower():
            space_uuid = space.get("uuid")
            space_name = space.get("name")
            break
            
    if not space_uuid:
        raise ValueError(f"Space '{space_identifier}' not found")
        
    lightdash_client.delete(f"/api/v1/spaces/{space_uuid}")
    
    return f"Successfully deleted space '{space_name}'"

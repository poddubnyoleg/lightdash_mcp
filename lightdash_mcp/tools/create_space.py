from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="create-space",
    description="""Create a new space (folder) to organize charts and dashboards.

Spaces help organize content by:
- Team (e.g., "Marketing Analytics", "Finance")
- Product area (e.g., "User Growth", "Revenue")
- Development stage (e.g., "Production Dashboards", "Development")

**When to use:** 
- Before creating charts that belong to a new category
- To organize existing content into logical groups
- To set up restricted areas for sensitive data (use is_private=true)

**Best practices:**
- Use descriptive names that indicate content purpose
- Create private spaces for sensitive or work-in-progress content
- Get the space UUID from the response to use when creating charts""",
    inputSchema={
        "properties": {
            "name": ToolParameter(
                type="string",
                description="Name of the space. Should be descriptive and indicate the type of content it will contain."
            ),
            "is_private": ToolParameter(
                type="boolean",
                description="Whether the space is private (restricted access). Default: false (public space visible to all users)"
            )
        },
        "required": ["name"]
    }
)

def run(name: str, is_private: bool = False) -> str:
    """Run the create space tool"""
    space_data = {
        "name": name,
        "isPrivate": is_private
    }
    
    project_uuid = get_project_uuid()
    response = lightdash_client.post(f"/api/v1/projects/{project_uuid}/spaces", data=space_data)
    new_space_uuid = response.get("results", {}).get("uuid", "")
    
    return f"Successfully created space '{name}' with UUID: {new_space_uuid}"

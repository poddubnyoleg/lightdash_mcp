from typing import Any, Optional

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="get-custom-metrics",
    description="""Get custom metrics defined in the project.

Custom metrics are user-defined metrics created in the Lightdash UI that aren't part of the dbt model definitions. These are stored separately and can be used in charts and dashboards.

Returns:
- Custom metric definitions
- SQL expressions used to calculate them
- Associated tables/explores
- Labels and descriptions

**When to use:**
- To discover custom business metrics created by analysts
- To understand what custom calculations are available
- Before using a custom metric in a chart or query

**Note:** These are different from metrics defined in your dbt models.""",
    inputSchema={
        "properties": {
            "project_uuid": ToolParameter(
                type="string",
                description="Optional: UUID of the project. If not provided, uses current project."
            )
        }
    }
)

def run(project_uuid: Optional[str] = None) -> list[dict[str, Any]]:
    """Run the get custom metrics tool"""
    if not project_uuid:
        project_uuid = get_project_uuid()
    
    response = lightdash_client.get(f"/api/v1/projects/{project_uuid}/custom-metrics")
    return response.get("results", [])

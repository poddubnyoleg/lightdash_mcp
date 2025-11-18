from typing import Any, Optional

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="get-metrics-catalog",
    description="""Get the metrics catalog for a project.

Returns all metrics defined in the project with metadata including:
- Metric names and field IDs
- Metric types (count, sum, average, etc.)
- Which table/explore each metric belongs to
- Descriptions and labels
- Chart usage statistics

**When to use:**
- To discover available metrics for analysis
- To find metrics by business term or description
- To understand what aggregations are available
- Before creating charts to select appropriate metrics

**Difference from get-catalog:** This focuses only on metrics (aggregated measures), while get-catalog includes both dimensions and metrics.""",
    inputSchema={
        "properties": {
            "project_uuid": ToolParameter(
                type="string",
                description="Optional: UUID of the project. If not provided, uses current project."
            )
        }
    }
)

def run(project_uuid: Optional[str] = None) -> dict[str, Any]:
    """Run the get metrics catalog tool"""
    if not project_uuid:
        project_uuid = get_project_uuid()
    
    response = lightdash_client.get(f"/api/v1/projects/{project_uuid}/metrics")
    return response.get("results", {})

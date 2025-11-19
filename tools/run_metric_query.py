from typing import Any, Dict, Optional
import json

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="run-metric-query",
    description="""Execute a raw metric query against a Lightdash explore.

This tool allows you to run arbitrary queries by specifying dimensions, metrics, filters, and sorts directly.
It is useful for:
- Running ad-hoc analysis without creating a saved chart
- Executing queries for dashboard-only charts (which don't have a saved chart UUID)
- Debugging data issues by running simplified queries

**Input:**
- `explore_name`: The name of the explore (table) to query.
- `metric_query`: The query definition (dimensions, metrics, filters, etc.).
- `limit`: Optional row limit.

**Returns:**
- `rows`: Array of data rows.
- `metricQuery`: The query that was executed.
""",
    inputSchema={
        "properties": {
            "explore_name": ToolParameter(
                type="string",
                description="Name of the explore (table) to query (e.g., 'orders', 'customers')"
            ),
            "metric_query": ToolParameter(
                type="string",
                description="JSON string of the metric query configuration. Must include 'dimensions', 'metrics', etc."
            ),
            "limit": ToolParameter(
                type="number",
                description="Optional: Limit number of rows returned. Default is 500."
            )
        },
        "required": ["explore_name", "metric_query"]
    }
)

def run(explore_name: str, metric_query: str | Dict[str, Any], limit: Optional[int] = 500) -> dict[str, Any]:
    """Run the run metric query tool"""
    project_uuid = get_project_uuid()
    
    # Parse metric_query if it's a string
    if isinstance(metric_query, str):
        try:
            query_config = json.loads(metric_query)
        except json.JSONDecodeError:
            raise ValueError("metric_query must be a valid JSON string")
    else:
        query_config = metric_query

    # Ensure limit is set
    if limit:
        query_config['limit'] = limit

    url = f"/api/v1/projects/{project_uuid}/explores/{explore_name}/runQuery"
    
    response = lightdash_client.post(url, data=query_config)
    results = response.get("results", {})
    
    # Return simplified response
    return {
        "rows": results.get("rows", []),
        "row_count": len(results.get("rows", [])),
        "fields": results.get("fields", {}) # Keep fields as they are useful for understanding the data
    }

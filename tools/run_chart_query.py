from typing import Any

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .utils import flatten_rows

TOOL_DEFINITION = ToolDefinition(
    name="run-chart-query",
    description="""Execute a chart query and return the data results.

Runs the chart's configured query against the data warehouse and returns the results.

**Returns:**
- `rows`: Array of data rows (each row is an object with field names as keys)
- `row_count`: Total number of rows returned

**When to use:** 
- To get actual data from a chart for analysis
- To verify a chart is returning expected results
- To export chart data programmatically
- To preview data before creating a dashboard tile

**Performance notes:**
- Large result sets may take time to execute
- Use the `limit` parameter to restrict rows returned
- Query execution happens in real-time against your warehouse

**Optional limit parameter:** Restricts the number of rows returned (useful for large datasets)""",
    inputSchema={
        "properties": {
            "chart_uuid": ToolParameter(
                type="string",
                description="UUID of the chart to execute"
            ),
            "limit": ToolParameter(
                type="number",
                description="Optional: Limit number of rows returned. Useful for large datasets. Example: 100 will return max 100 rows"
            )
        },
        "required": ["chart_uuid"]
    }
)

def run(chart_uuid: str, limit: int = None) -> dict[str, Any]:
    """Run the run chart query tool"""
    # We no longer verify if the chart exists in the project list to save an API call.
    # The API will return a 404 if the chart UUID is invalid.
        
    url = f"/api/v1/saved/{chart_uuid}/results"
    
    payload = {}
    if limit:
        payload['limit'] = limit
        
    response = lightdash_client.post(url, data=payload)
    query_results = response.get("results", {})
    
    rows = query_results.get("rows", [])
    if limit is not None and isinstance(rows, list) and len(rows) > limit:
        rows = rows[:limit]
        
    return {"rows": flatten_rows(rows), "row_count": len(rows)}

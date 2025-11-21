from typing import Any, Dict, Optional, Union
import json

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid
from .utils import flatten_rows, format_as_csv

TOOL_DEFINITION = ToolDefinition(
    name="run-raw-query",
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

═══════════════════════════════════════════════════════════════════
COMPLETE WORKING EXAMPLE:
═══════════════════════════════════════════════════════════════════

metric_query:
{
  "dimensions": ["my_table_date_day"],
  "metrics": [],
  "filters": {
    "dimensions": {
      "id": "root",
      "and": [
        {
          "id": "filter_1",
          "target": {"fieldId": "my_table_country"},
          "operator": "equals",
          "values": ["US"]
        },
        {
          "id": "filter_2",
          "target": {"fieldId": "my_table_date_day"},
          "values": [30],
          "operator": "inThePast",
          "required": false,
          "settings": {
            "completed": false,
            "unitOfTime": "days"
          }
        }
      ]
    }
  },
  "sorts": [{"fieldId": "my_table_date_day", "descending": true}],
  "limit": 500,
  "tableCalculations": [],
  "additionalMetrics": [
    {
      "name": "dau",
      "label": "Daily Active Users",
      "description": "Count of unique users",
      "type": "count_distinct",
      "sql": "${TABLE}.user_id",
      "table": "my_table",
      "baseDimensionName": "user_id",
      "formatOptions": {"type": "default", "separator": "default"}
    }
  ]
}

**Key Rules:**
1. **Field IDs**: Use `table_field` format (e.g., `orders_amount`). Use `get-explore-schema` to find correct IDs.
2. **Filters**:
   - Simple: `{"operator": "equals", "values": ["value"]}`
   - Time: `{"operator": "inThePast", "values": [7], "settings": {"unitOfTime": "days", "completed": false}}`
3. **Additional Metrics**: Use this to create ad-hoc metrics (like count distinct) that aren't in the dbt model.
""",
    inputSchema={
        "properties": {
            "explore_name": ToolParameter(
                type="string",
                description="Name of the explore (table) to query (e.g., 'orders', 'customers')"
            ),
            "metric_query": ToolParameter(
                type="string",
                description="JSON string of the metric query configuration. Must include 'dimensions', 'metrics', etc. See description for example."
            ),
            "limit": ToolParameter(
                type="number",
                description="Optional: Limit number of rows returned. Default is 500."
            )
        },
        "required": ["explore_name", "metric_query"]
    }
)

def run(explore_name: str, metric_query: Union[str, Dict[str, Any]], limit: Optional[int] = 500) -> str:
    """Run the run raw query tool"""
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
    
    flattened_rows = flatten_rows(results.get("rows", []))
    metadata = {
        "row_count": len(flattened_rows),
        "fields": results.get("fields", {})
    }
    
    return format_as_csv(flattened_rows, metadata)

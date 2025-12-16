import json
from typing import Any

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_chart_details import get_chart as get_chart_details
from .list_charts import run as list_charts

TOOL_DEFINITION = ToolDefinition(
    name="update-chart",
    description="""Update an existing saved chart's configuration.

This tool allows partial updates - you only need to provide the fields you want to change.

**Updatable fields:**
- `name`: Chart name
- `description`: Chart description  
- `metric_query`: JSON string with metricQuery updates (dimensions, metrics, filters, sorts, etc.)
- `chart_config`: JSON string with chartConfig updates (visualization settings)
- `pivot_config`: JSON string with pivotConfig updates

**Common use cases:**

1. **Change sorting:**
   metric_query: {"sorts": [{"fieldId": "table_field_name", "descending": false}]}

2. **Update filters:**
   metric_query: {"filters": {"dimensions": {"id": "root", "and": [...]}}}

3. **Change chart type:**
   chart_config: {"type": "cartesian", "config": {...}}

4. **Add/remove dimensions or metrics:**
   metric_query: {"dimensions": ["dim1", "dim2"], "metrics": ["metric1"]}

**Important notes:**
- Uses PATCH endpoint - only provided fields are updated
- For metric_query updates, provide only the keys you want to change
- The tool merges your updates with the existing configuration
- Use get-chart-details first to see current configuration

**Example - Change sort to ascending by name:**
```
chart_identifier: "My Chart Name"
metric_query: {"sorts": [{"fieldId": "table_column_name", "descending": false}]}
```""",
    inputSchema={
        "properties": {
            "chart_identifier": ToolParameter(
                type="string",
                description="Chart name (exact match) or UUID to update"
            ),
            "name": ToolParameter(
                type="string",
                description="Optional: New name for the chart"
            ),
            "description": ToolParameter(
                type="string",
                description="Optional: New description for the chart"
            ),
            "metric_query": ToolParameter(
                type="string",
                description="Optional: JSON string with metricQuery fields to update (e.g., sorts, filters, dimensions, metrics)"
            ),
            "chart_config": ToolParameter(
                type="string",
                description="Optional: JSON string with chartConfig fields to update"
            ),
            "pivot_config": ToolParameter(
                type="string",
                description="Optional: JSON string with pivotConfig to update. Use null to remove pivot."
            )
        },
        "required": ["chart_identifier"]
    }
)


def deep_merge(base: dict, updates: dict) -> dict:
    """
    Deep merge updates into base dict.
    For lists, replaces entirely (doesn't merge list items).
    """
    result = base.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def run(
    chart_identifier: str,
    name: str = "",
    description: str = "",
    metric_query: str = "",
    chart_config: str = "",
    pivot_config: str = ""
) -> str:
    """Run the update chart tool"""
    
    # Find the chart
    charts = list_charts()
    
    chart_uuid = None
    chart_name = ""
    for chart in charts:
        if chart.get("uuid") == chart_identifier:
            chart_uuid = chart_identifier
            chart_name = chart.get("name", "")
            break
    
    if not chart_uuid:
        for chart in charts:
            if chart.get("name", "").lower() == chart_identifier.lower():
                chart_uuid = chart.get("uuid")
                chart_name = chart.get("name", "")
                break
    
    if not chart_uuid:
        raise ValueError(f"Chart '{chart_identifier}' not found. Use list-charts to see available charts.")
    
    # Get current chart config for reference and as base for updates
    current_chart = get_chart_details(chart_uuid)
    
    # Build version payload - start with current values
    base_metric_query = current_chart.get("metricQuery", {}).copy()
    # Remove fields that shouldn't be in the update
    base_metric_query.pop("metricOverrides", None)
    # Remove uuid from additionalMetrics as it's auto-generated
    for am in base_metric_query.get("additionalMetrics", []):
        am.pop("uuid", None)
    
    version_data: dict[str, Any] = {
        "tableName": current_chart.get("tableName"),
        "metricQuery": base_metric_query,
        "chartConfig": current_chart.get("chartConfig", {}),
        "tableConfig": current_chart.get("tableConfig", {}),
    }
    
    # Add optional fields if they exist in current chart
    if current_chart.get("pivotConfig"):
        version_data["pivotConfig"] = current_chart.get("pivotConfig")
    
    updated_fields = []
    
    # Apply updates
    if name:
        version_data["name"] = name
        updated_fields.append(f"name: '{name}'")
    
    if description:
        version_data["description"] = description
        updated_fields.append("description")
    
    if metric_query:
        try:
            metric_query_updates = json.loads(metric_query)
            # Merge with already-cleaned base_metric_query
            merged_metric_query = deep_merge(base_metric_query, metric_query_updates)
            version_data["metricQuery"] = merged_metric_query
            updated_fields.append(f"metricQuery ({', '.join(metric_query_updates.keys())})")
        except json.JSONDecodeError as e:
            return f"Error parsing metric_query JSON: {str(e)}"
    
    if chart_config:
        try:
            chart_config_updates = json.loads(chart_config)
            # Merge with existing chartConfig
            current_chart_config = current_chart.get("chartConfig", {})
            merged_chart_config = deep_merge(current_chart_config, chart_config_updates)
            version_data["chartConfig"] = merged_chart_config
            updated_fields.append("chartConfig")
        except json.JSONDecodeError as e:
            return f"Error parsing chart_config JSON: {str(e)}"
    
    if pivot_config:
        try:
            if pivot_config.lower() == "null":
                version_data["pivotConfig"] = None
                updated_fields.append("pivotConfig (removed)")
            else:
                pivot_config_data = json.loads(pivot_config)
                version_data["pivotConfig"] = pivot_config_data
                updated_fields.append("pivotConfig")
        except json.JSONDecodeError as e:
            return f"Error parsing pivot_config JSON: {str(e)}"
    
    if not updated_fields:
        return "No updates provided. Specify at least one field to update (name, description, metric_query, chart_config, or pivot_config)."
    
    # Create new version using POST endpoint
    try:
        result = lightdash_client.post(f"/api/v1/saved/{chart_uuid}/version", data=version_data)
        
        return f"✅ Successfully updated chart '{chart_name}' (UUID: {chart_uuid})\n\nUpdated fields: {', '.join(updated_fields)}"
    
    except Exception as e:
        return f"❌ Failed to update chart '{chart_name}':\n\n{str(e)}"

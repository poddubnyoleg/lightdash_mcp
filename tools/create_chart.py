import json

import requests

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid


def validate_chart_config(chart_config: dict, metric_query: dict) -> tuple[bool, str]:
    """
    Validate the eChartsConfig part of a chart configuration.
    - Ensures series have encode.xRef/yRef as objects, not strings.
    - Checks that referenced fields exist in the metric query.
    """
    if not isinstance(chart_config, dict) or "config" not in chart_config or "eChartsConfig" not in chart_config["config"]:
        return False, "chartConfig must be a dictionary with 'config' and 'eChartsConfig' keys."

    echarts_config = chart_config["config"]["eChartsConfig"]
    if "series" not in echarts_config or not isinstance(echarts_config["series"], list):
        return False, "eChartsConfig must have a 'series' list."

    # Get all available fields from the metric query
    available_fields = set(metric_query.get("dimensions", []))
    available_fields.update(metric_query.get("metrics", []))
    additional_metrics = metric_query.get("additionalMetrics", [])
    for am in additional_metrics:
        table = am.get("table", "")
        name = am.get("name", "")
        if table and name:
            available_fields.add(f"{table}_{name}")
    
    # Add custom dimensions to available fields
    custom_dimensions = metric_query.get("customDimensions", [])
    for cd in custom_dimensions:
        dim_id = cd.get("id", "")
        if dim_id:
            available_fields.add(dim_id)

    # Check each series configuration
    for i, series in enumerate(echarts_config["series"]):
        if "encode" not in series:
            return False, f"Series {i} is missing 'encode' configuration."
        
        encode = series["encode"]
        refs = {"xRef", "yRef"}
        
        for ref_key in refs:
            if ref_key in encode:
                ref_value = encode[ref_key]
                if not isinstance(ref_value, dict) or "field" not in ref_value:
                    return False, f"Series {i} '{ref_key}' must be an object with a 'field' key (e.g., {{\"field\": \"my_field\"}}). It should not be a plain string."
                
                # Check if the referenced field is valid
                field_id = ref_value["field"]
                if field_id not in available_fields:
                    return False, f"Series {i} references field '{field_id}' which is not present in the metricQuery dimensions, metrics, or additionalMetrics. Available fields: {sorted(available_fields)}"

    return True, ""

def build_table_config(metric_query: dict) -> dict:
    """
    Auto-generates the tableConfig.columnOrder from a metric query.
    The order is dimensions, custom dimensions, then metrics, then table calculations.
    """
    dimensions = metric_query.get("dimensions", [])
    metrics = metric_query.get("metrics", [])
    table_calcs = [tc.get("name") for tc in metric_query.get("tableCalculations", []) if tc.get("name")]
    
    # Add custom dimensions to the dimensions list for column ordering
    custom_dimensions = metric_query.get("customDimensions", [])
    custom_dim_ids = [cd.get("id") for cd in custom_dimensions if cd.get("id")]
    custom_dim_names = [cd.get("name") for cd in custom_dimensions if cd.get("name")]
    
    # Add additional metrics to the metrics list for column ordering
    additional_metrics = metric_query.get("additionalMetrics", [])
    for am in additional_metrics:
        table = am.get("table", "")
        name = am.get("name", "")
        if table and name:
            metric_field_id = f"{table}_{name}"
            if metric_field_id not in metrics:
                metrics.append(metric_field_id)

    # Include both custom dimension IDs and names (Lightdash shows both)
    column_order = dimensions + custom_dim_ids + custom_dim_names + metrics + table_calcs
    
    return {"columnOrder": column_order}

TOOL_DEFINITION = ToolDefinition(
    name="create-chart",
    description="""Create a new saved chart in a space. Requires table name, metric query, and chart configuration.

⚠️  CRITICAL: Chart configuration structure must be precise or the chart will break!

═══════════════════════════════════════════════════════════════════
COMPLETE WORKING EXAMPLE - Line Chart with Count Distinct Metric:
═══════════════════════════════════════════════════════════════════

metricQuery:
{
  "exploreName": "my_table",
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

chartConfig:
{
  "type": "cartesian",
  "config": {
    "layout": {
      "xField": "my_table_date_day",
      "yField": ["my_table_dau"],
      "flipAxes": false
    },
    "eChartsConfig": {
      "xAxis": [{"name": "Date"}],
      "yAxis": [{"name": "DAU"}],
      "series": [
        {
          "type": "line",
          "encode": {
            "xRef": {"field": "my_table_date_day"},
            "yRef": {"field": "my_table_dau"}
          },
          "yAxisIndex": 0
        }
      ]
    }
  }
}

pivotConfig (optional):
{
  "columns": ["my_table_country"]
}

═══════════════════════════════════════════════════════════════════
EXAMPLE WITH CUSTOM DIMENSIONS - Stacked/Segmented Charts:
═══════════════════════════════════════════════════════════════════

Use Case: Create grouped/segmented visualizations by categorizing data into
meaningful buckets (e.g., Top N + "Other" pattern, status groupings, etc.)

metricQuery:
{
  "exploreName": "your_table",
  "dimensions": ["your_table_date_day", "category_dimension"],
  "metrics": [],
  "filters": {
    "dimensions": {
      "id": "root",
      "and": [
        {
          "id": "filter_1",
          "target": {"fieldId": "your_table_date_day"},
          "values": [30],
          "operator": "inThePast",
          "required": false,
          "settings": {"completed": false, "unitOfTime": "days"}
        }
      ]
    }
  },
  "sorts": [{"fieldId": "your_table_date_day", "descending": true}],
  "limit": 500,
  "additionalMetrics": [
    {
      "name": "unique_count",
      "label": "Unique Count",
      "type": "count_distinct",
      "sql": "${TABLE}.identifier_column",
      "table": "your_table",
      "baseDimensionName": "identifier_column"
    }
  ],
  "customDimensions": [
    {
      "id": "category_dimension",
      "name": "Category Dimension",
      "type": "sql",
      "table": "your_table",
      "sql": "CASE\\n    WHEN raw_field = 'value1' THEN 'Category A'\\n    WHEN raw_field = 'value2' THEN 'Category B'\\n    WHEN raw_field IN ('value3', 'value4') THEN 'Category C'\\n    ELSE 'Other'\\n  END",
      "dimensionType": "string"
    }
  ]
}

chartConfig:
{
  "type": "cartesian",
  "config": {
    "layout": {
      "xField": "your_table_date_day",
      "yField": ["your_table_unique_count"],
      "flipAxes": false
    },
    "eChartsConfig": {
      "xAxis": [{"name": "Date"}],
      "yAxis": [{"name": "Count"}],
      "series": [
        {
          "type": "bar",
          "stack": "your_table_unique_count",
          "encode": {
            "xRef": {"field": "your_table_date_day"},
            "yRef": {"field": "your_table_unique_count"}
          },
          "yAxisIndex": 0
        }
      ]
    }
  }
}

pivotConfig:
{
  "columns": ["category_dimension"]
}

Key Pattern: The custom dimension "category_dimension" is:
1. Defined in customDimensions with SQL CASE logic
2. Added to dimensions array for grouping
3. Used in pivotConfig.columns to create separate stacks/segments per category
Result: One stacked segment per CASE branch, visualizing data by category over time

═══════════════════════════════════════════════════════════════════
KEY RULES (MUST FOLLOW):
═══════════════════════════════════════════════════════════════════

1. additionalMetrics naming:
   - Metrics are referenced as: "{table}_{metricName}"
   - Example: table="my_table", name="dau" → "my_table_dau"

2. series.encode MUST use objects (NOT strings):
   ✅ CORRECT:   "xRef": {"field": "my_table_date_day"}
   ❌ WRONG:     "xRef": "my_table_date_day"

3. eChartsConfig.series is required:
   - Must have at least one series object
   - Each series MUST have: type, encode.xRef, encode.yRef

4. Metric types for additionalMetrics:
   - "count_distinct": COUNT(DISTINCT field)
   - "count": COUNT(*)
   - "sum": SUM(field)
   - "avg": AVG(field)
   - "min": MIN(field)
   - "max": MAX(field)

5. Filter operators and structures:
   
   **Simple filters:**
   - "equals": {"operator": "equals", "values": ["US"]}
   - "notEquals": {"operator": "notEquals", "values": ["US"]}  
   - "contains": {"operator": "contains", "values": ["search_term"]}
   - "notNull": {"operator": "notNull"}
   - "isNull": {"operator": "isNull"}
   
   **Time-based filters (CRITICAL - note the structure):**
   The "inThePast" operator requires specific structure:
   {
     "id": "filter_1",
     "target": {"fieldId": "table_date_field"},
     "values": [30],                    # ← Number goes HERE in values array
     "operator": "inThePast",
     "required": false,
     "settings": {
       "completed": false,              # ← Must be FALSE (not true)
       "unitOfTime": "days"             # Options: "days", "weeks", "months", "years"
     }
   }
   
   ⚠️  Common mistakes to AVOID:
   ❌ WRONG: "settings": {"number": 30}  → Number does NOT go in settings
   ❌ WRONG: "completed": true           → Must be false
   ✅ CORRECT: "values": [30] + "completed": false

6. Pivot configuration:
   - Use pivotConfig to split series by dimension values
   - Example: {"columns": ["my_table_country"]} creates one line per country
   - This enables grouping/segmentation in charts

7. Custom Dimensions (customDimensions):
   - Create calculated dimensions using SQL expressions (CASE, CONCAT, etc.)
   - Custom dimensions can be used in dimensions array, pivots, and filters
   - Each custom dimension requires: id, name, type, table, sql, dimensionType
   
   **Structure:**
   {
     "id": "custom_dim_id",           # Unique identifier to reference in dimensions/pivots
     "name": "Custom Dimension Name",  # Display name shown in UI
     "type": "sql",                    # Always "sql" for custom dimensions
     "table": "base_table",            # Base table name (matches exploreName)
     "sql": "CASE WHEN ... THEN ... ELSE ... END",  # SQL expression
     "dimensionType": "string"         # Data type: "string", "number", "date", etc.
   }
   
   **Common Patterns:**
   
   a) Top N + "Other" grouping (reduce cardinality):
   {
     "id": "top_items_group",
     "sql": "CASE\n    WHEN item_name = 'TopItem1' THEN 'TopItem1'\n    WHEN item_name = 'TopItem2' THEN 'TopItem2'\n    WHEN item_name IN ('TopItem3', 'TopItem4') THEN 'TopItem3/4'\n    ELSE 'Other'\n  END",
     "dimensionType": "string"
   }
   
   b) Status/Category mapping:
   {
     "id": "status_group",
     "sql": "CASE\n    WHEN status IN ('active', 'pending') THEN 'Active'\n    WHEN status IN ('completed', 'archived') THEN 'Completed'\n    ELSE 'Other'\n  END",
     "dimensionType": "string"
   }
   
   c) Numeric bucketing:
   {
     "id": "value_bucket",
     "sql": "CASE\n    WHEN amount < 10 THEN 'Small'\n    WHEN amount < 100 THEN 'Medium'\n    ELSE 'Large'\n  END",
     "dimensionType": "string"
   }
   
   **Usage in metricQuery:**
   - Add to customDimensions array: "customDimensions": [...]
   - Reference by id in dimensions: "dimensions": ["table_date", "custom_dim_id"]
   - Use in pivots: "pivotConfig": {"columns": ["custom_dim_id"]}
   - Filter on custom dimensions just like regular dimensions
   
   **Benefits:**
   - Reduce high-cardinality dimensions to manageable segments
   - Apply business logic without modifying base tables
   - Create "Top N + Other" patterns for cleaner visualizations
   - Categorize raw values into meaningful groups
   
   **With Pivots - Creating Segmented Charts:**
   When a custom dimension is used in BOTH dimensions array AND pivotConfig.columns,
   Lightdash creates one separate series/segment per unique value from the CASE statement.
   Example: 5 CASE branches = 5 stacked segments in the chart.

═══════════════════════════════════════════════════════════════════
CHART TYPES:
═══════════════════════════════════════════════════════════════════

Line Chart:    series[].type = "line"
Bar Chart:     series[].type = "bar"
Area Chart:    series[].type = "line" + series[].areaStyle = {}
Stacked Area:  series[].type = "line" + series[].areaStyle = {} + series[].stack = "stack_name"

═══════════════════════════════════════════════════════════════════
VALIDATION:
═══════════════════════════════════════════════════════════════════

The server will automatically:
- Validate chart config structure (xRef/yRef objects)
- Validate field references match metricQuery
- Auto-generate tableConfig.columnOrder
- Add additionalMetrics to metrics array for proper display

If validation fails, you'll get a detailed error message.
""",
    inputSchema={
        "properties": {
            "name": ToolParameter(type="string", description="Name of the chart"),
            "table_name": ToolParameter(type="string", description="Name of the table/explore to query (use get-explore-schema to find available tables)"),
            "space_uuid": ToolParameter(type="string", description="UUID of the space to save the chart in (use list-spaces to find UUIDs)"),
            "metric_query": ToolParameter(type="string", description="JSON string of the metric query configuration (see description for complete example)"),
            "chart_config": ToolParameter(type="string", description="JSON string of the chart visualization configuration (see description for complete example with proper eChartsConfig structure)"),
            "pivot_config": ToolParameter(type="string", description="Optional: JSON string for pivot configuration to group data by dimension. Example: {\"columns\": [\"table_dimension\"]} creates separate series for each dimension value"),
            "description": ToolParameter(type="string", description="Optional description of the chart")
        },
        "required": ["name", "table_name", "space_uuid", "metric_query", "chart_config"]
    }
)

def run(name: str, table_name: str, space_uuid: str, metric_query: str, chart_config: str, pivot_config: str = "", description: str = "") -> str:
    """Run the create chart tool"""
    try:
        metric_query_data = json.loads(metric_query)
        chart_config_data = json.loads(chart_config)
        pivot_config_data = json.loads(pivot_config) if pivot_config else None
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {str(e)}"

    additional_metrics = metric_query_data.get("additionalMetrics", [])
    current_metrics = metric_query_data.get("metrics", [])
    
    for am in additional_metrics:
        table = am.get("table", "")
        name = am.get("name", "")
        if table and name:
            metric_field_id = f"{table}_{name}"
            if metric_field_id not in current_metrics:
                current_metrics.append(metric_field_id)
    
    metric_query_data["metrics"] = current_metrics
    
    is_valid, error_msg = validate_chart_config(chart_config_data, metric_query_data)
    if not is_valid:
        return f"❌ Chart configuration validation failed:\n\n{error_msg}\n\nPlease fix the configuration and try again. See the create-chart tool description for complete working examples."

    table_config = build_table_config(metric_query_data)
    
    chart_data = {
        "name": name,
        "description": description,
        "tableName": table_name,
        "metricQuery": metric_query_data,
        "chartConfig": chart_config_data,
        "tableConfig": table_config,
        "spaceUuid": space_uuid
    }
    
    if pivot_config_data:
        chart_data["pivotConfig"] = pivot_config_data
    
    project_uuid = get_project_uuid()
    
    try:
        result = lightdash_client.post(f"/api/v1/projects/{project_uuid}/saved", data=chart_data)
        new_chart_uuid = result.get("results", {}).get("uuid", "")
        
        pivot_info = f"\n\nPivot configuration: {json.dumps(pivot_config_data)}" if pivot_config_data else ""
        
        return f"✅ Successfully created chart '{name}' with UUID: {new_chart_uuid}\n\nColumns in table view: {table_config['columnOrder']}{pivot_info}"
    except requests.HTTPError as e:
        error_detail = str(e)
        try:
            error_json = e.response.json()
            error_detail = json.dumps(error_json, indent=2)
        except (ValueError, AttributeError):
            try:
                error_detail = e.response.text
            except AttributeError:
                error_detail = str(e)
        
        return f"❌ Failed to create chart '{name}':\n\n{error_detail}\n\nThe chart configuration passed validation but the API rejected it. This might indicate:\n- Invalid field references in filters\n- Table/explore '{table_name}' doesn't exist\n- Space UUID '{space_uuid}' is invalid\n\nUse get-explore-schema to verify table and field names."

from typing import Any

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="get-explore-schema",
    description="""Get the complete schema for an explore/table including all available dimensions, metrics, and joins.

This is **essential before creating charts** to understand what fields exist and their types.

**Returns:**
- **Base table information:** Name, label, description
- **All dimensions by table:** Field IDs, types, labels, descriptions
- **All metrics by table:** Field IDs, types, SQL, labels, descriptions
- **Joins:** How tables are connected, join types, join conditions
- **Summary statistics:** Counts of tables, dimensions, metrics

**Field information includes:**
- `fieldId`: Use this exact value in chart queries (format: `table_fieldname`)
- `type`: Field data type (string, number, date, timestamp, etc.)
- `label`: Human-readable name
- `description`: What the field represents
- `hidden`: Whether field is hidden by default
- `sql`: For metrics, the SQL expression used

**When to use:** 
- **Before creating any chart** - to find correct field IDs
- To understand available data and metrics
- To discover join relationships between tables
- To find field types for proper formatting
- To explore what analysis is possible with a data model

**Best practices:**
1. Start with get-catalog or get-metrics-catalog to find relevant explores
2. Use get-explore-schema on specific explores to get detailed field information
3. Copy exact fieldId values when building chart queries
4. Check field descriptions to ensure you're using the right data

**Hidden fields:** By default, hidden fields are excluded. Set include_hidden=true to see all fields including internal/technical ones.""",
    inputSchema={
        "properties": {
            "table_name": ToolParameter(
                type="string",
                description="Name of the table/explore to introspect. This is the exploreName from your dbt models (e.g., 'snowplow__events_processed', 'wallet_users', 'orders'). Use get-catalog to discover available explore names."
            ),
            "include_hidden": ToolParameter(
                type="boolean",
                description="Optional: Include hidden fields in the response (default: false). Hidden fields are typically internal or technical fields not meant for general use."
            )
        },
        "required": ["table_name"]
    }
)

def run(table_name: str, include_hidden: bool = False) -> dict[str, Any]:
    """Run the get explore schema tool"""
    project_uuid = get_project_uuid()
    
    try:
        response = lightdash_client.get(f"/api/v1/projects/{project_uuid}/explores/{table_name}")
        explore = response.get("results", {})
        
        base_table = explore.get("baseTable", table_name)
        tables = explore.get("tables", {})
        joins = explore.get("joinedTables", [])
        
        result = {
            "exploreName": explore.get("name", table_name),
            "baseTable": base_table,
            "label": explore.get("label", ""),
            "tags": explore.get("tags", []),
            "tables": {}
        }
        
        for table_key, table_data in tables.items():
            table_info = {
                "name": table_data.get("name", table_key),
                "label": table_data.get("label", ""),
                "description": table_data.get("description", ""),
                "dimensions": [],
                "metrics": []
            }
            
            dimensions = table_data.get("dimensions", {})
            for dim_key, dim_data in dimensions.items():
                if not include_hidden and dim_data.get("hidden", False):
                    continue
                
                table_info["dimensions"].append({
                    "name": dim_data.get("name", dim_key),
                    "fieldId": f"{table_key}_{dim_data.get('name', dim_key)}",
                    "type": dim_data.get("type", ""),
                    "label": dim_data.get("label", ""),
                    "description": dim_data.get("description", ""),
                    "hidden": dim_data.get("hidden", False),
                    "table": dim_data.get("table", table_key)
                })
            
            metrics = table_data.get("metrics", {})
            for metric_key, metric_data in metrics.items():
                if not include_hidden and metric_data.get("hidden", False):
                    continue
                
                table_info["metrics"].append({
                    "name": metric_data.get("name", metric_key),
                    "fieldId": f"{table_key}_{metric_data.get('name', metric_key)}",
                    "type": metric_data.get("type", ""),
                    "label": metric_data.get("label", ""),
                    "description": metric_data.get("description", ""),
                    "hidden": metric_data.get("hidden", False),
                    "table": metric_data.get("table", table_key),
                    "sql": metric_data.get("sql", "")
                })
            
            result["tables"][table_key] = table_info
            
        result["joins"] = []
        for join in joins:
            result["joins"].append({
                "table": join.get("table", ""),
                "type": join.get("type", "left"),
                "sqlOn": join.get("sqlOn", "")
            })
            
        total_dimensions = sum(len(t["dimensions"]) for t in result["tables"].values())
        total_metrics = sum(len(t["metrics"]) for t in result["tables"].values())
        
        result["summary"] = {
            "totalTables": len(result["tables"]),
            "totalDimensions": total_dimensions,
            "totalMetrics": total_metrics,
            "totalJoins": len(result["joins"])
        }
        
        return result
        
    except Exception as e:
        raise ValueError(f"Error fetching explore schema for '{table_name}': {str(e)}\n\nMake sure the explore/table name is correct. Use list-charts to see examples of table names used in existing charts.") from None

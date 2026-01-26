from typing import Any

from .base_tool import ToolDefinition, ToolParameter
from .list_charts import run as list_charts

TOOL_DEFINITION = ToolDefinition(
    name="search-charts",
    description="""Search for charts by name or description.

Performs case-insensitive partial matching against:
- Chart names
- Chart descriptions

Returns matching charts with their UUID, name, space, and description.

**When to use:** 
- To find charts related to a topic or metric
- When you know part of a chart's name but not the exact name
- To discover charts by business term (if described well)

**Difference from list-charts:** This searches both name AND description, while list-charts only filters by name.""",
    inputSchema={
        "properties": {
            "search_term": ToolParameter(
                type="string",
                description="Search term to match against chart names and descriptions (case-insensitive). Example: 'user retention' will match charts with those words in name or description"
            )
        },
        "required": ["search_term"]
    }
)

def run(search_term: str) -> list[dict[str, Any]]:
    """Run the search charts tool"""
    charts = list_charts()
    
    results = []
    for chart in charts:
        name = chart.get("name", "").lower()
        desc = chart.get("description", "").lower()
        if search_term.lower() in name or search_term.lower() in desc:
            results.append({
                "uuid": chart.get("uuid"),
                "name": chart.get("name"),
                "space": chart.get("spaceName", ""),
                "description": chart.get("description", "")
            })
            
    return results

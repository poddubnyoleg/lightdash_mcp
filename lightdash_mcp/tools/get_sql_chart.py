from typing import Any

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid

TOOL_DEFINITION = ToolDefinition(
    name="get-sql-chart",
    description="""Get a SQL Runner (saved SQL) chart's full definition — including its raw `sql`, `config`, and `limit`.

SQL Runner charts are a DIFFERENT entity from explore-based saved charts: they live under
`/api/v1/projects/{project}/sqlRunner/saved/{uuid}`, NOT `/api/v1/saved/{uuid}`. Because of that,
`get-chart-details` and `update-chart` return 404 on them. Use this tool for any dashboard tile
whose type is `sql_chart` (identified by a `savedSqlUuid` in get-dashboard-tiles).

**Returns:** savedSqlUuid, name, description, slug, sql, limit, config, chartKind, space, dashboard.

**When to use:**
- To read the raw SQL behind a SQL-chart tile (e.g. to debug or to find a hard-coded table/dataset)
- Before editing it with update-sql-chart (fetch the current sql/config to modify)

**Accepts:** the savedSqlUuid (from a sql_chart tile's `properties.savedSqlUuid`).""",
    inputSchema={
        "properties": {
            "saved_sql_uuid": ToolParameter(
                type="string",
                description="savedSqlUuid of the SQL Runner chart (from a sql_chart tile's properties.savedSqlUuid)"
            )
        },
        "required": ["saved_sql_uuid"]
    }
)


def get_sql_chart(saved_sql_uuid: str) -> dict[str, Any]:
    project_uuid = get_project_uuid()
    response = lightdash_client.get(
        f"/api/v1/projects/{project_uuid}/sqlRunner/saved/{saved_sql_uuid}"
    )
    return response.get("results", {})


def run(saved_sql_uuid: str) -> dict[str, Any]:
    """Run the get SQL chart tool"""
    return get_sql_chart(saved_sql_uuid)

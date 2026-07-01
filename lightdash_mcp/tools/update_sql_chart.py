import json
from typing import Any

from .. import lightdash_client
from .base_tool import ToolDefinition, ToolParameter
from .get_project import get_project_uuid
from .get_sql_chart import get_sql_chart

TOOL_DEFINITION = ToolDefinition(
    name="update-sql-chart",
    description="""Update a SQL Runner (saved SQL) chart's query, config, or limit.

SQL Runner charts live under `/api/v1/projects/{project}/sqlRunner/saved/{uuid}` and are NOT
reachable by `update-chart` (which only handles explore-based saved charts and 404s on these).
Use this for any `sql_chart` tile (identified by a `savedSqlUuid`).

**Two ways to change the SQL:**
1. `find` + `replace` — substring replacement on the CURRENT SQL. Ideal for repointing a table or
   dataset, e.g. find `project.old_dataset.tbl` replace `project.new_dataset.tbl`. Aborts (no write)
   if `find` is absent from the current SQL, so it is safe/idempotent to re-run.
2. `sql` — replace the ENTIRE SQL with this string.

Optionally also pass `config` (JSON string) and/or `limit`. Unspecified fields are preserved from the
current version. A new chart version is created; prior versions are retained (revertible).

**Workflow:** call `get-sql-chart` first to read the current SQL, then `update-sql-chart`.""",
    inputSchema={
        "properties": {
            "saved_sql_uuid": ToolParameter(
                type="string",
                description="savedSqlUuid of the SQL Runner chart to update"
            ),
            "find": ToolParameter(
                type="string",
                description="Optional: exact substring to find in the current SQL (used with 'replace')"
            ),
            "replace": ToolParameter(
                type="string",
                description="Optional: text to substitute for every occurrence of 'find'"
            ),
            "sql": ToolParameter(
                type="string",
                description="Optional: full new SQL string (alternative to find/replace)"
            ),
            "config": ToolParameter(
                type="string",
                description="Optional: JSON string to replace the chart config"
            ),
            "limit": ToolParameter(
                type="integer",
                description="Optional: new row limit"
            ),
        },
        "required": ["saved_sql_uuid"]
    }
)


def run(
    saved_sql_uuid: str,
    find: str = "",
    replace: str = "",
    sql: str = "",
    config: str = "",
    limit: Any = "",
) -> str:
    """Run the update SQL chart tool"""
    current = get_sql_chart(saved_sql_uuid)
    if not current:
        return f"❌ SQL chart '{saved_sql_uuid}' not found."

    cur_sql = current.get("sql", "")
    new_sql = cur_sql
    changed = []

    if sql:
        new_sql = sql
        changed.append("sql (full replace)")
    elif find:
        if find not in cur_sql:
            return (f"❌ 'find' text not present in current SQL — no change made "
                    f"(safe to re-run).\nfind: {find}")
        count = cur_sql.count(find)
        new_sql = cur_sql.replace(find, replace)
        changed.append(f"sql (replaced {count}x)")
    elif replace:
        return "❌ 'replace' provided without 'find'."

    versioned: dict[str, Any] = {
        "sql": new_sql,
        "config": current.get("config"),
        "limit": current.get("limit"),
    }

    if config:
        try:
            versioned["config"] = json.loads(config)
            changed.append("config")
        except json.JSONDecodeError as e:
            return f"❌ config is not valid JSON: {e}"

    if limit not in ("", None):
        try:
            versioned["limit"] = int(limit)
            changed.append("limit")
        except (ValueError, TypeError):
            return f"❌ limit must be an integer, got: {limit!r}"

    if not changed:
        return "No changes specified. Provide find+replace, sql, config, and/or limit."

    project_uuid = get_project_uuid()
    try:
        resp = lightdash_client.patch(
            f"/api/v1/projects/{project_uuid}/sqlRunner/saved/{saved_sql_uuid}",
            {"versionedData": versioned},
        )
    except Exception as e:
        return f"❌ Failed to update SQL chart '{current.get('name')}':\n\n{str(e)}"

    version = resp.get("results", {}).get("savedSqlVersionUuid", "")
    return (f"✅ Updated SQL chart '{current.get('name')}' ({saved_sql_uuid})\n"
            f"Changed: {', '.join(changed)}\nNew version: {version}")

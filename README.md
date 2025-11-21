# Lightdash MCP Server

A Model Context Protocol (MCP) server for interacting with [Lightdash](https://www.lightdash.com/), enabling LLMs to discover data, create charts, and manage dashboards programmatically.

## Features

This MCP server provides a comprehensive set of tools for the full data analytics workflow:

*   **Discovery**: Explore data catalogs, find tables/explores, and understand schemas
*   **Querying**: Execute queries with full filter, metric, and aggregation support
*   **Chart Management**: Create, read, update, and delete charts with complex visualizations
*   **Dashboard Management**: Build and manage dashboards with tiles, filters, and layouts
*   **Resource Organization**: Create and manage spaces for content organization

## Installation

### Prerequisites

*   Python 3.8+
*   A Lightdash instance (Cloud or self-hosted)
*   Lightdash Personal Access Token (obtain from your Lightdash profile settings)

### Setup

1.  **Clone this repository**:
    ```bash
    git clone <repository-url>
    cd lightdash_mcp
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

### Environment Variables

The server requires the following environment variables:

| Variable | Required | Description | Example |
| :--- | :---: | :--- | :--- |
| `LIGHTDASH_TOKEN` | ✅ | Your Lightdash Personal Access Token | `ldt_abc123...` |
| `LIGHTDASH_URL` | ✅ | Base URL of your Lightdash API | `https://app.lightdash.cloud/api/v1` |
| `CF_ACCESS_CLIENT_ID` | ❌ | Cloudflare Access Client ID (if behind CF Access) | - |
| `CF_ACCESS_CLIENT_SECRET` | ❌ | Cloudflare Access Client Secret (if behind CF Access) | - |

### Getting Your Lightdash Token

1. Log into your Lightdash instance
2. Go to **Settings** → **Personal Access Tokens**
3. Click **Generate new token**
4. Copy the token (starts with `ldt_`)

### Usage with Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lightdash": {
      "command": "python",
      "args": ["/absolute/path/to/lightdash_mcp/server.py"],
      "env": {
        "LIGHTDASH_TOKEN": "ldt_your_token_here",
        "LIGHTDASH_URL": "https://app.lightdash.cloud/api/v1"
      }
    }
  }
}
```

> **Note**: Replace `/absolute/path/to/` with the actual absolute path to your installation.

### Usage with Other MCP Clients

Export the environment variables before running:

```bash
export LIGHTDASH_TOKEN="ldt_your_token_here"
export LIGHTDASH_URL="https://app.lightdash.cloud/api/v1"
python server.py
```

## Available Tools

### 📊 Discovery & Metadata

| Tool | Description |
| :--- | :--- |
| `list-projects` | List all available Lightdash projects |
| `get-project` | Get detailed information about a specific project |
| `list-explores` | List all available explores/tables in a project |
| `get-explore-schema` | Get detailed schema for a specific explore (dimensions, metrics, joins) |
| `list-spaces` | List all spaces (folders) in the project |
| `get-custom-metrics` | Get custom metrics defined in the project |

### 📈 Chart Management

| Tool | Description |
| :--- | :--- |
| `list-charts` | List all saved charts, optionally filtered by name |
| `search-charts` | Search for charts by name or description |
| `get-chart-details` | Get complete configuration of a specific chart |
| `create-chart` | Create a new saved chart with metric query and visualization config |
| `run-chart-query` | Execute a chart's query and retrieve the data |
| `delete-chart` | Delete a saved chart |

### 📋 Dashboard Management

| Tool | Description |
| :--- | :--- |
| `list-dashboards` | List all dashboards in the project |
| `create-dashboard` | Create a new dashboard (empty or with tiles) |
| `duplicate-dashboard` | Clone an existing dashboard with a new name |
| `get-dashboard-tiles` | Get all tiles from a dashboard with optional full config |
| `get-dashboard-tile-chart-config` | Get complete chart configuration for a specific dashboard tile |
| `get-dashboard-code` | Get the complete dashboard configuration as code |
| `create-dashboard-tile` | Add a new tile (chart, markdown, or loom) to a dashboard |
| `update-dashboard-tile` | Update tile properties (position, size, content) |
| `rename-dashboard-tile` | Rename a dashboard tile |
| `delete-dashboard-tile` | Remove a tile from a dashboard |
| `update-dashboard-filters` | Update dashboard-level filters |
| `run-dashboard-tiles` | Execute one, multiple, or all tiles on a dashboard concurrently |

### 🔍 Query Execution

| Tool | Description |
| :--- | :--- |
| `run-chart-query` | Execute a saved chart's query and return data |
| `run-dashboard-tiles` | Run queries for dashboard tiles (supports bulk execution) |
| `run-raw-query` | Execute an ad-hoc metric query against any explore |

### 🗂️ Resource Management

| Tool | Description |
| :--- | :--- |
| `create-space` | Create a new space to organize charts and dashboards |
| `delete-space` | Delete an empty space |

## Project Structure

```
lightdash_mcp/
├── server.py                 # Main MCP server entry point
├── lightdash_client.py       # Lightdash API client with auth
├── requirements.txt          # Python dependencies
├── tools/                    # Tool implementations
│   ├── __init__.py          # Auto-discovery and tool registry
│   ├── base_tool.py         # Base tool interface
│   ├── utils.py             # Shared utilities
│   ├── dashboard_utils.py   # Dashboard-specific helpers
│   ├── list_projects.py     # Project listing tool
│   ├── get_project.py       # Project details tool
│   ├── list_explores.py     # Explore listing tool
│   ├── get_explore_schema.py # Schema introspection tool
│   ├── list_charts.py       # Chart listing tool
│   ├── search_charts.py     # Chart search tool
│   ├── get_chart_details.py # Chart details tool
│   ├── create_chart.py      # Chart creation tool
│   ├── run_chart_query.py   # Chart query execution
│   ├── delete_chart.py      # Chart deletion tool
│   ├── list_dashboards.py   # Dashboard listing tool
│   ├── create_dashboard.py  # Dashboard creation tool
│   ├── duplicate_dashboard.py # Dashboard duplication
│   ├── get_dashboard_tiles.py # Tile listing tool
│   ├── get_dashboard_tile_chart_config.py # Tile config retrieval
│   ├── get_dashboard_code.py # Dashboard config export
│   ├── create_dashboard_tile.py # Tile creation tool
│   ├── update_dashboard_tile.py # Tile update tool
│   ├── rename_dashboard_tile.py # Tile rename tool
│   ├── delete_dashboard_tile.py # Tile deletion tool
│   ├── update_dashboard_filters.py # Dashboard filter updates
│   ├── run_dashboard_tiles.py # Dashboard tile execution
│   ├── run_raw_query.py     # Ad-hoc query execution
│   ├── list_spaces.py       # Space listing tool
│   ├── create_space.py      # Space creation tool
│   ├── delete_space.py      # Space deletion tool
│   └── get_custom_metrics.py # Custom metrics retrieval
└── README.md                # This file
```

## Development

### Adding a New Tool

The server automatically discovers and registers tools from the `tools/` directory. To add a new tool:

1.  **Create a new file** in `tools/` (e.g., `my_new_tool.py`)

2.  **Define the tool**:
    ```python
    from pydantic import BaseModel, Field
    from .base_tool import ToolDefinition
    from .. import lightdash_client as client
    
    class MyToolInput(BaseModel):
        param1: str = Field(..., description="Description of param1")
    
    TOOL_DEFINITION = ToolDefinition(
        name="my-new-tool",
        description="Description of what this tool does",
        input_schema=MyToolInput
    )
    
    def run(param1: str) -> dict:
        """Execute the tool logic"""
        result = client.get(f"/some/endpoint/{param1}")
        return result
    ```

3.  **Restart the server** - the tool will be automatically registered

### Tool Registry

Tools are automatically discovered via `tools/__init__.py`, which:
*   Scans the `tools/` directory for Python modules
*   Imports each module (excluding utility modules)
*   Registers tools by their `TOOL_DEFINITION.name`

### Testing

You can test individual tools by importing them:

```python
from tools import tool_registry

# List all registered tools
print(tool_registry.keys())

# Test a specific tool
result = tool_registry['list-projects'].run()
print(result)
```

## Troubleshooting

### Authentication Errors

If you see `401 Unauthorized` errors:
*   Verify your `LIGHTDASH_TOKEN` is correct and starts with `ldt_`
*   Check that the token hasn't expired
*   Ensure you have the necessary permissions in Lightdash

### Connection Errors

If you see connection errors:
*   Verify `LIGHTDASH_URL` is correct (should end with `/api/v1`)
*   For Lightdash Cloud: use `https://app.lightdash.cloud/api/v1`
*   For self-hosted: use `https://your-domain.com/api/v1`
*   If behind Cloudflare Access, ensure `CF_ACCESS_CLIENT_ID` and `CF_ACCESS_CLIENT_SECRET` are set

### Tool Not Found

If a tool isn't showing up:
*   Check that the file is in the `tools/` directory
*   Ensure the file has a `TOOL_DEFINITION` variable
*   Verify the file isn't in the exclusion list in `tools/__init__.py`
*   Restart the MCP server

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add your changes with appropriate tests
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
*   [Lightdash Documentation](https://docs.lightdash.com/)
*   [Lightdash Community Slack](https://join.slack.com/t/lightdash-community/shared_invite/)
*   [MCP Documentation](https://modelcontextprotocol.io/)

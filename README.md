# Lightdash MCP Server

A Model Context Protocol (MCP) server for interacting with [Lightdash](https://www.lightdash.com/), enabling LLMs to discover data, create charts, and manage dashboards.

## Features

This MCP server provides a rich set of tools for the full data analytics workflow:

*   **Discovery**: Explore your data catalog, find tables, and understand schemas.
*   **Creation**: Create new charts and dashboards programmatically.
*   **Management**: Update dashboard layouts, resize tiles, and manage resources.
*   **Execution**: Run queries and fetch data from your charts.

## Installation

1.  Clone this repository:
    ```bash
    git clone <repository-url>
    cd lightdash_mcp
    ```

2.  Install dependencies (assuming you have a virtual environment set up):
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The server requires the following environment variables to be set. You can add these to your MCP client configuration (e.g., Claude Desktop config) or export them in your shell.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `LIGHTDASH_TOKEN` | **Required**. Your Lightdash Personal Access Token. | - |
| `LIGHTDASH_URL` | The base URL of your Lightdash instance. |  |
| `CF_ACCESS_CLIENT_ID` | Optional. Cloudflare Access Client ID (if behind CF Access). | - |
| `CF_ACCESS_CLIENT_SECRET` | Optional. Cloudflare Access Client Secret (if behind CF Access). | - |

### Usage with Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lightdash": {
      "command": "python",
      "args": ["/path/to/lightdash_mcp/server.py"],
      "env": {
        "LIGHTDASH_TOKEN": "your_token_here",
        "LIGHTDASH_URL": "https://app.lightdash.cloud/api/v1/org/projects" 
      }
    }
  }
}
```
*Note: Update the path and URL to match your setup.*

## Available Tools

### Discovery & Metadata
*   `get-catalog`: Get the complete data catalog for a project (explores, tables, metrics).
*   `get-explore-schema`: Get detailed schema for a specific explore/table.
*   `list-projects`: List all available projects.
*   `list-spaces`: List all spaces in the project.
*   `list-dashboards`: List all dashboards.
*   `list-charts`: List all saved charts.
*   `search-charts`: Search for charts by name.

### Chart Management
*   `create-chart`: Create a new saved chart with a specific metric query and visualization config.
*   `run-chart-query`: Execute a chart's query and get the data rows.
*   `get-chart-details`: Get full details and configuration of a specific chart.
*   `delete-chart`: Delete a saved chart.

### Dashboard Management
*   `create-dashboard`: Create a new empty dashboard.
*   `duplicate-dashboard`: Clone an existing dashboard.
*   `get-dashboard-tiles`: Get all tiles (charts, markdown) from a dashboard.
*   `update-dashboard-tile`: Update tile properties (position, size, title, content).
*   `update-dashboard-filters`: Update the filters applied to a dashboard.
*   `create-dashboard-tile`: Add a new tile to a dashboard.
*   `delete-dashboard-tile`: Remove a tile from a dashboard.
*   `rename-dashboard-tile`: Rename a specific tile.

### Resource Management
*   `create-space`: Create a new space to organize content.
*   `delete-space`: Delete an empty space.

## Development

The server is built using the `mcp` python SDK. Tools are modularized in the `tools/` directory and automatically loaded by `server.py`.

To add a new tool:
1.  Create a new file in `tools/` (e.g., `my_new_tool.py`).
2.  Define a `TOOL_DEFINITION` and a `run` function.
3.  The server will automatically pick it up on restart.

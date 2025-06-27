*This project is not affiliated with Notion. Use at your own risk.*

* Official Notion / MCP Github can be found -> https://github.com/makenotion/notion-mcp-server?tab=readme-ov-file.*

# Notion MCP Utilities

A collection of Python scripts for interacting with Notion via the Model Context Protocol (MCP) server. These tools allow you to list databases, query tickets, update page titles/descriptions, and explore Notion workspace resources using the Notion MCP Docker image.

## Features

- **List Notion Databases**: Discover all databases in your Notion workspace and identify where tickets or issues are tracked.
- **Query Refined Tickets**: Search for ticket information in a specific "Refined" database.
- **Update Page Title & Description**: Change the title and description of a Notion page by its ID.
- **List Workspace Contents**: Enumerate all databases and pages in your workspace, including their properties and sample entries.
- **List MCP Capabilities**: Explore all available actions, tools, and resources provided by the Notion MCP server.
- **Find Page ID**: Locate the page (row) ID for a specific entry (e.g., 'Current Tickets') in a database.

## Requirements

- Python 3.7+
- Docker (for running the Notion MCP server)
- A Notion integration token (`NOTION_TOKEN` environment variable)

## Setup

1. **Install Python dependencies** (if any are added in the future):
   ```sh
   pip install -r requirements.txt
   ```
   (Currently, only standard library modules are used.)

2. **Set your Notion integration token**:
   ```sh
   export NOTION_TOKEN=your_notion_secret_token
   ```

3. **Ensure Docker is running** and you can pull the `mcp/notion` image:
   ```sh
   docker pull mcp/notion
   ```

## Usage

Each script is executable and can be run directly from the command line. Example usages:

- **List all databases:**
  ```sh
  python list_databases.py
  ```
- **Query refined tickets:**
  ```sh
  python query_refined.py
  ```
- **Update a page's title and description:**
  ```sh
  python update_page_title_description.py --id <PAGE_ID> --title "New Title" --description "New description"
  ```
- **List workspace contents:**
  ```sh
  python list_workspace.py
  ```
- **List MCP server capabilities:**
  ```sh
  python list_mcp_capabilities.py
  ```
- **Find the page ID for 'Current Tickets':**
  ```sh
  python get_current_tickets_pageid.py
  ```

## Environment Variables

- `NOTION_TOKEN`: Your Notion integration token (required for all scripts).

## How It Works

All scripts communicate with the Notion MCP server via Docker, using JSON-RPC over stdin/stdout. The MCP server provides a unified interface to the Notion API, making it easy to automate workspace management and data extraction.

## License

MIT License

---

*This project is not affiliated with Notion. Use at your own risk.*

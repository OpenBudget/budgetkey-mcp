# OpenBudget MCP Server

An MCP server that provides access to the OpenBudget API, allowing you to query and search various budget-related datasets.

## Description

This project provides a FastMCP server that interfaces with Israel's OpenBudget data.</br>
Allowing easy access to budget data, contracts, and supports information.</br>
It serves as a bridge between the OpenBudget API and MCP clients.

This project is possible only thanks to amazing work of [OpenBudget/BudgetKey](https://github.com/OpenBudget/BudgetKey) team.</br>
See their [UsingTheAPI](https://github.com/OpenBudget/BudgetKey/blob/master/documentation/UsingTheAPI.md) for more details about the API used in this MCP server.</br>
If you wish to craft your own queries or tool you can use their [Redash](http://data.obudget.org/) to test them (You can see my queries in [ILBudgetServer.py](ILBudgetServer.py)).

## Features

- Full access to Israel's governmental budget data
- Real-time integration with the OpenBudget API
- Comprehensive search capabilities across multiple data categories
- Historical budget tracking and analysis
- Contract and support payment information retrieval
- Easy-to-use MCP interface for client applications

## Requirements

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

```bash
git clone <repository-url>
cd OpenBudget-mcp
uv venv
.venv\Scripts\activate
uv pip install -r pyproject.toml
uv lock
```

## Usage

Install and run the server using one of these methods:

1. For use with [Visual Studio Code (using Copilot)](https://code.visualstudio.com/download):</br>
Go to [vscode/mcp.json](/.vscode/mcp.json) and replace {YOUR-LOCAL-PATH} with the path you cloned the repo.</br>
VSCode should discover you server automatically.</br>
If that doesn't work, make sure you enabled MCP & MCP.Discovery in [vscode://settings/mcp](vscode://settings/mcp).</br>
Make sure to enable agent mode in your vscode copilot.</br>
![Agent Mode Enabled](AgentModeEnabled.png)

2. For use with [Claude AI Assistant](https://claude.ai):
```bash
fastmcp install server.py
```

3. For testing with MCP Inspector (Learn how at [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector)):
```bash
fastmcp dev server.py
```

## Available Datasets

The following datasets are available:
- budget_items_data
- income_items_data
- supports_data
- contracts_data
- entities_data
- budgetary_change_requests_data
- budgetary_change_transactions_data

## MCP Tools

### get_dataset_info

Get information about a dataset's structure, including its columns and database schema.

### search_dataset

Perform a full-text search within a dataset.

### query_dataset

Execute SQL queries on a dataset.

## MCP Resources

### available_datasets

Get a list of all available datasets.

## Error Handling

The tools will return appropriate error messages in the following cases:
- Invalid dataset name
- Invalid SQL query
- API request failures
- Network connectivity issues

## API Documentation

The server is based on the OpenBudget API. For more details about the API endpoints and data structure, refer to the OpenAPI specification in `budgetkey.yaml`.

## Contributing

We welcome contributions to help improve the DataGov Israel MCP server.</br>
Whether you want to add new tools, enhance existing functionality, or improve documentation, your input is valuable.

For examples of other MCP servers and implementation patterns, see the [Model Context Protocol servers repository](https://github.com/modelcontextprotocol/servers).

## License

This project is dual-licensed under:
- MIT License
- Creative Commons Attribution-ShareAlike 4.0 International License

See the [LICENSE](LICENSE) file for details.

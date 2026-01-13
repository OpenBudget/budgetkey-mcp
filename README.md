# BudgetKey MCP Server

An MCP (Model Context Protocol) server that provides access to the Israeli State Budget (BudgetKey) API through Claude and other AI assistants.

## Overview

The BudgetKey MCP Server enables AI assistants to query and analyze Israeli budget data, including:

- **Budget Book Data** (ספר התקציב) - Planned and executed state budget
- **Support Programs** - Budgetary support programs provided by the state
- **Support Transactions** - Individual payments under support programs
- **Procurement Contracts** - Government contracts with suppliers
- **Entities** - Information on organizations, companies, associations
- **State Revenues** - Data on taxes, fees, and revenues
- **Budget Change Requests** - Requests to modify the budget

Data is available from 1997 to 2025.

## Features

The server provides three main tools:

### DatasetInfo
Get comprehensive information about any dataset, including its columns and database schema. Always use this tool before querying a dataset.

**Parameters:**
- `dataset`: Dataset ID (e.g., `budget_items_data`, `contracts_data`)

### DatasetFullTextSearch
Perform free-text search on a dataset to find relevant items. Use this to locate textual identifiers before performing database queries.

**Parameters:**
- `dataset`: Dataset ID
- `q`: Search query text

### DatasetDBQuery
Execute SQL queries on a dataset's database to retrieve precise information. Always include the `item_url` field to provide direct links to the data.

**Parameters:**
- `dataset`: Dataset ID
- `query`: PostgreSQL-compatible SQL query
- `page_size`: Number of rows to return (default: 50)

## Available Datasets

| Dataset ID | Description |
|------------|-------------|
| `budget_items_data` | Budget book data - planned and executed expense budget |
| `support_programs_data` | Budgetary support programs |
| `supports_transactions_data` | Individual support payments to organizations |
| `contracts_data` | Government procurement contracts |
| `entities_data` | Corporations, companies, associations, local authorities |
| `income_items_data` | State revenues - taxes, fees, expected revenues |
| `budgetary_change_requests_data` | Budget change requests |
| `budgetary_change_transactions_data` | Budget change transactions |

## Installation

> **📖 For detailed integration instructions with Claude Desktop, VS Code, Cursor, and other clients, see the [Integration Guide](./INTEGRATION-GUIDE.md)**

### Quick Start: Claude Desktop

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "budgetkey": {
      "type": "http",
      "url": "https://next.obudget.org/mcp"
    }
  }
}
```

Restart Claude Desktop and you're ready to query Israeli budget data!

### Using Docker

```bash
docker run -p 8000:8000 ghcr.io/openbudget/budgetkey-mcp:latest
```

The server will be available at `http://localhost:8000/mcp`

**Note**: The Docker image is hosted on GitHub Container Registry under the OpenBudget organization.

### From Source

```bash
git clone https://github.com/OpenBudget/budgetkey-mcp.git
cd budgetkey-mcp
pip install -r requirements.txt
python server.py
```

## Usage Examples

### Example 1: Find Budget Information

1. Use `DatasetInfo` with `dataset="budget_items_data"` to understand the schema
2. Use `DatasetFullTextSearch` with `dataset="budget_items_data"` and `q="חינוך"` to find education-related items
3. Use `DatasetDBQuery` to get precise data:
   ```sql
   SELECT year, code, title, net_allocated, net_executed, item_url
   FROM budget_items_data
   WHERE year = 2025 AND title LIKE '%חינוך%'
   ORDER BY net_allocated DESC
   LIMIT 10
   ```

### Example 2: Find Organization Contracts

1. Use `DatasetInfo` with `dataset="entities_data"` to understand entity structure
2. Use `DatasetFullTextSearch` with `dataset="entities_data"` and `q="אוניברסיטת תל אביב"` to find the entity ID
3. Use `DatasetInfo` with `dataset="contracts_data"` to understand contract schema
4. Use `DatasetDBQuery` to query contracts for that entity

## API Base URL

The server connects to: `https://next.obudget.org`

This can be customized via the `BUDGETKEY_API_BASE` environment variable.

## Workflow

When using this MCP server, follow these steps:

1. **Identify**: Determine which datasets and identifiers are needed
2. **Learn Schema**: Use `DatasetInfo` to understand the dataset structure
3. **Search**: Use `DatasetFullTextSearch` to find precise identifiers (if needed)
4. **Query**: Use `DatasetDBQuery` with SQL to get the exact information
5. **Present**: Include links to data using the `item_url` field and offer download links from `download_url`

## Development

### Project Structure

```
budgetkey-mcp/
├── server.py              # Main MCP server implementation
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container definition
├── ci.sh                 # CI/CD build script
├── .github/
│   └── workflows/
│       └── deploy.yml    # GitHub Actions deployment
└── README.md             # This file
```

### Building

```bash
docker build -t ghcr.io/openbudget/budgetkey-mcp:latest .
```

**CI/CD**: The GitHub Actions workflow automatically builds and publishes Docker images to GitHub Container Registry on every push to `main`.

### Testing

```bash
# Start the server
python server.py

# Test the health check endpoint
curl http://localhost:8000/mcp/health

# To test MCP functionality, configure Claude Desktop to use http://localhost:8000/mcp
# or use an MCP client library to connect to the server
```

## Contributing

Contributions are welcome! Please open issues or pull requests on the GitHub repository.

## License

This project follows the same license as the BudgetKey project.

## Links

- [Integration Guide](./INTEGRATION-GUIDE.md) - Detailed setup for Claude Desktop, VS Code, Cursor, and Python
- [Docker Image](https://github.com/OpenBudget/budgetkey-mcp/pkgs/container/budgetkey-mcp) - GitHub Container Registry
- [BudgetKey Website](https://next.obudget.org)
- [BudgetKey API Documentation](https://next.obudget.org/api/docs)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)

## Support

For questions or issues:
- Open an issue on GitHub
- Contact the BudgetKey team through the main website

---

**Note:** The server communicates efficiently in both Hebrew (עברית) and English, as the Israeli budget data contains information in Hebrew.

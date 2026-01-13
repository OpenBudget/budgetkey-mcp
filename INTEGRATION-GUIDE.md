# BudgetKey MCP Server - Integration Guide

This guide provides detailed instructions for integrating the BudgetKey MCP Server with various AI clients and IDEs.

## Table of Contents

- [Claude Desktop](#claude-desktop)
- [Visual Studio Code (Cline Extension)](#visual-studio-code-cline-extension)
- [Cursor IDE](#cursor-ide)
- [Python Client (Direct Integration)](#python-client-direct-integration)
- [Remote vs Local Deployment](#remote-vs-local-deployment)
- [Troubleshooting](#troubleshooting)

---

## Claude Desktop

Claude Desktop natively supports MCP servers via HTTP connections.

### Option 1: Using Remote Server (Recommended for Production)

1. Open Claude Desktop Settings:
   - **macOS**: Claude Desktop → Settings → Developer → Edit Config
   - **Windows**: Settings → Developer → Edit Config

2. Add the BudgetKey MCP server to your `claude_desktop_config.json`:

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

3. Save the file and restart Claude Desktop.

4. Verify the connection:
   - Look for the 🔌 icon in Claude's interface
   - The BudgetKey server should appear in the list of available servers
   - You should see 3 tools: DatasetInfo, DatasetFullTextSearch, DatasetDBQuery

### Option 2: Using Local Development Server

If you're running the server locally for development:

```json
{
  "mcpServers": {
    "budgetkey-local": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**Note**: You must start the server manually first:
```bash
cd /path/to/budgetkey-mcp
python server.py
```

### Option 3: Using uv with Local Python Server

For running the server process directly from Python:

```json
{
  "mcpServers": {
    "budgetkey": {
      "command": "/path/to/uv",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "/path/to/budgetkey-mcp/server.py"
      ]
    }
  }
}
```

**Setup Requirements**:
- Install `uv`: `pip install uv`
- Update `/path/to/uv` to your actual uv installation path (find with `which uv`)
- Update `/path/to/budgetkey-mcp/server.py` to the actual path

---

## Visual Studio Code (Cline Extension)

The Cline extension for VS Code supports MCP servers through a configuration file.

### Setup Steps

1. Install the Cline extension from the VS Code marketplace

2. Create a `.vscode/mcp.json` file in your project root:

**For Remote Server:**
```json
{
  "servers": {
    "budgetkey": {
      "type": "http",
      "url": "https://next.obudget.org/mcp"
    }
  }
}
```

**For Local Development:**
```json
{
  "servers": {
    "budgetkey-local": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

3. If running locally, start the server:
```bash
cd /path/to/budgetkey-mcp
python server.py
```

4. In VS Code:
   - Open the Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
   - Run: `MCP: List Servers`
   - Start the BudgetKey MCP server
   - Open the Copilot pane (Ctrl+Shift+I / Cmd+Shift+I)
   - Switch to 'Agent' mode

5. Test the integration:
   - Ask: "What datasets are available in BudgetKey?"
   - The agent should have access to the 3 BudgetKey tools

---

## Cursor IDE

Cursor IDE has built-in support for MCP servers.

### Setup Steps

1. In Cursor, open Settings (Cmd+, or Ctrl+,)

2. Navigate to: **Tools & Integrations** → **MCP**

3. Click **Add Tool** and select **MCP Server**

4. In the configuration file that opens, add:

**For Remote Server:**
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

**For Local Development:**
```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "local-port",
      "description": "Local server port (default: 8000)",
      "default": "8000"
    }
  ],
  "servers": {
    "budgetkey-local": {
      "type": "http",
      "url": "http://localhost:${input:local-port}/mcp"
    }
  }
}
```

5. Save the configuration

6. If running locally, start the server first:
```bash
cd /path/to/budgetkey-mcp
python server.py
```

7. Test the integration in Cursor's AI chat

---

## Python Client (Direct Integration)

You can integrate the BudgetKey MCP server directly into Python applications using the MCP SDK.

### Installation

```bash
pip install mcp requests
```

### Example: Basic Connection

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_budgetkey_mcp():
    # For HTTP server
    server_url = "https://next.obudget.org/mcp"

    # Connect to the server
    async with stdio_client(
        StdioServerParameters(
            command="python",
            args=["-m", "mcp.server.stdio"],
            env={"MCP_SERVER_URL": server_url}
        )
    ) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [tool.name for tool in tools])

            # Call DatasetInfo tool
            result = await session.call_tool(
                "DatasetInfo",
                arguments={"dataset": "budget_items_data"}
            )
            print("Dataset info:", result)

# Run the example
asyncio.run(use_budgetkey_mcp())
```

### Example: Using Requests (Direct HTTP)

For simpler integration without the MCP SDK:

```python
import requests

def get_dataset_info(dataset_id: str):
    """Get information about a BudgetKey dataset."""
    url = "https://next.obudget.org/api/tables/{}/info".format(dataset_id)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

def search_dataset(dataset_id: str, query: str):
    """Search within a BudgetKey dataset."""
    url = "https://next.obudget.org/api/tables/{}/search".format(dataset_id)
    response = requests.get(url, params={"q": query}, timeout=30)
    response.raise_for_status()
    return response.json()

def query_dataset(dataset_id: str, sql_query: str, page_size: int = 50):
    """Execute SQL query on a BudgetKey dataset."""
    url = "https://next.obudget.org/api/tables/{}/query".format(dataset_id)
    params = {
        "query": sql_query,
        "page_size": page_size
    }
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    return response.json()

# Example usage
if __name__ == "__main__":
    # Get dataset information
    info = get_dataset_info("budget_items_data")
    print("Columns:", info.get("columns", []))

    # Search for items related to education
    results = search_dataset("budget_items_data", "חינוך")
    print("Search results:", len(results.get("results", [])))

    # Query budget data
    query_result = query_dataset(
        "budget_items_data",
        "SELECT year, title, net_allocated FROM budget_items_data WHERE year = 2025 LIMIT 10"
    )
    print("Query results:", query_result.get("rows", []))
```

---

## Remote vs Local Deployment

### Remote Server (Production)

**URL**: `https://next.obudget.org/mcp`

**Advantages**:
- ✅ Always available
- ✅ No setup required
- ✅ Production data
- ✅ Automatic updates

**Use when**:
- Working with real Israeli budget data
- Sharing with others
- Production applications

### Local Server (Development)

**URL**: `http://localhost:8000/mcp`

**Advantages**:
- ✅ Fast iteration
- ✅ Offline development
- ✅ Custom modifications
- ✅ Debugging capabilities

**Setup**:
```bash
# Clone the repository
git clone https://github.com/OpenBudget/budgetkey-mcp.git
cd budgetkey-mcp

# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

**Use when**:
- Developing new features
- Testing modifications
- Learning how the server works

---

## Troubleshooting

### Issue: Server Not Showing Up in Claude Desktop

**Solutions**:
1. Check the configuration file syntax (must be valid JSON)
2. Restart Claude Desktop completely
3. Check Claude Desktop logs:
   - **macOS**: `~/Library/Logs/Claude/mcp*.log`
   - **Windows**: `%APPDATA%\Claude\logs\mcp*.log`
4. Verify the server URL is accessible:
   ```bash
   curl https://next.obudget.org/mcp/health
   ```

### Issue: Local Server Won't Start

**Solutions**:
1. Check if port 8000 is already in use:
   ```bash
   lsof -i :8000  # macOS/Linux
   netstat -ano | findstr :8000  # Windows
   ```
2. Verify Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Check for errors in the terminal where you ran `python server.py`
4. Try a different port:
   ```python
   # Edit server.py, change the last line:
   mcp.run(transport='streamable-http', path='/mcp', host="0.0.0.0", port=8001)
   ```

### Issue: Tools Not Appearing

**Solutions**:
1. Verify the MCP connection is established (check for 🔌 icon in Claude)
2. Try asking: "What tools do you have access to?"
3. Restart the client application
4. Check that the server URL includes the `/mcp` path

### Issue: Queries Failing or Returning Errors

**Solutions**:
1. Test the underlying API directly:
   ```bash
   curl "https://next.obudget.org/api/tables/budget_items_data/info"
   ```
2. Check your SQL syntax (must be PostgreSQL-compatible)
3. Verify dataset names are correct (see README.md for list)
4. Review the error message - the server provides detailed error information

### Issue: Connection Timeout

**Solutions**:
1. Check your internet connection
2. Verify the server is running (for local development)
3. Check firewall settings
4. Try increasing timeout values in your client configuration

### Issue: Hebrew Text Not Displaying Properly

**Solutions**:
1. Ensure your terminal/IDE supports UTF-8 encoding
2. The server uses UTF-8 for all responses
3. Check client display settings for Unicode support

---

## Advanced Configuration

### Using Multiple MCP Servers

You can configure multiple MCP servers simultaneously. For example, combine BudgetKey with other data sources:

```json
{
  "mcpServers": {
    "budgetkey": {
      "type": "http",
      "url": "https://next.obudget.org/mcp"
    },
    "another-service": {
      "type": "http",
      "url": "https://example.com/mcp"
    }
  }
}
```

### Custom Server Configuration

For advanced use cases, you can customize the server:

1. Clone and modify `server.py`
2. Adjust `BUDGETKEY_API_BASE` environment variable:
   ```bash
   export BUDGETKEY_API_BASE=https://custom-api.example.com
   python server.py
   ```
3. Update tools or instructions as needed
4. Deploy your custom version

### Claude Code Permissions

When using Claude Code (CLI), you can pre-approve specific tools:

```json
{
  "permissions": {
    "allow": [
      "mcp__budgetkey__DatasetInfo",
      "mcp__budgetkey__DatasetFullTextSearch",
      "mcp__budgetkey__DatasetDBQuery"
    ],
    "deny": [],
    "ask": []
  }
}
```

---

## Best Practices

1. **Start with DatasetInfo**: Always call `DatasetInfo` first to understand the dataset structure
2. **Use Search for IDs**: When you need identifiers, use `DatasetFullTextSearch` first
3. **Include item_url**: Always include `item_url` in your SQL queries for direct links
4. **Filter by Time**: Always specify time periods in your queries
5. **Test Locally First**: When developing new integrations, test with a local server
6. **Monitor Logs**: Check server logs when debugging issues
7. **Cache Results**: Consider caching frequent query results to reduce API load

---

## Additional Resources

- [BudgetKey Website](https://next.obudget.org)
- [BudgetKey API Documentation](https://next.obudget.org/api/docs)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Main README](./README.md)

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [main README](./README.md) for general information
2. Open an issue on [GitHub](https://github.com/OpenBudget/budgetkey-mcp/issues)
3. Contact the BudgetKey team through the main website
4. Review server logs for detailed error messages

---

*Last updated: January 2026*

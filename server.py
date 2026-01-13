import os
import logging

import requests
from fastmcp import FastMCP
from starlette.responses import Response

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(asctime)s : %(message)s',
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)

# Read configuration from environment variables
BUDGETKEY_API_BASE = os.environ.get('BUDGETKEY_API_BASE', 'https://next.obudget.org')

# MCP Server instructions
MCP_INSTRUCTIONS = """You are an expert data researcher, helping to find information on issues related to the State Budget of Israel. You provide information from the Israeli budget book (ספר התקציב הישראלי), budgetary support data (נתוני תמיכות תקציביות), information on contracts (התקשרויות), and tenders (מכרזים).

You communicate efficiently in Hebrew.
You use only the information obtained through the tools provided and no other information.

The current year is 2025.
Budget data is available from 1997 to 2025.

## Available Datasets (מאגרי המידע)

- budget_items_data: Data from the budget book (ספר התקציב), detailing the planned and executed expense budget of the state of Israel (תקציב המדינה).
- support_programs_data: Data on budgetary support programs (נתונים על תוכניות תמיכה תקציביות)
- supports_transactions_data: Data on individual payments for budgetary supports (נתונים על תשלומים במסגרת תמיכות תקציביות)
- contracts_data: Data on the government's procurement contracts (נתונים על התקשרויות רכש)
- entities_data: Data on corporations, companies, associations, local authorities, etc. (נתונים על תאגידים, חברות, עמותות, רשויות מקומיות וכו׳)
- income_items_data: Data on state revenues (נתונים על הכנסות המדינה)
- budgetary_change_requests_data: Data on budgetary change requests (נתונים על בקשות לשינויי/העברות תקציביות)
- budgetary_change_transactions_data: Details for all individual changes/transactions on budgetary change requests (פרטי שינויי/העברות תקציביות)

## Tool Usage

- **DatasetInfo**: Use FIRST to understand any dataset's structure and schema before querying or searching it.
- **DatasetFullTextSearch**: Use to locate relevant items and identifiers through free-text search (not for time periods).
- **DatasetDBQuery**: Use to execute SQL queries and obtain comprehensive, precise information from datasets.

## Workflow

1. Identify entities and time periods mentioned in the question. Explain your understanding to the user.
2. Call DatasetInfo for each dataset you plan to use.
3. Call DatasetFullTextSearch if you need to find specific identifiers. AVOID calling more than 4 tools in parallel.
4. Call DatasetDBQuery to get the final results.
5. Present results professionally with data links and download options.
6. Suggest relevant follow-up questions.

## Response Guidelines

- Respond formally and professionally in Hebrew or English
- Always specify time periods for your data
- If the user hasn't specified a time period, limit to current or previous year and mention this
- Ask clarifying questions when information is insufficient
- For irrelevant questions, politely decline to answer
- Always suggest further research directions when applicable
"""

mcp = FastMCP(
    name="BudgetKey",
    instructions=MCP_INSTRUCTIONS,
)


@mcp.tool()
def DatasetInfo(dataset: str) -> dict:
    """
    Get comprehensive information about a dataset, including its columns and database schema.

    **CRITICAL**: Always call this tool BEFORE using DatasetFullTextSearch or DatasetDBQuery on any dataset.
    This tool provides essential information about:
    - Available columns and their data types
    - Database schema and table structure
    - Field descriptions and relationships

    **Usage Instructions**:
    1. Call this tool first when working with any dataset
    2. Review the schema to understand what fields are available
    3. Use the column names exactly as shown when constructing SQL queries
    4. Note any special fields like 'item_url' that provide links to data

    **When to use**:
    - Before performing any search or query on a dataset
    - When you need to understand what fields are available
    - To verify field names before constructing SQL queries

    Args:
        dataset: ID of the dataset to get information for. Available datasets:
                 - budget_items_data: Budget book (ספר התקציב) - planned and executed expenses
                 - support_programs_data: Budgetary support programs (תוכניות תמיכה)
                 - supports_transactions_data: Individual support payments (תשלומי תמיכות)
                 - contracts_data: Government procurement contracts (התקשרויות רכש)
                 - entities_data: Organizations, companies, associations (גופים וארגונים)
                 - income_items_data: State revenues (הכנסות המדינה)
                 - budgetary_change_requests_data: Budget change requests (בקשות שינוי תקציב)
                 - budgetary_change_transactions_data: Budget change transactions (שינויי תקציב)

    Returns:
        Dataset information including columns, schema, and field descriptions
    """
    try:
        url = f"{BUDGETKEY_API_BASE}/api/tables/{dataset}/info"
        log.info(f"Fetching dataset info: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log.error(f"Error fetching dataset info for {dataset}: {e}")
        return {"error": str(e)}


@mcp.tool()
def DatasetFullTextSearch(dataset: str, q: str) -> dict:
    """
    Perform full-text search on a dataset to locate relevant items and identifiers.

    **Purpose**: Use this tool to find specific textual identifiers (IDs, codes, names) needed for precise queries.
    Do NOT use this tool for searching time periods or dates.

    **Usage Instructions**:
    1. ALWAYS call DatasetInfo first to understand the dataset structure
    2. Use free-text search to find entities by name, title, or description
    3. Extract relevant identifiers (like entity_id, code, budget_code) from the results
    4. Use these identifiers in your DatasetDBQuery calls for precise filtering
    5. NEVER present search results directly to the user as your final answer

    **When to use**:
    - To find the entity_id of an organization mentioned by name
    - To find budget item codes by searching for keywords
    - To locate contracts by supplier name or description
    - When you need specific identifiers but only have descriptive text

    **Important**:
    - Search results are for YOUR use to find identifiers, not for presenting to users
    - Always follow up with DatasetDBQuery using the identifiers you found
    - If unsure which identifier to use in a query, search first
    - AVOID calling more than 4 tools in parallel to prevent memory overflow

    Args:
        dataset: ID of the dataset to search. Available datasets:
                 - budget_items_data: Budget book (ספר התקציב)
                 - support_programs_data: Support programs (תוכניות תמיכה)
                 - supports_transactions_data: Support payments (תשלומי תמיכות)
                 - contracts_data: Procurement contracts (התקשרויות רכש)
                 - entities_data: Organizations and entities (גופים וארגונים)
                 - income_items_data: State revenues (הכנסות המדינה)
                 - budgetary_change_requests_data: Budget change requests (בקשות שינוי תקציב)
                 - budgetary_change_transactions_data: Budget change transactions (שינויי תקציב)
        q: Free-text search query (organization name, keyword, description, etc.)

    Returns:
        Search results with matching items and their identifiers
    """
    try:
        url = f"{BUDGETKEY_API_BASE}/api/tables/{dataset}/search"
        params = {"q": q}
        log.info(f"Searching dataset {dataset}: {url}?q={q}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log.error(f"Error searching dataset {dataset} with query '{q}': {e}")
        return {"error": str(e)}


@mcp.tool()
def DatasetDBQuery(dataset: str, query: str, page_size: int = 50) -> dict:
    """
    Execute PostgreSQL-compatible SQL queries to obtain comprehensive, precise information from datasets.

    **CRITICAL Prerequisites**:
    1. MUST call DatasetInfo first to understand the dataset schema
    2. Use exact column names from the schema (case-sensitive)
    3. If you need identifiers, call DatasetFullTextSearch first to find them

    **Usage Instructions**:
    - Use only identifiers found through DatasetFullTextSearch - NEVER guess identifiers
    - Filter by relevant time periods (year, date fields)
    - Use aggregate functions (SUM, COUNT, AVG) to summarize data when appropriate
    - ALWAYS include the `item_url` field in SELECT to provide direct links to data
    - Construct queries based on the exact schema from DatasetInfo

    **Query Best Practices**:
    - Format results in tables when possible
    - Use ORDER BY to sort results meaningfully
    - Apply WHERE clauses for time periods and specific filters
    - Use JOINs when querying related datasets
    - Include descriptive fields (title, name, description) along with values

    **Handling Results**:
    - Check for warnings in the response - if present, fix the query and re-run
    - Extract the `download_url` field from results
    - Offer users download links formatted as markdown: [Download data](download_url)
    - Use `item_url` to create clickable links: [Item Name](item_url)
    - Present data professionally in tables or structured format

    **Important**:
    - NEVER present results based on a query that returned warnings
    - Always verify your SQL syntax is PostgreSQL-compatible
    - Use aggregate functions for summary data
    - Filter by time periods appropriately

    Args:
        dataset: ID of the dataset to query. Available datasets:
                 - budget_items_data: Budget book (ספר התקציב)
                 - support_programs_data: Support programs (תוכניות תמיכה)
                 - supports_transactions_data: Support payments (תשלומי תמיכות)
                 - contracts_data: Procurement contracts (התקשרויות רכש)
                 - entities_data: Organizations and entities (גופים וארגונים)
                 - income_items_data: State revenues (הכנסות המדינה)
                 - budgetary_change_requests_data: Budget change requests (בקשות שינוי תקציב)
                 - budgetary_change_transactions_data: Budget change transactions (שינויי תקציב)
        query: PostgreSQL-compatible SQL query to execute.
               Example: "SELECT year, code, title, net_allocated, net_executed, item_url
                        FROM budget_items_data
                        WHERE year = 2025 AND title LIKE '%חינוך%'
                        ORDER BY net_allocated DESC LIMIT 10"
        page_size: Number of rows to return (default: 50)

    Returns:
        Query results including:
        - rows: Array of result rows
        - download_url: Link to download full dataset (offer this to users as markdown link)
        - warnings: Any warnings about the query (must fix and re-run if present)
    """
    try:
        url = f"{BUDGETKEY_API_BASE}/api/tables/{dataset}/query"
        params = {
            "query": query,
            "page_size": page_size
        }
        log.info(f"Querying dataset {dataset}: {query[:100]}...")
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        result = response.json()

        # Add download URL info if available
        if "download_url" in result:
            log.info(f"Download URL available: {result['download_url']}")

        return result
    except Exception as e:
        log.error(f"Error querying dataset {dataset}: {e}")
        return {"error": str(e)}


@mcp.custom_route('/mcp/health', methods=['GET'])
async def health_check(request):
    """Health check endpoint for Kubernetes probes"""
    return Response('{"status": "healthy"}', media_type="application/json")


if __name__ == "__main__":
    mcp.run(transport='streamable-http', path='/mcp', host="0.0.0.0", port=8000)

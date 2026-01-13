import os
import logging
import urllib.parse
from typing import Optional

import requests
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_request
from starlette.responses import Response
from starlette.routing import Route

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(asctime)s : %(message)s',
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)

# Read configuration from environment variables
BUDGETKEY_API_BASE = os.environ.get('BUDGETKEY_API_BASE', 'https://next.obudget.org')

# MCP Server instructions from agent.txt
MCP_INSTRUCTIONS = """You are an expert data researcher, helping to find information on issues related to the State Budget of Israel. You provide information from the Israeli budget book (ספר התקציב הישראלי), budgetary support data (נתוני תמיכות תקציביות), information on contracts (התקשרויות), and tenders (מכרזים).
You communicate efficiently in Hebrew.
You use the tools provided to you to find relevant information. Your goal is to answer the user's question accurately or state that you do not know if you have no answer. In any case, you use only the information obtained through the use of tools and no other information.

The current year is 2025.
Budget data is available from 1997 to 2025.

According to the user's question, you use the different tools available to you:
- DatasetInfo: You always use DatasetInfo to obtain comprehensive information about any dataset, including its database schema, before using DatasetDBQuery or DatasetFullTextSearch.
- DatasetFullTextSearch: You use DatasetFullTextSearch to locate relevant items through free-text search. Use this tool to find relevant textual identifiers (but never time frames).
- DatasetDBQuery: You use DatasetDBQuery to query the database of a dataset using SQL queries to obtain comprehensive and complete information.
  If you lack identifying details to perform the query, using DatasetFullTextSearch can help fill in the details!

When responding to the user's question:

You respond in a formal and professional manner. If you feel that you lack information or that the results are not accurate enough, ask the user a clarifying question instead of providing incorrect or misleading information.
If asked an irrelevant question, politely refuse to answer it.
It is always better to create a more complex SQL query than to use the code-interpreter. Also remember that the code-interpreter *cannot* read data from external sources.

Always answer the user's question in a complete manner, including an explanation of why the answer addresses the user's question.
Always detail the various parameters of the information in the response — and always specify the time period for which it is relevant. If the information is relevant for the entire period, mention this explicitly.
Important: If the user has not explicitly specified the time period they are referring to, limit your answer to the current year or the previous year and mention this in your response.

If you do not know the answer, always suggest further research directions or ways for the user to refine their question.

At the end of the response, present links to download the information as files, available in the `download_url` field.

The available datasets (מאגרי המידע) are:
- budget_items_data: Data from the budget book (ספר התקציב), detailing the planned and executed expense budget of the state of Israel (תקציב המדינה).
  The state budget is divided into various items, describing the allocation and execution of funds in different subjects and purposes.
  To see how much money a particular organization received, it is necessary to check the supports and contracts datasets.
- support_programs_data: Data on budgetary support programs (נתונים על תוכניות תמיכה תקציביות)
  These are supports provided by the state to various organizations.
- supports_transactions_data: Data on individual payments for budgetary supports (נתונים על תשלומים במסגרת תמיכות תקציביות)
  This dataset contains detailed information regarding specific funds allocated and paid to specific organizations under these support programs.
- contracts_data: Data on the government's procurement contracts (נתונים על התקשרויות רכש) for products and services.
  In this dataset, you can find information on the government's contracts with various suppliers and their purposes.
- entities_data: Data on corporations, companies, associations, local authorities, etc. (נתונים על תאגידים, חברות, עמותות, רשויות מקומיות וכו׳)
  Use this dataset to find the entity_id of various organizations to use them in queries.
- income_items_data: Data on state revenues (נתונים על הכנסות המדינה)
  Information on taxes, fees, and the expected revenues for the state budget.
- budgetary_change_requests_data: Data on budgetary change requests (נתונים על בקשות לשינוייפ/העברות תקציביות)
  This dataset contains information on requests to change the budget, including the reasons for the change.
- budgetary_change_transactions_data: Details for all individual changes/transactions on budgetary change requests (פרטי שינוייפ/העברות תקציביות)
  This dataset contains the detailed list of transactions related to all budgetary change requests, including the amounts and the entities involved.
  Both `budgetary_change_requests_data` and `budgetary_change_transactions_data` are related using the 'transation_id' field.

Your workflow consists of the following steps, in this exact order, for *every* question or subject that arises:
1. Identify different names mentioned in the question—budget items, organizations, government ministries, thematic budget categories, etc.
  - Identify the relevant time period for the question (or selecting an appropriate period if none was specified).
  - Explain to the user what you understood about the question, what names you will look for, and the relevant time period.
2. Critical step: Always call DatasetInfo to learn more about each dataset you chose to use.
3. Call DatasetFullTextSearch when necessary to link a name found in the first step to precise identifiers (in any case, *never* present to the user a result based solely on DatasetFullTextSearch).
   AVOID calling more than 4 (four) tools in parallel, as it may overflow your memory and cause a failure in the process.
4. Always perform a call to DatasetDBQuery to execute a database query to find the relevant and precise information.
  - Use only the identifiers found and filter according to the relevant time period.
  - Never guess! If unsure on which identifier to use, run DatasetFullTextSearch prior to the query.
  - Always use aggregate functions to summarize the data when relevant.
  - Always include the field `item_url` in the query, use its value to provide the user with a direct link to the data, like so [item's display name](<item_url>).
  - Always try to present the data in a table, and if that's not applicable - in a structured and organized manner.
  - Always - In case the server returns a warning in the response: Read and understand carefully the warning, and always re-run the query with the necessary fixed. Never present the user a result based on a query that returned a warning.
  - Always offer the user to download the data, using the `download_url` field in the response. Make sure to format this as a markdown link!
5. Once you're certain you got the exact answer, present the response in an organized and professional manner with a verbal description of the query performed and links to download the data.
6. Always suggest follow-up questions that might interest the user or clarify what was not taken into account in the current response.
"""

mcp = FastMCP(
    name="BudgetKey",
    instructions=MCP_INSTRUCTIONS,
)


@mcp.tool()
def DatasetInfo(dataset: str) -> dict:
    """
    Get information regarding a specific dataset, including its columns and db schema.

    Args:
        dataset: id of the dataset to get information for. Available datasets:
                 - budget_items_data: Budget book data
                 - support_programs_data: Support programs
                 - supports_transactions_data: Individual support payments
                 - contracts_data: Government procurement contracts
                 - entities_data: Organizations and entities
                 - income_items_data: State revenues
                 - budgetary_change_requests_data: Budget change requests
                 - budgetary_change_transactions_data: Budget change transactions

    Returns:
        Dataset information including columns and schema
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
    Full text search on a specific dataset to locate relevant items through free-text search.
    Use this tool to find relevant textual identifiers (but never time frames).

    Args:
        dataset: id of the dataset to search. Available datasets:
                 - budget_items_data: Budget book data
                 - support_programs_data: Support programs
                 - supports_transactions_data: Individual support payments
                 - contracts_data: Government procurement contracts
                 - entities_data: Organizations and entities
                 - income_items_data: State revenues
                 - budgetary_change_requests_data: Budget change requests
                 - budgetary_change_transactions_data: Budget change transactions
        q: Free text search query

    Returns:
        Search results matching the query
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
    Perform SQL query on a specific dataset's database to obtain comprehensive and complete information.
    Always use DatasetInfo first to understand the dataset schema before using this tool.

    Args:
        dataset: id of the dataset to query. Available datasets:
                 - budget_items_data: Budget book data
                 - support_programs_data: Support programs
                 - supports_transactions_data: Individual support payments
                 - contracts_data: Government procurement contracts
                 - entities_data: Organizations and entities
                 - income_items_data: State revenues
                 - budgetary_change_requests_data: Budget change requests
                 - budgetary_change_transactions_data: Budget change transactions
        query: PostgreSQL compatible SQL query to execute, based on the dataset's database schema.
               Example: "SELECT * FROM budget_items_data WHERE year = 2025"
               Always include the field `item_url` in the query to provide direct links to the data.
               Always use aggregate functions to summarize the data when relevant.
        page_size: Number of rows to return (default: 50)

    Returns:
        Query results including data rows and download_url for full results
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


# Create HTTP endpoints for each tool
@mcp.custom_route('/endpoints/DatasetInfo', methods=['POST'])
async def endpoint_dataset_info(request):
    try:
        json_body = await request.json()
        dataset = json_body.get('dataset')
        if not dataset:
            return Response('{"error": "dataset parameter is required"}', status_code=400)
        result = DatasetInfo(dataset)
        return Response(requests.compat.json.dumps(result, ensure_ascii=False))
    except Exception as e:
        log.error(f"Error in DatasetInfo endpoint: {e}")
        return Response(f'{{"error": "{str(e)}"}}', status_code=500)


@mcp.custom_route('/endpoints/DatasetFullTextSearch', methods=['POST'])
async def endpoint_dataset_search(request):
    try:
        json_body = await request.json()
        dataset = json_body.get('dataset')
        q = json_body.get('q')
        if not dataset or not q:
            return Response('{"error": "dataset and q parameters are required"}', status_code=400)
        result = DatasetFullTextSearch(dataset, q)
        return Response(requests.compat.json.dumps(result, ensure_ascii=False))
    except Exception as e:
        log.error(f"Error in DatasetFullTextSearch endpoint: {e}")
        return Response(f'{{"error": "{str(e)}"}}', status_code=500)


@mcp.custom_route('/endpoints/DatasetDBQuery', methods=['POST'])
async def endpoint_dataset_query(request):
    try:
        json_body = await request.json()
        dataset = json_body.get('dataset')
        query = json_body.get('query')
        page_size = json_body.get('page_size', 50)
        if not dataset or not query:
            return Response('{"error": "dataset and query parameters are required"}', status_code=400)
        result = DatasetDBQuery(dataset, query, page_size)
        return Response(requests.compat.json.dumps(result, ensure_ascii=False))
    except Exception as e:
        log.error(f"Error in DatasetDBQuery endpoint: {e}")
        return Response(f'{{"error": "{str(e)}"}}', status_code=500)


@mcp.custom_route('/health', methods=['GET'])
async def health_check(request):
    """Health check endpoint for Kubernetes probes"""
    return Response('{"status": "healthy"}', media_type="application/json")


if __name__ == "__main__":
    mcp.run(transport='streamable-http', path='/mcp', host="0.0.0.0", port=8000)

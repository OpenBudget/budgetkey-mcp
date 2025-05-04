"""OpenBudget MCP server implementation."""
from typing import Dict, Any
import httpx
from fastmcp import FastMCP, Context

from config import API_BASE_URL, AVAILABLE_DATASETS, DEFAULT_PAGE_SIZE

server = FastMCP("OpenBudget", dependencies=["httpx", "typing"])
http_client = httpx.AsyncClient()

async def _make_request(path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a request to the API."""
    url = f"{API_BASE_URL}{path}"
    try:
        response = await http_client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise ValueError(f"API request failed: {str(e)}")

@server.tool("get_dataset_info")
async def get_dataset_info(dataset: str, ctx: Context) -> Dict:
    """Get information about a dataset's structure."""
    ctx.info(f"Starting to get dataset info for {dataset}")
    if dataset not in AVAILABLE_DATASETS:
        raise ValueError(f"Invalid dataset. Must be one of: {', '.join(AVAILABLE_DATASETS)}")
    
    path = f"/api/tables/{dataset}/info"
    result = await _make_request(path)
    ctx.info(f"Successfully retrieved info for dataset {dataset}")
    return result

@server.tool("search_dataset")
async def search_dataset(dataset: str, search_query: str, ctx: Context) -> Dict:
    """Search within a dataset."""
    ctx.info(f"Starting search in dataset {dataset} with query: {search_query}")
    if dataset not in AVAILABLE_DATASETS:
        raise ValueError(f"Invalid dataset. Must be one of: {', '.join(AVAILABLE_DATASETS)}")
    
    path = f"/api/tables/{dataset}/search"
    params = {"q": search_query}
    result = await _make_request(path, params)
    ctx.info(f"Successfully completed search in dataset {dataset}")
    return result

@server.tool("query_dataset")
async def query_dataset(dataset: str, sql_query: str, ctx: Context) -> Dict:
    """Execute a SQL query on a dataset."""
    ctx.info(f"Starting SQL query execution on dataset {dataset}")
    if dataset not in AVAILABLE_DATASETS:
        raise ValueError(f"Invalid dataset. Must be one of: {', '.join(AVAILABLE_DATASETS)}")
    
    path = f"/api/tables/{dataset}/query"
    params = {
        "query": sql_query,
        "page_size": DEFAULT_PAGE_SIZE
    }
    result = await _make_request(path, params)
    ctx.info(f"Successfully executed SQL query on dataset {dataset}")
    return result

@server.resource("resource://available_datasets")
def get_available_datasets():
    """Get the list of available datasets."""
    return AVAILABLE_DATASETS

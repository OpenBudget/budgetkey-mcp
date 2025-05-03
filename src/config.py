"""Configuration settings for the OpenBudget MCP server."""

API_BASE_URL = "https://next.obudget.org"
DEFAULT_PAGE_SIZE = 30

AVAILABLE_DATASETS = [
    "budget_items_data",
    "income_items_data",
    "supports_data",
    "contracts_data", 
    "entities_data",
    "budgetary_change_requests_data",
    "budgetary_change_transactions_data"
]

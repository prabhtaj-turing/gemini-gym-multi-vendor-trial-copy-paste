from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/JqlApi.py
from .SimulationEngine.db import DB
from typing import Dict, Any

@tool_spec(
    spec={
        'name': 'get_jql_autocomplete_suggestions',
        'description': """ Retrieve JQL (Jira Query Language) autocomplete data for query assistance.
        
        This method returns autocomplete suggestions that help users construct valid JQL queries.
        The data includes available field names and operators that can be used in JQL expressions
        for searching and filtering issues in Jira. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_jql_autocomplete_data() -> Dict[str, Any]:
    """
    Retrieve JQL (Jira Query Language) autocomplete data for query assistance.

    This method returns autocomplete suggestions that help users construct valid JQL queries.
    The data includes available field names and operators that can be used in JQL expressions
    for searching and filtering issues in Jira.

    Returns:
        Dict[str, Any]: A dictionary containing autocomplete suggestions:
            - fields (List[str]): Available field names that can be used in JQL queries
            - operators (List[str]): Valid JQL operators for field comparisons
        If the database has no jql_autocomplete_data, it will return an empty dictionary.
    """
    return DB.get("jql_autocomplete_data", {})

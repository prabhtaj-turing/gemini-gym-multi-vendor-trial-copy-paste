from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, List

from google_search.SimulationEngine import utils, custom_errors


@tool_spec(
    spec={
        'name': 'search_queries',
        'description': """ Search Google for information from the internet.
        
        This function performs web searches using Google Search. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'queries': {
                    'type': 'array',
                    'description': 'One or multiple queries to Google Search.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'queries'
            ]
        }
    }
)
def get(queries: List[str]) -> List[Dict[str, Any]]:
    """Search Google for information from the internet.
    
    This function performs web searches using Google Search.
    
    Args:
        queries (List[str]): One or multiple queries to Google Search.
    
    Returns:
        List[Dict[str, Any]]: A list of search results, where each result contains:
            - query (str): The search query that was executed
            - result (str): search result for the query
    
    Raises:
        ValidationError: If input arguments fail validation.
    """
    # Input validation
    if not isinstance(queries, list) or len(queries) == 0:
        raise custom_errors.ValidationError("Queries must be a non-empty list of strings.")
    for i, q in enumerate(queries):
        if not isinstance(q, str) or not q.strip():
            raise custom_errors.ValidationError(f"Query at index {i} must be a non-empty string.")
    search_queries = [q.strip() for q in queries]

    results = []

    for search_query in search_queries:
        search_result = utils.get_gemini_response(search_query)
        result = {
            "query": search_query,
            "result": search_result
        }
        utils.add_recent_search(result)
        results.append(result)

    return results

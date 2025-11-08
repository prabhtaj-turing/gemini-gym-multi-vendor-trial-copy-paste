import json
import os
import re
import uuid
from typing import Optional, Dict, Any, List

import requests
from dotenv import load_dotenv, find_dotenv
from common_utils.print_log import print_log

from .db import DB

load_dotenv(find_dotenv(filename=".env", raise_error_if_not_found=False, usecwd=False))

Global_result = None


def get_gemini_response(query_text: str):
    """
    Constructs and executes an HTTP request to query the Gemini API using the 'requests' library.

    Args:
        query_text: The user's text to send to the model.

    Returns:
        A dictionary parsed from the JSON response, or None on error.

    Raises:
        EnvironmentError: If the environment variables GOOGLE_API_KEY or GEMINI_API_KEY or LIVE_API_URL are not set.
    """
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Google API Key not found. Please create a .env file in the project root with GOOGLE_API_KEY or GEMINI_API_KEY, or set it as an environment variable.")
    
    live_api_url = os.getenv("LIVE_API_URL")
    if not live_api_url:
        raise EnvironmentError("Live API URL not found. Please create a .env file in the project root with LIVE_API_URL, or set it as an environment variable.")
    
    if live_api_url.endswith("key="):
        url = f"{live_api_url}{api_key}"
    elif live_api_url.endswith("?"):
        url = f"{live_api_url}key={api_key}"
    else:
        url = f"{live_api_url}?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "models/chat-bard-003",
        "generationConfig": {"candidateCount": 1},
        "contents": [{"role": "user", "parts": {"text": query_text}}]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # This will raise an exception for HTTP error codes
        return response.json()

    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"An error occurred with the HTTP request: {e}")
        return None

def extract_youtube_results(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts the results from the response.
    Args:
        response: The response from the Gemini API.

    Returns:
        A dictionary containing the results or None if the response is not a dictionary or if the results are not found in the response.

    """
    if response is None:
        return None
    if not isinstance(response, dict):
        return None
    try:
        results = json.loads(response['candidates'][0]['content']['parts'][2]['structuredData']['multiStepPlanInfo']['multiStepPlan']['steps'][2]['blocks'][0]['codeOutputState']['executionTrace']['executions'][0]['jsonOutput'])
        return results
    except (json.JSONDecodeError, KeyError) as e:
        return None


def find_and_print_executions(data_node):
    """
    Recursively traverses a data structure (dicts, lists) to find and print
    the 'executions' list within any 'executionTrace' dictionary.
    """
    global Global_result
    # If the current node is a dictionary, check for the target and recurse on values
    if isinstance(data_node, dict):
        # Check if the key 'executionTrace' exists and its value is a dictionary
        if 'executionTrace' in data_node and isinstance(data_node.get('executionTrace'), dict):
            # Check if 'executions' is in the 'executionTrace' dictionary
            if 'executions' in data_node['executionTrace']:
                for execution in data_node['executionTrace']['executions']:
                    Global_result = json.dumps(execution, indent=2)

        # Continue searching deeper in the dictionary's values
        for key in data_node:
            find_and_print_executions(data_node[key])

    # If the current node is a list, recurse on each item
    elif isinstance(data_node, list):
        for item in data_node:
            find_and_print_executions(item)

    # If the current node is a string, it might contain embedded JSON
    elif isinstance(data_node, str):
        try:
            # Attempt to parse the string as JSON and search within it
            inner_data = json.loads(data_node)
            find_and_print_executions(inner_data)
        except (json.JSONDecodeError, TypeError):
            # The string is not valid JSON, so we stop here for this branch
            pass


def get_json_response(gemini_output: str):
    global Global_result 
    Global_result = ""
    find_and_print_executions(gemini_output)
    try:
        json_output = json.loads(Global_result).get('jsonOutput','[]')
        return json.loads(json_output)
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        print(f"An error occurred with the JSON response: {e}")
        return None


def get_recent_searches(endpoint: str="search", max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve a list of recent searches for a given endpoint.

    Args:
        endpoint (str): The API endpoint for which to retrieve recent searches.
        max_results (int, optional): Maximum number of recent searches to return. Defaults to 5.

    Returns:
        List[Dict[str, Any]]: A list of recent search entries, each containing 'parameters' and 'result' keys.
    """
    results = DB.get("recent_searches", {}).get(endpoint, [])
    max_results = min(max_results, len(results))
    return results[:max_results]

def add_recent_search(endpoint:str, parameters: Dict[str, Any], result: List[Dict[str, Any]]) -> None:
    """
    Add a recent search entry for a specific API endpoint.

    Args:
        endpoint (str): The API endpoint for which to add the recent search.
        parameters (Dict[str, Any]): The parameters used in the search.
        result (List[Dict[str, Any]]): The result returned from the search.

    Returns:
        None
    """
    try:
        recent_searches = DB.get("recent_searches", {})

        endpoint_searches = recent_searches.get(endpoint, [])

        search_dict = {
            "parameters": parameters,
            "result": result
        }

        endpoint_searches.insert(0, search_dict)

        recent_searches[endpoint] = endpoint_searches[:50]

        DB["recent_searches"] = recent_searches
    
    except Exception as e:
        print_log(f"Error adding recent search: {e}")

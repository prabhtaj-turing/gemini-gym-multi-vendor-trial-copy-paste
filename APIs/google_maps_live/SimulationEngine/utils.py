# google_maps_live/SimulationEngine/utils.py
import math
from typing import Dict, Any, TypeVar, Type
import requests
import json
import os
import re
import time
from typing import Optional, List, Dict, Any, Union
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from common_utils.print_log import print_log
from google_maps_live.SimulationEngine.db import DB
from google_maps_live.SimulationEngine.custom_errors import (
    ParseError, 
    UserLocationError, 
    UndefinedLocationError
)
from google_maps_live.SimulationEngine.models import (
    TravelMode, 
    UserLocation
)

# Load environment variables from .env file
load_dotenv()

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)


def get_gemini_response(query: str):
    """
    Sends a query to the Gemini API using the 'requests' library and returns the main text response.

    Args:
        query (str): The user's text to send to the Gemini model.

    Returns:
        str: The main text content returned by the Gemini API.

    Raises:
        EnvironmentError: If the GOOGLE_API_KEY environment variable is not set.
        RuntimeError: If there is an HTTP error or if the response cannot be parsed as JSON.
    """

    # Construct the query text to send to the model.
    query_text = f"Use @Google Maps to search exactly this query, do not alter it: '{query}'"
    
    # Get API key from environment variable
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
    
    print_log(f"Sending request to Gemini API at {url}")

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "model": "models/chat-bard-003",
        "generationConfig": {"candidateCount": 1},
        "contents": [{"role": "user", "parts": {"text": query_text}}]
    }

    print_log("Sending request to Gemini API...")
    
    try:
        # Execute the POST request
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # This will raise an exception for HTTP error codes

        # The output is parsed from the JSON response
        gemini_output =  response.json()
        main_text = gemini_output['candidates'][0]['content']['parts'][0]['text']
                
        return main_text

    except requests.exceptions.RequestException as e:
        raise e
    
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Failed to parse JSON from the response")


def parse_json_from_gemini_response(gemini_response: str) -> Any:
    """
    Extracts and parses the first valid JSON object or array from a Gemini response string.
    Raises ParseError if parsing fails.
    """
    start_obj = gemini_response.find('{')
    start_arr = gemini_response.find('[')

    # Find the first JSON structure (object or array)
    if start_obj == -1 and start_arr == -1:
        raise ParseError("No JSON object or array found in Gemini response.")
    
    if start_obj == -1 or (start_arr != -1 and start_arr < start_obj):
        # Array comes first
        start = start_arr
        end = gemini_response.rfind(']')
    else:
        # Object comes first
        start = start_obj
        end = gemini_response.rfind('}')

    if start == -1 or end == -1 or end < start:
        raise ParseError("Malformed JSON in Gemini response.")
    response_text = gemini_response[start:end+1]

    try:
        json_response = json.loads(response_text)
        return json_response
    
    except Exception as e:
        raise ParseError(f"Error decoding JSON from Gemini response: {e}")


def get_location_from_env(variable_name: str) -> str:
    """
    Retrieves the value of a user location from environment variables.

    Args:
        variable_name (str): The name or value of the UserLocation enum (e.g., "MY_HOME", "MY_LOCATION", "MY_WORK").

    Returns:
        str: The value of the corresponding environment variable.

    Raises:
        UserLocationError: If the provided variable_name is not a valid UserLocation name or value.
        UndefinedLocationError: If the corresponding environment variable is not set or is empty.
    """
    if (variable_name not in  UserLocation.names()) or (variable_name not in UserLocation.values()):
        raise UserLocationError(f"Invalid location variable: '{variable_name}'. Must be one of {', '.join([e.name for e in UserLocation])}")

    # The name of the enum member (e.g., "MY_LOCATION") is used as the key
    # for the environment variable.
    value = os.getenv(variable_name)

    if value is None or value == "":
        raise UndefinedLocationError(f"Environment variable for '{variable_name}' is not defined.")

    return value


def get_model_from_gemini_response(
    query: str, 
    model_class: Type[T], 
    max_retries: int = 3,
    retry_delay: int = 1
) -> T:
    """
    Sends a query to the Gemini API and retries until the response passes Pydantic model validation.
    
    This function implements retry logic to handle cases where the Gemini API returns
    malformed JSON or JSON that doesn't match the expected Pydantic model schema.
    
    Args:
        query (str): The query to send to the Gemini API
        model_class (Type[T]): The Pydantic model class to validate against
        max_retries (int): Maximum number of retry attempts (default: 3)
        
    Returns:
        T: An instance of the validated Pydantic model
    
    Raises:
        Exception: The last error encountered after all retry attempts are exhausted
    """
    
    gemini_response = None
    
    for attempt in range(max_retries + 1):
        try:
            # Get response from Gemini API 
            gemini_response = get_gemini_response(query)
            
            # Parse JSON from response
            json_response = parse_json_from_gemini_response(gemini_response)
            
            # Validate against Pydantic model
            validated_model = model_class(**json_response)
            
            return validated_model
            
        except Exception as e:
            print_log(f"Error validating model: {e}")
            time.sleep(retry_delay)
    
    # If we get here, all retries failed - raise the last error
    raise NotImplementedError(gemini_response)


def get_recent_searches(endpoint: str, max_results: int = 5) -> List[Union[Dict[str, Any], List[Dict[str, Any]]]]:
    """
    Retrieve a list of recent searches for a given endpoint.

    Args:
        endpoint (str): The API endpoint for which to retrieve recent searches.
            Possible values include:
                - "find_directions": For direction search history
                - "navigate": For navigation search history
                - "query_places": For place search history
                - "show_on_map": For map display history
                - "lookup_place_details": For place details history
                - "analyze_places": For place analysis history
        max_results (int, optional): Maximum number of recent searches to return. Defaults to 5.

    Returns:
        List[Dict[str, Any]]: A list of recent search entries, each containing 'parameters' and 'result' keys.
    """
    return DB.get("recent_searches", {}).get(endpoint, [])[:max_results]


def add_recent_search(endpoint:str, parameters: Dict[str, Any], result: Dict[str, Any]) -> None:
    """
    Add a recent search entry for a specific API endpoint.

    Args:
        endpoint (str): The API endpoint for which to add the recent search.
        parameters (Dict[str, Any]): The parameters used in the search.
        result (Dict[str, Any]): The result returned from the search.

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

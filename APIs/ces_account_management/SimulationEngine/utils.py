"""
Utility functions for the Account Management Service.
"""

import base64
import json
from datetime import datetime, timedelta, timezone
import google.auth.transport.requests as google_auth_transport_requests
from google.oauth2 import service_account
import requests
from typing import Dict, List, Optional, Any

from .custom_errors import ActionNotSupportedError, ParseError
from .phone_utils import normalize_phone_number
from common_utils.print_log import print_log
from common_utils.ces_infobot_config import CESInfobotConfigManager
from pydantic import BaseModel
from typing import TypeVar, Type
import time

from .db import DB

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)

Request = google_auth_transport_requests.Request

# Create service-specific config manager
_config_manager = CESInfobotConfigManager(
    service_name="ces_account_management",
    default_tool_resources={
        "account_orders": "46f527f8-0509-4e28-9563-db5666e0790b",
        "plans_features": "c90c11bb-6868-4631-8bf0-7f8b5fe4b92c"
    }
)


def _get_token() -> str:
    """Returns the access token for the service account."""
    config = _config_manager.get_config()
    
    if not config.service_account_info:
        raise ValueError(
            "Service account info must be set before uploading the image."
        )
    info = json.loads(base64.b64decode(config.service_account_info).decode("utf-8"))
    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=config.scopes
    )

    session = requests.Session()
    session.verify = config.ca_bundle

    credentials.refresh(Request(session=session))
    return credentials.token


def _query_infobot(query: str, tool_name: str) -> dict[str, Any]:
    """Queries Infobot service through the `executeTool` API."""
    config = _config_manager.get_config()
    
    tool_resource_id = config.tool_resources.get(tool_name)
    if not tool_resource_id:
        raise ValueError(f"Tool resource '{tool_name}' not configured")
    
    tool_resource = config.parent_resource + "/tools/" + tool_resource_id
    
    response = requests.post(
        f"{config.full_api_endpoint}:executeTool",
        headers={
            "Authorization": f"Bearer {_get_token()}",
            "Content-Type": "application/json",
        },
        data=json.dumps({"args": {"query": query}, "tool": tool_resource}),
        verify=config.ca_bundle,
    )
    response.raise_for_status()
    return response.json()["response"]


def query_plans_and_features_infobot(query: str) -> dict[str, Any]:
    """Queries Infobot service through the `executeTool` API."""
    return _query_infobot(query, "plans_features")


def query_account_orders_infobot(query: str) -> dict[str, Any]:
    """Queries Infobot service through the `executeTool` API."""
    return _query_infobot(query, "account_orders")


def get_account(account_id: str) -> Optional[Dict[str, Any]]:
    """Get account by account ID or phone number.

    Args:
        account_id (str): The unique account ID to search for.

    Returns:
        Optional[Dict[str, Any]]: The account data if found, None otherwise.
    """
    # First try to get account by ID
    all_accounts = DB.get("accountDetails", {})
    account_details = all_accounts.get(account_id)

    # If not found by ID, try to search by phone number
    if account_details is None:
        phone_number = normalize_phone_number(account_id)
        if phone_number is not None:
            account_details = search_accounts_by_phone(phone_number)

    if account_details is None:
        return None

    account_details_copy = account_details.copy()
    if "orders" in account_details_copy:
        del account_details_copy["orders"]

    return account_details_copy


def get_device(device_id: str) -> Optional[Dict[str, Any]]:
    """Get device by device ID.

    Args:
        device_id (str): The unique device ID to search for.

    Returns:
        Optional[Dict[str, Any]]: The device data if found, None otherwise.
    """
    all_accounts = DB.get("accountDetails", {})
    for account in all_accounts.values():
        devices = account.get("devices", [])
        for device in devices:
            if device.get("deviceId") == device_id:
                return device
    return None


def get_service_plan(plan_id: str) -> Optional[Dict[str, Any]]:
    """Get service plan by plan ID.

    Args:
        plan_id (str): The unique plan ID to search for.

    Returns:
        Optional[Dict[str, Any]]: The service plan data if found, None otherwise.
    """
    plans = DB.get("availablePlans", {}).get("plans", {})
    return plans.get(plan_id)


def create_account(account_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new account.

    Args:
        account_data (Dict[str, Any]): The account data to create.

    Returns:
        Dict[str, Any]: The created account data.
    """
    account_id = account_data.get("accountId")
    if not account_id:
        raise ValueError("Account ID is required")

    if "accountDetails" not in DB:
        DB["accountDetails"] = {}
    DB["accountDetails"][account_id] = account_data
    return account_data


def update_account(account_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing account.

    Args:
        account_id (str): The account ID to update.
        update_data (Dict[str, Any]): The data to update.

    Returns:
        Dict[str, Any]: The updated account data.
    """
    all_accounts = DB.get("accountDetails", {})
    if account_id not in all_accounts:
        raise ValueError(f"Account {account_id} not found")

    # Handle nested dictionary updates
    for k, v in update_data.items():
        if v is not None:
            if isinstance(v, dict):
                if k not in all_accounts[account_id]:
                    all_accounts[account_id][k] = {}
                for k1, v1 in v.items():
                    if v1 is not None:
                        all_accounts[account_id][k][k1] = v1
            else:
                all_accounts[account_id][k] = v

    return all_accounts[account_id]


def add_device_to_account(
    account_id: str, device_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Add a device to an account.

    Args:
        account_id (str): The account ID to add the device to.
        device_data (Dict[str, Any]): The device data to add.

    Returns:
        Dict[str, Any]: The added device data.
    """
    all_accounts = DB.get("accountDetails", {})
    if account_id not in all_accounts:
        raise ValueError(f"Account {account_id} not found")

    device_id = device_data.get("deviceId")
    if not device_id:
        raise ValueError("Device ID is required")

    # Add device to account's devices list
    if "devices" not in all_accounts[account_id]:
        all_accounts[account_id]["devices"] = []

    # Replace if device with same id exists, else append
    replaced = False
    for idx, existing in enumerate(all_accounts[account_id]["devices"]):
        if existing.get("deviceId") == device_id:
            all_accounts[account_id]["devices"][idx] = device_data
            replaced = True
            break
    if not replaced:
        all_accounts[account_id]["devices"].append(device_data)
    return device_data


def add_service_to_account(
    account_id: str, service_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Add a service plan to an account.

    Args:
        account_id (str): The account ID to add the service to.
        service_data (Dict[str, Any]): The service data to add.

    Returns:
        Dict[str, Any]: The added service data.
    """
    all_accounts = DB.get("accountDetails", {})
    if account_id not in all_accounts:
        raise ValueError(f"Account {account_id} not found")

    service_id = service_data.get("serviceId")
    if not service_id:
        raise ValueError("Service ID is required")

    # Add service to account's services list
    if "services" not in all_accounts[account_id]:
        all_accounts[account_id]["services"] = []

    all_accounts[account_id]["services"].append(service_data)
    return service_data


def search_accounts_by_phone(phone_number: str) -> Optional[Dict[str, Any]]:
    """Search for an account by phone number.

    Args:
        phone_number (str): The phone number to search for.

    Returns:
        Optional[Dict[str, Any]]: The account data if found, None otherwise.
    """
    all_accounts = DB.get("accountDetails", {})
    normalized_phone_number = normalize_phone_number(phone_number)
    for account in all_accounts.values():
        contact_phone = account.get("contactPhone")
        contact_phone = normalize_phone_number(contact_phone)
        if contact_phone is None:
            continue
        if contact_phone == normalized_phone_number:
            return account
    return None


def search_accounts_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Search for an account by email address.

    Args:
        email (str): The email address to search for.

    Returns:
        Optional[Dict[str, Any]]: The account data if found, None otherwise.
    """
    all_accounts = DB.get("accountDetails", {})
    for account in all_accounts.values():
        if account.get("contactEmail") == email:
            return account
    return None


def update_service_plan(
    account_id: str, service_index: int, service_data: Dict[str, Any]
) -> None:
    """Update a specific service plan on an account.

    Args:
        account_id (str): The account ID to update.
        service_index (int): The index of the service to update.
        service_data (Dict[str, Any]): The updated service data.
    """
    all_accounts = DB.get("accountDetails", {})
    if account_id not in all_accounts:
        raise ValueError(f"Account {account_id} not found")

    all_accounts[account_id]["services"][service_index] = service_data


def _generate_order_id(action: str) -> str:
    """
    Generate an order ID by combining the action prefix with a unique counter.

    Args:
        action (str): The action type (e.g., "CHANGE_PLAN", "ADD_FEATURE", "REMOVE_FEATURE")

    Returns:
        str: Order ID in format "ORD_{action_prefix}_{order_id_counter}"
    """
    # Get the part before the first underscore
    action_prefix = action.split("_")[0]

    order_id_counter = DB.get("order_id_counter", 100000) + 1

    DB["order_id_counter"] = order_id_counter

    return f"ORD_{action_prefix}_{order_id_counter}"


def create_order(account_id: str, action: str, message: str) -> None:
    """Insert order information into the database.

    Args:
        account_id (str): The account ID associated with the order.
        action (str): The action taken (e.g., "CHANGE_PLAN").
        message (str): The message associated with the order.
    """
    order_id = _generate_order_id(action)
    createdAt = datetime.now(timezone.utc)
    if action == "CHANGE_PLAN":
        effective_date = (createdAt + timedelta(days=7)).strftime("%Y-%m-%d")
    elif action == "ADD_FEATURE":
        effective_date = (createdAt + timedelta(days=0)).strftime("%Y-%m-%d")
    elif action == "REMOVE_FEATURE":
        effective_date = (createdAt + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        raise ActionNotSupportedError(f"Action {action} not supported.")

    order_info = {
        "orderId": order_id,
        "accountId": account_id,
        "orderType": action,
        "orderDate": createdAt.strftime("%Y-%m-%d"),
        "estimatedCompletionDate": effective_date,
        "status": "Processing",
        "statusDescription": message,
    }

    if "orders" not in DB["accountDetails"].get(account_id, {}):
        DB["accountDetails"][account_id]["orders"] = {}

    DB["accountDetails"][account_id]["orders"][order_id] = order_info

    return order_info


def get_all_available_plans_and_features() -> List[Dict[str, Any]]:
    """Get all available plans and features directly from the database.

    Returns:
        List[Dict[str, Any]]: List of all available plans and features with plan_id added.
    """
    available_plans = DB.get("availablePlans", {})
    current_plans = available_plans.get("plans", {})

    all_plans = []
    for _, plan_data in current_plans.items():
        all_plans.append(plan_data)

    return all_plans


def _get_gemini_response(query: str) -> str:
    """
    Sends a query to the Gemini API using the Google GenAI library and returns the main text response.

    Args:
        query (str): The user's text to send to the Gemini model.

    Returns:
        str: The main text content returned by the Gemini API.

    Raises:
        EnvironmentError: If the GOOGLE_API_KEY environment variable is not set.
        RuntimeError: If there is an error with the API call.
    """
    import os
    from google import genai
    from google.genai import types

    # Get API key from environment variable
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Google API Key not found. Please create a .env file in the project root with GOOGLE_API_KEY or GEMINI_API_KEY, or set it as an environment variable."
        )

    # Initialize the client
    client = genai.Client(api_key=api_key)

    print_log("Sending request to Gemini 2.5 Pro with temperature 0...")

    try:
        # Generate content
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=types.Part.from_text(text=query),
            config=types.GenerateContentConfig(
                temperature=0  # Deterministic results
            ),
        )

        if response.text:
            return response.text
        else:
            raise RuntimeError("No text content in Gemini response")

    except Exception as e:
        raise RuntimeError(f"Error calling Gemini API: {e}")


def _parse_json_from_gemini_response(gemini_response: str) -> Any:
    """
    Extracts and parses the first valid JSON object or array from a Gemini response string.
    Handles both plain JSON and markdown-wrapped JSON responses.
    Raises ParseError if parsing fails.
    """

    # First, try to handle markdown-wrapped JSON (```json ... ```)
    if "```json" in gemini_response:
        start_marker = gemini_response.find("```json")
        if start_marker != -1:
            start_marker += 7  # Length of '```json'
            end_marker = gemini_response.find("```", start_marker)
            if end_marker != -1:
                json_text = gemini_response[start_marker:end_marker].strip()
                try:
                    return json.loads(json_text)
                except Exception as e:
                    raise ParseError(
                        f"Error decoding markdown-wrapped JSON from Gemini response: {e}"
                    )

    # Also try to handle generic code blocks (``` ... ```)
    if "```" in gemini_response:
        start_marker = gemini_response.find("```")
        if start_marker != -1:
            start_marker += 3  # Length of '```'
            end_marker = gemini_response.find("```", start_marker)
            if end_marker != -1:
                json_text = gemini_response[start_marker:end_marker].strip()
                try:
                    return json.loads(json_text)
                except Exception:
                    pass  # Continue to regular JSON parsing

    # Fall back to regular JSON parsing
    start_obj = gemini_response.find("{")
    start_arr = gemini_response.find("[")

    # Find the first JSON structure (object or array)
    if start_obj == -1 and start_arr == -1:
        raise ParseError("No JSON object or array found in Gemini response.")

    if start_obj == -1 or (start_arr != -1 and start_arr < start_obj):
        # Array comes first
        start = start_arr
        end = gemini_response.rfind("]")
    else:
        # Object comes first
        start = start_obj
        end = gemini_response.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ParseError("Malformed JSON in Gemini response.")
    response_text = gemini_response[start : end + 1]

    try:
        json_response = json.loads(response_text)
        return json_response

    except Exception as e:
        raise ParseError(f"Error decoding JSON from Gemini response: {e}")


def get_model_from_gemini_response(
    query: str, model_class: Type[T], max_retries: int = 3, retry_delay: int = 1
) -> T:
    """
    Sends a query to the Gemini API and retries until the response passes Pydantic model validation.

    This function implements retry logic to handle cases where the Gemini API returns
    malformed JSON or JSON that doesn't match the expected Pydantic model schema.

    Args:
        query (str): The query to send to the Gemini API
        model_class (Type[T]): The Pydantic model class to validate against
        max_retries (int): Maximum number of retry attempts (default: 3)
        retry_delay (int): Delay between retries in seconds (default: 1)

    Returns:
        T: An instance of the validated Pydantic model

    Raises:
        Exception: The last error encountered after all retry attempts are exhausted
    """

    gemini_response = None

    for attempt in range(max_retries + 1):
        try:
            # Get response from Gemini API
            gemini_response = _get_gemini_response(query)

            # Parse JSON from response
            json_response = _parse_json_from_gemini_response(gemini_response)

            # Validate against Pydantic model
            validated_model = model_class(**json_response)

            return validated_model

        except Exception as e:
            print_log(
                f"Error validating model (attempt {attempt + 1}/{max_retries + 1}): {e}"
            )
            if attempt < max_retries:
                time.sleep(retry_delay)

    # If we get here, all retries failed - raise the last error
    raise NotImplementedError(
        f"Failed to get valid response after {max_retries + 1} attempts. Last response: {gemini_response}"
    )


def search_plans_by_query(query: str) -> List[Dict[str, Any]]:
    """Search for plans and features matching a query string using Gemini API for deterministic results.

    This function uses the Gemini API to intelligently search through available plans and features
    based on the user's query, providing more accurate and contextually relevant results than
    traditional keyword matching.

    Args:
        query (str): The search query to match against plan names, descriptions, and features.

    Returns:
        List[Dict[str, Any]]: List of matching plans and features ordered by relevance.

    Raises:
        ValueError: If query is empty or not a string
        ParseError: If JSON parsing from API response fails
        NotImplementedError: If API response cannot be parsed as valid JSON
        ValidationError: If response data doesn't match expected schema
    """
    # Input validation
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string")

    try:
        from .models import PlanSearchResult
        import json

        # Get all available plans and features to provide context to Gemini
        all_plans = get_all_available_plans_and_features()

        # Create a focused query for plan and feature search
        search_query = f"""
        Find the most relevant service plans and features for this customer query: "{query}"
        
        Available Plans and Features:
        {json.dumps(all_plans, indent=2)}
        
        Matching Rules:
        1. Exact name matches (highest priority)
        2. Semantic understanding: device type, cost level, data amount, features, family/shared usage
        3. Price filtering: "under $X" = cost < X, "greater than $X" = cost > X, "affordable" = lower cost
        4. Data filtering: "X GB" = data >= X, "unlimited" = unlimited data, "data only" = data-focused plans
        5. Feature matching: "add-ons" = FEATURE_ADDON types, "international" = international features
        
        Result Limits:
        - For comprehensive/general queries (asking for all plans, complete lists, what's available, or browsing): Return ALL available plans and features
        - For specific/filtered queries (asking for particular types, features, or criteria): Return maximum 5 most relevant results
        - For exact name matches: Return the specific plan/feature even if it's the only result
        
        Return ONLY a valid JSON array of plan objects following this exact schema for each plan:
        {json.dumps(PlanSearchResult.model_json_schema(), indent=2)}
        
        Requirements:
        - JSON array only, no markdown or explanations
        - Include all required fields: id, name, description, type, monthlyCost, dataAllowance, termsAndConditionsUrl, compatibilityNotes
        - Use empty strings for missing text, 0 for missing numbers, null for missing optional fields
        - Order results by relevance: exact matches first, then semantic matches
        - Be deterministic and consistent
        """

        print_log(f"Searching plans/features with Gemini for query: {query}")

        # Get the raw JSON response from Gemini
        gemini_response = _get_gemini_response(search_query)

        # Parse the JSON array response
        json_response = _parse_json_from_gemini_response(gemini_response)

        # Validate that it's a list
        if not isinstance(json_response, list):
            raise ValueError("Expected JSON array response from Gemini")

        # Convert each plan to PlanSearchResult and then to dictionary
        result_plans = []
        for plan_data in json_response:
            try:
                plan = PlanSearchResult(**plan_data)
                plan_dict = {
                    "id": plan.id or "",
                    "name": plan.name or "",
                    "description": plan.description or "",
                    "type": plan.type or "",
                    "monthlyCost": plan.monthlyCost or 0.0,
                    "dataAllowance": plan.dataAllowance or "",
                    "termsAndConditionsUrl": plan.termsAndConditionsUrl or "",
                    "compatibilityNotes": plan.compatibilityNotes or "",
                }
                result_plans.append(plan_dict)
            except Exception as e:
                print_log(
                    f"Error validating plan data: {e}, skipping plan: {plan_data}"
                )
                continue

        print_log(
            f"Found {len(result_plans)} matching plans/features for query: {query}"
        )
        return result_plans

    except Exception as e:
        print_log(f"Error in search_plans_by_query_v2: {e}")
        raise


def search_account_orders_by_query(query: str, account_id: str) -> List[Dict[str, Any]]:
    """Search for account orders matching a query string using embedding-based search.

    Args:
        query (str): The search query to match against order details.
        account_id (str): The account ID to filter orders by.
    """
    from .search_engine import search_engine_manager

    # Get the search engine
    engine = search_engine_manager.get_engine()

    # Ensure the search engine is initialized with current database data
    search_engine_manager.service_adapter.init_from_db(strategy=engine)

    # Build filter for order content
    search_filter = {"content_type": "order", "account_id": account_id}

    # Perform the search with filtering for order content
    search_results = engine.search(query, filter=search_filter)

    # Extract the original order data from search results
    matching_orders = []
    for result in search_results:
        matching_orders.append(result)

    return matching_orders


def get_end_of_conversation_status() -> str:
    """Get the end of conversation status.

    Returns:
        str: The end of conversation status.
    """
    return DB.get("_end_of_conversation_status", {})


# Public configuration API functions
def get_infobot_config():
    """Get current Infobot configuration
    
    Returns:
        CESInfobotConfig: Current configuration object
    """
    return _config_manager.get_config()


def update_infobot_config(**kwargs):
    """Update Infobot configuration
    
    Args:
        **kwargs: Configuration key-value pairs to update
        
    Examples:
        update_infobot_config(gcp_project="my-project")
        update_infobot_config(service_account_info="base64_encoded_account")
        update_infobot_config(
            gcp_project="my-project",
            tool_resources={
                "account_orders": "custom-tool-id-1",
                "plans_features": "custom-tool-id-2"
            }
        )
    """
    _config_manager.update_config(**kwargs)


def save_infobot_config(filepath: str = None):
    """Save Infobot configuration to file
    
    Args:
        filepath: Optional path to save config. Defaults to ces_account_management_infobot_config.json
    """
    _config_manager.save_config(filepath)


def load_infobot_config(filepath: str):
    """Load Infobot configuration from file
    
    Args:
        filepath: Path to configuration file
    """
    _config_manager.load_config(filepath)


def reset_infobot_config():
    """Reset Infobot configuration to defaults"""
    _config_manager.reset_to_defaults()


def show_infobot_config():
    """Display current Infobot configuration"""
    _config_manager.show_config()


def set_infobot_mode(use_real: bool):
    """Set real/simulation mode for Infobot queries
    
    Args:
        use_real: True to use real Infobot, False for simulation
    """
    # Import here to avoid circular imports
    if "use_real_datastore" not in DB:
        DB["use_real_datastore"] = False
    DB["use_real_datastore"] = use_real
    mode = "real" if use_real else "simulated"
    print(f"Infobot mode set to: {mode}")

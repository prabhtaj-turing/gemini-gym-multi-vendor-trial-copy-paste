# ces/SimulationEngine/utils.py
import base64
import json
from typing import Any, Dict, List
from google import genai
from google.genai import types
import google.auth.transport.requests as google_auth_transport_requests
from google.oauth2 import service_account
import requests
from .db import DB
from common_utils.ces_infobot_config import CESInfobotConfigManager
from dotenv import load_dotenv

Request = google_auth_transport_requests.Request

load_dotenv()

# Create service-specific config manager
_config_manager = CESInfobotConfigManager(
    service_name="ces_system_activation",
    default_tool_resources={
        "activation_guides": "46f527f8-0509-4e28-9563-db5666e0790b",
        "order_details": "c90c11bb-6868-4631-8bf0-7f8b5fe4b92c"
    }
)


def _get_token() -> str:
  """Returns the access token for the service account."""
  config = _config_manager.get_config()
  
  if not config.service_account_info:
    raise ValueError(
        'Service account info must be set before uploading the image.'
    )
  info = json.loads(
      base64.b64decode(config.service_account_info).decode('utf-8')
  )
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
  
  tool_resource = config.parent_resource + '/tools/' + tool_resource_id
  
  response = requests.post(
      f'{config.full_api_endpoint}:executeTool',
      headers={
          'Authorization': f'Bearer {_get_token()}',
          'Content-Type': 'application/json',
      },
      data=json.dumps({'args': {'query': query}, 'tool': tool_resource}),
      verify=config.ca_bundle,
  )
  response.raise_for_status()
  return response.json()['response']


def query_activation_guides_infobot(query: str) -> dict[str, Any]:
  """Queries Infobot service through the `executeTool` API."""
  return _query_infobot(query, "activation_guides")


def query_order_details_infobot(query: str) -> dict[str, Any]:
  """Queries Infobot service through the `executeTool` API."""
  return _query_infobot(query, "order_details")

def search_order_details_by_query(query: str, order_id: str = "", account_id: str = "") -> List[Dict[str, any]]:
    """Search for order details matching a query string using embedding-based search.
    
    Args:
        query (str): The search query to match against order details.
        order_id (str): The order ID to filter orders by.
        account_id (str): The account ID to filter orders by.
    """
   
    from .search_engine import search_engine_manager

    engine = search_engine_manager.get_engine()

    search_engine_manager.service_adapter.init_from_db(strategy=engine)

    search_filter = {
        "content_type": "order",
    }

    if order_id:
        search_filter["order_id"] = order_id
    if account_id:
        search_filter["account_id"] = account_id

    search_results = engine.search(query, filter=search_filter)

    if len(search_results) == 0:

        if order_id:
            search_filter = {
                "content_type": "order",
            }
            search_filter["order_id"] = order_id
            search_results = engine.search(query, filter=search_filter)

        if (len(search_results) == 0 or len(search_results) > 1) and account_id:
            search_filter = {
                "content_type": "order",
            }
            search_filter["account_id"] = account_id
            search_results = engine.search(query, filter=search_filter)

    matching_orders = []
    
    for result in search_results:
        matching_orders.append(result)

    return matching_orders

def search_activation_guides_by_llm(query: str) -> Dict[str, Any]:
    client = genai.Client()
    prompt = f"Based on the user's query, provide a concise answer using the information from the following activation guide. If the query is general, summarize the guide's introduction and steps. Check the solution section under troubleshooting\n\nQuery: {query}\n\nActivation Guide:\n{json.dumps(DB['activationGuides'], indent=2)}"
    
    response = client.models.generate_content(
        model="gemini-2.5-pro", 
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=f"Just return the answer, no markdown formatting without any other interaction with the user. Make it straight forward and concise. Return with the structure: {{'answer': 'The answer to the query', 'snippets': {{'introduction': 'The introduction of the guide', 'title': 'The title of the guide', 'uri': 'The URI of the guide in the provided Activation Guides data following the format: activationGuides/DOCUMENT_TITLE'}}}} if you are not able to find the information, return an empty object: {{}}",
            response_mime_type= "application/json",
        )
    )

    return json.loads(response.text)


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
                "activation_guides": "custom-tool-id-1",
                "order_details": "custom-tool-id-2"
            }
        )
    """
    _config_manager.update_config(**kwargs)


def save_infobot_config(filepath: str = None):
    """Save Infobot configuration to file
    
    Args:
        filepath: Optional path to save config. Defaults to ces_system_activation_infobot_config.json
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


def get_conversation_end_status(function_name: str = None):
    """Function that will return the end of conversation status functions status"""
    data = DB.get("_end_of_conversation_status")
    if function_name:
        data = data.get(function_name)
    return data
    
from common_utils.tool_spec_decorator import tool_spec
# APIs/tiktokApi/Business/Publish/Status/__init__.py
import uuid
import re
from typing import Dict, Union, List
from tiktok.SimulationEngine.db import DB


@tool_spec(
    spec={
        'name': 'get_business_publish_status',
        'description': """ Get the publishing status of a TikTok video or photo post.
        
        This endpoint allows you to check the current status of a post publishing task,
        including whether it has completed successfully or is still in progress. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'access_token': {
                    'type': 'string',
                    'description': 'Access token authorized by TikTok creators.'
                },
                'business_id': {
                    'type': 'string',
                    'description': 'Application specific unique identifier for the TikTok account.'
                },
                'publish_id': {
                    'type': 'string',
                    'description': 'Unique identifier for a post publishing task.'
                }
            },
            'required': [
                'access_token',
                'business_id',
                'publish_id'
            ]
        }
    }
)
def get(access_token: str, business_id: str, publish_id: str) -> Dict[str, Union[int, str, Dict[str, Union[str, List[str]]]]]:
    """
    Get the publishing status of a TikTok video or photo post.

    This endpoint allows you to check the current status of a post publishing task,
    including whether it has completed successfully or is still in progress.

    Args:
        access_token (str): Access token authorized by TikTok creators.
        business_id (str): Application specific unique identifier for the TikTok account.
        publish_id (str): Unique identifier for a post publishing task.

    Returns:
        Dict[str, Union[int, str, Dict[str, Union[str, List[str]]]]]: A dictionary containing:
            - code (int): HTTP status code (200 for success, 400 for bad request, 404 for not found)
            - message (str): Status message describing the result
            - request_id (str): Unique identifier for the request
            - data (Dict[str, Union[str, List[str]]]): Publishing status information containing:
                - status (str): Current status of the publishing task (e.g., "PUBLISH_COMPLETE", "PUBLISH_PENDING", "PUBLISH_FAILED")
                - post_ids (List[str]): List of IDs for the published posts

    Raises:
        ValueError: If any of the input parameters are invalid or missing.

    """
    # Type validation
    if not isinstance(access_token, str):
        raise ValueError("access_token must be a string")
    if not isinstance(business_id, str):
        raise ValueError("business_id must be a string")
    if not isinstance(publish_id, str):
        raise ValueError("publish_id must be a string")
    
    # Value validation
    if not access_token.strip():
        raise ValueError("Access-Token is required")
    if not business_id.strip():
        raise ValueError("business_id is required")
    if not publish_id.strip():
        raise ValueError("publish_id is required")
    
    # Validate business_id format (should be a valid identifier)
    if not re.match(r'^[a-zA-Z0-9_-]+$', business_id):
        raise ValueError("Invalid business_id format")
    
    # Validate publish_id format (should be a valid UUID or similar identifier)
    if not re.match(r'^[a-zA-Z0-9_-]+$', publish_id):
        raise ValueError("Invalid publish_id format")

    # Check if business account exists (business accounts are under "business_accounts" key)
    if business_id not in DB:
        raise ValueError("Business account not found")

    # Look up publish status in DB
    publish_statuses = DB.get("publish_status", {})
    if publish_id not in publish_statuses:
        raise ValueError("Publish task not found")
    
    publish_status = publish_statuses[publish_id]
    
    return {
        "code": 200,
        "message": "OK",
        "request_id": str(uuid.uuid4()),
        "data": {
            "status": publish_status.get("status", "PUBLISH_PENDING"),
            "post_ids": publish_status.get("post_ids", []),
        },
    }

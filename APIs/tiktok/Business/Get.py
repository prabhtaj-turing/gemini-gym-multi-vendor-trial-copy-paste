from common_utils.tool_spec_decorator import tool_spec
# APIs/tiktokApi/Business/Get/__init__.py

from typing import Dict, Optional, List, Union
from tiktok.SimulationEngine.db import DB
import datetime


@tool_spec(
    spec={
        'name': 'get_business_profile_data',
        'description': 'Get profile data of a TikTok account, including analytics and insights.',
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
                'start_date': {
                    'type': 'string',
                    'description': 'Query start date in YYYY-MM-DD format. Defaults to None.'
                },
                'end_date': {
                    'type': 'string',
                    'description': 'Query end date in YYYY-MM-DD format. Defaults to None.'
                },
                'fields': {
                    'type': 'array',
                    'description': """ List of requested fields to include in the response. Defaults to None.
                    - username
                    - display_name
                    - profile
                    - analytics
                    - settings """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'access_token',
                'business_id'
            ]
        }
    }
)
def get(
    access_token: str,
    business_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[List[str]] = None,
) -> Dict[str, Union[int, str, Dict[str, Union[str, Dict[str, Union[str, int, float, bool]]]]]]:
    """
    Get profile data of a TikTok account, including analytics and insights.

    Args:
        access_token (str): Access token authorized by TikTok creators.
        business_id (str): Application specific unique identifier for the TikTok account.
        start_date (Optional[str]): Query start date in YYYY-MM-DD format. Defaults to None.
        end_date (Optional[str]): Query end date in YYYY-MM-DD format. Defaults to None.
        fields (Optional[List[str]]): List of requested fields to include in the response. Defaults to None.
            - username
            - display_name
            - profile
            - analytics
            - settings

    Returns:
        Dict[str, Union[int, str, Dict[str, Union[str, Dict[str, Union[str, int, float, bool]]]]]]: A dictionary containing:
            - code (int): HTTP status code (200 for success, 400 for bad request, 404 for not found)
            - message (str): Status message describing the result
            - data (Dict[str, Union[str, Dict[str, Union[str, int, float, bool]]]]): The requested profile data, filtered by fields if specified
                - username (str): The username of the TikTok account
                - display_name (str): The display name of the TikTok account
                - profile (Dict[str, Union[str, int]]): The profile data of the TikTok account
                    - bio (str): The bio of the TikTok account
                    - followers_count (int): The number of followers of the TikTok account
                    - following_count (int): The number of following of the TikTok account
                    - website (str): The website of the TikTok account
                - analytics (Dict[str, Union[int, float]]): The analytics data of the TikTok account
                    - total_likes (int): The total number of likes of the TikTok account
                    - total_views (int): The total number of views of the TikTok account
                    - engagement_rate (float): The engagement rate of the TikTok account
                - settings (Dict[str, Union[bool, str]]): The settings of the TikTok account
                    - notifications_enabled (bool): Whether the notifications are enabled for the TikTok account
                    - ads_enabled (bool): Whether the ads are enabled for the TikTok account
                    - language (str): The language of the TikTok account

    Raises:
        TypeError: If access_token or business_id is not a string, or if fields is not a list, or if elements in fields contains non-string values.
        ValueError: If access_token or business_id is not provided or is empty, if date format in start_date or end_date is invalid, 
                   if start_date is after end_date, if fields contains invalid field names, or if account is not found.
    """
    # Valid fields that can be requested
    valid_fields = {"username", "display_name", "profile", "analytics", "settings"}

    # Input validation
    if not access_token:
        raise ValueError("Access-Token is required")
    if not isinstance(access_token, str):
        raise TypeError("access_token must be a string")   
    if not access_token.strip():
        raise ValueError("Access-Token must be a non-empty string")

    if not business_id:
        raise ValueError("business_id is required")
    if not isinstance(business_id, str):
        raise TypeError("business_id must be a string")
    if not business_id.strip():
        raise ValueError("business_id must be a non-empty string")

    # Validate fields parameter
    if fields is not None:
        if not isinstance(fields, list):
            raise TypeError("fields must be a list")

        # Check if all fields are strings and valid
        for field in fields:
            if not isinstance(field, str):
                raise TypeError("All fields must be strings")
            if field not in valid_fields:
                raise ValueError(f"Invalid field '{field}'. Valid fields are: analytics, settings, username, profile, display_name")

    # Parse and validate date parameters
    parsed_start_date = None
    parsed_end_date = None

    if start_date:
        if not isinstance(start_date, str):
            raise TypeError("start_date must be a string")
        try:
            parsed_start_date = datetime.datetime.strptime(
                start_date, "%Y-%m-%d"
            ).date()
        except ValueError:
            raise ValueError("Invalid start_date format. Use YYYY-MM-DD")

    if end_date:
        if not isinstance(end_date, str):
            raise TypeError("end_date must be a string")
        try:
            parsed_end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid end_date format. Use YYYY-MM-DD")

    # Validate date range
    if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
        raise ValueError("start_date cannot be after end_date")

    # Simulate data retrieval based on business_id
    account_data = DB.get(business_id)
    if not account_data:
        raise ValueError("Account not found")

    filtered_data = account_data.copy()  # Create a copy to avoid modifying the original

    # Apply fields filtering if fields are provided
    if fields is not None:
        filtered_data = {
            field: filtered_data.get(field)
            for field in fields
            if field in filtered_data
        }

    return {"code": 200, "message": "OK", "data": filtered_data}

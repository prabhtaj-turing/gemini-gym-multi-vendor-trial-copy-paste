from common_utils.tool_spec_decorator import tool_spec
# APIs/hubspot/Campaigns.py
from typing import Optional, Dict, Union, List
import uuid
from hubspot.SimulationEngine.db import DB
import builtins
from datetime import datetime
import re


@tool_spec(
    spec={
        'name': 'get_campaigns',
        'description': 'Returns a list of marketing campaigns (Basic implementation).',
        'parameters': {
            'type': 'object',
            'properties': {
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of campaigns to return.'
                },
                'offset': {
                    'type': 'integer',
                    'description': 'The number of campaigns to skip.'
                },
                'created_at': {
                    'type': 'string',
                    'description': 'Filter campaigns by creation date.'
                },
                'created_at__gt': {
                    'type': 'string',
                    'description': 'Filter campaigns by creation date greater than a specific date.'
                },
                'created_at__gte': {
                    'type': 'string',
                    'description': 'Filter campaigns by creation date greater than or equal to a specific date.'
                },
                'created_at__lt': {
                    'type': 'string',
                    'description': 'Filter campaigns by creation date less than a specific date.'
                },
                'created_at__lte': {
                    'type': 'string',
                    'description': 'Filter campaigns by creation date less than or equal to a specific date.'
                },
                'updated_at': {
                    'type': 'string',
                    'description': 'Filter campaigns by update date.'
                },
                'updated_at__gt': {
                    'type': 'string',
                    'description': 'Filter campaigns by update date greater than a specific date.'
                },
                'updated_at__gte': {
                    'type': 'string',
                    'description': 'Filter campaigns by update date greater than or equal to a specific date.'
                },
                'updated_at__lt': {
                    'type': 'string',
                    'description': 'Filter campaigns by update date less than a specific date.'
                },
                'updated_at__lte': {
                    'type': 'string',
                    'description': 'Filter campaigns by update date less than or equal to a specific date.'
                },
                'name': {
                    'type': 'string',
                    'description': 'Filter campaigns by name.'
                },
                'name__contains': {
                    'type': 'string',
                    'description': 'Filter campaigns by name containing a specific string.'
                },
                'name__icontains': {
                    'type': 'string',
                    'description': 'Filter campaigns by name containing a specific string (case insensitive).'
                },
                'name__ne': {
                    'type': 'string',
                    'description': 'Filter campaigns by name not equal to a specific string.'
                },
                'id': {
                    'type': 'string',
                    'description': 'Filter campaigns by id.'
                },
                'id__ne': {
                    'type': 'string',
                    'description': 'Filter campaigns by id not equal to a specific string.'
                },
                'type': {
                    'type': 'string',
                    'description': 'Filter campaigns by type.'
                },
                'type__ne': {
                    'type': 'string',
                    'description': 'Filter campaigns by type not equal to a specific string.'
                }
            },
            'required': []
        }
    }
)
def get_campaigns(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    created_at: Optional[str] = None,
    created_at__gt: Optional[str] = None,
    created_at__gte: Optional[str] = None,
    created_at__lt: Optional[str] = None,
    created_at__lte: Optional[str] = None,
    updated_at: Optional[str] = None,
    updated_at__gt: Optional[str] = None,
    updated_at__gte: Optional[str] = None,
    updated_at__lt: Optional[str] = None,
    updated_at__lte: Optional[str] = None,
    name: Optional[str] = None,
    name__contains: Optional[str] = None,
    name__icontains: Optional[str] = None,
    name__ne: Optional[str] = None,
    id: Optional[str] = None,
    id__ne: Optional[str] = None,
    type: Optional[str] = None,
    type__ne: Optional[str] = None,
) -> Dict[str, Union[List[Dict[str, Union[str, int, float]]], int, Optional[int]]]:
    """
    Returns a list of marketing campaigns.

    Args:
        limit(Optional[int]): The maximum number of campaigns to return. Defaults to None.
        offset(Optional[int]): The number of campaigns to skip. Defaults to None.
        created_at(Optional[str]): Filter campaigns by creation date. Defaults to None.
        created_at__gt(Optional[str]): Filter campaigns by creation date greater than a specific date. Defaults to None.
        created_at__gte(Optional[str]): Filter campaigns by creation date greater than or equal to a specific date. Defaults to None.
        created_at__lt(Optional[str]): Filter campaigns by creation date less than a specific date. Defaults to None.
        created_at__lte(Optional[str]): Filter campaigns by creation date less than or equal to a specific date. Defaults to None.
        updated_at(Optional[str]): Filter campaigns by update date. Defaults to None.
        updated_at__gt(Optional[str]): Filter campaigns by update date greater than a specific date. Defaults to None.
        updated_at__gte(Optional[str]): Filter campaigns by update date greater than or equal to a specific date. Defaults to None.
        updated_at__lt(Optional[str]): Filter campaigns by update date less than a specific date. Defaults to None.
        updated_at__lte(Optional[str]): Filter campaigns by update date less than or equal to a specific date. Defaults to None.
        name(Optional[str]): Filter campaigns by name. Defaults to None.
        name__contains(Optional[str]): Filter campaigns by name containing a specific string. Defaults to None.
        name__icontains(Optional[str]): Filter campaigns by name containing a specific string (case insensitive). Defaults to None.
        name__ne(Optional[str]): Filter campaigns by name not equal to a specific string. Defaults to None.
        id(Optional[str]): Filter campaigns by id. Defaults to None.
        id__ne(Optional[str]): Filter campaigns by id not equal to a specific string. Defaults to None.
        type(Optional[str]): Filter campaigns by type. Defaults to None.
        type__ne(Optional[str]): Filter campaigns by type not equal to a specific string. Defaults to None.

    Returns: 
        Dict[str, Union[List[Dict[str, Union[str, int, float]]], int, Optional[int]]]: A dictionary containing the following keys:
        - results(List[Dict[str, Union[str, int, float]]]): A list of campaigns matching the filter criteria.
            - id(str): The id of the campaign.
            - name(str): The name of the campaign.
            - type(str): The type of the campaign.
            - start_date(str): The start date of the campaign.
            - end_date(str): The end date of the campaign.
            - status(str): The status of the campaign.
            - budget(float): The budget of the campaign.
            - target_audience(str): The target audience of the campaign.
            - utm_campaign(str): The utm campaign of the campaign.
            - slug(str): The slug of the campaign.
            - description(str): The description of the campaign.
            - start_year(int): The start year of the campaign.
            - start_month(int): The start month of the campaign.
            - start_day(int): The start day of the campaign.
            - end_year(int): The end year of the campaign.
            - end_month(int): The end month of the campaign.
            - end_day(int): The end day of the campaign.
            - theme(str): The theme of the campaign.
            - resource(str): The resource of the campaign.
            - color_label(str): The color label of the campaign.
            - is_archived(bool): Whether the campaign is archived.

        - total(int): The total number of campaigns matching the filter criteria.
        - limit(int): The maximum number of campaigns to return.
        - offset(int): The number of campaigns to skip.
    
    Raises:
        TypeError: If any of the arguments limit, offset, created_at, created_at__gt, created_at__gte, created_at__lt, created_at__lte, updated_at, updated_at__gt, updated_at__gte, updated_at__lt, updated_at__lte, name, name__contains, name__icontains, name__ne, id, id__ne, type, type__ne are of not correct type.
    """

    if limit is not None and not isinstance(limit, int):
        raise TypeError(f"limit must be an integer, but got {builtins.type(limit).__name__}.")
    if offset is not None and not isinstance(offset, int):
        raise TypeError(f"offset must be an integer, but got {builtins.type(offset).__name__}.")
    if created_at is not None and not isinstance(created_at, str):
        raise TypeError(f"created_at must be a string, but got {builtins.type(created_at).__name__}.")
    if created_at__gt is not None and not isinstance(created_at__gt, str):
        raise TypeError(f"created_at__gt must be a string, but got {builtins.type(created_at__gt).__name__}.")
    if created_at__gte is not None and not isinstance(created_at__gte, str):
        raise TypeError(f"created_at__gte must be a string, but got {builtins.type(created_at__gte).__name__}.")
    if created_at__lt is not None and not isinstance(created_at__lt, str):
        raise TypeError(f"created_at__lt must be a string, but got {builtins.type(created_at__lt).__name__}.")
    if created_at__lte is not None and not isinstance(created_at__lte, str):
        raise TypeError(f"created_at__lte must be a string, but got {builtins.type(created_at__lte).__name__}.")
    if updated_at is not None and not isinstance(updated_at, str):
        raise TypeError(f"updated_at must be a string, but got {builtins.type(updated_at).__name__}.")
    if updated_at__gt is not None and not isinstance(updated_at__gt, str):
        raise TypeError(f"updated_at__gt must be a string, but got {builtins.type(updated_at__gt).__name__}.")
    if updated_at__gte is not None and not isinstance(updated_at__gte, str):
        raise TypeError(f"updated_at__gte must be a string, but got {builtins.type(updated_at__gte).__name__}.")
    if updated_at__lt is not None and not isinstance(updated_at__lt, str):
        raise TypeError(f"updated_at__lt must be a string, but got {builtins.type(updated_at__lt).__name__}.")
    if updated_at__lte is not None and not isinstance(updated_at__lte, str):
        raise TypeError(f"updated_at__lte must be a string, but got {builtins.type(updated_at__lte).__name__}.")
    if name is not None and not isinstance(name, str):
        raise TypeError(f"name must be a string, but got {builtins.type(name).__name__}.")
    if name__contains is not None and not isinstance(name__contains, str):
        raise TypeError(f"name__contains must be a string, but got {builtins.type(name__contains).__name__}.")
    if name__icontains is not None and not isinstance(name__icontains, str):
        raise TypeError(f"name__icontains must be a string, but got {builtins.type(name__icontains).__name__}.")
    if name__ne is not None and not isinstance(name__ne, str):
        raise TypeError(f"name__ne must be a string, but got {builtins.type(name__ne).__name__}.")
    if id is not None and not isinstance(id, str):
        raise TypeError(f"id must be a string, but got {builtins.type(id).__name__}.")
    if id__ne is not None and not isinstance(id__ne, str):
        raise TypeError(f"id__ne must be a string, but got {builtins.type(id__ne).__name__}.")
    if type is not None and not isinstance(type, str):
        raise TypeError(f"type must be a string, but got {builtins.type(type).__name__}.")
    if type__ne is not None and not isinstance(type__ne, str):
        raise TypeError(f"type__ne must be a string, but got {builtins.type(type__ne).__name__}.")

    campaigns_list = list(DB["campaigns"].values())

    # Very basic filtering (only id, name, and type for simplicity)
    if id:
        campaigns_list = [c for c in campaigns_list if c.get("id") == id]
    if name:
        campaigns_list = [c for c in campaigns_list if c.get("name") == name]

    if type:
        campaigns_list = [c for c in campaigns_list if c.get("type") == type]
    if type__ne:
        campaigns_list = [c for c in campaigns_list if c.get("type") != type__ne]

    if id__ne:
        campaigns_list = [c for c in campaigns_list if c.get("id") != id__ne]
    if name__ne:
        campaigns_list = [c for c in campaigns_list if c.get("name") != name__ne]

    if name__contains:
        campaigns_list = [c for c in campaigns_list if name__contains in c.get("name")]
    if name__icontains:
        campaigns_list = [c for c in campaigns_list if name__icontains.lower() in c.get("name").lower()]
    

    # Very basic pagination
    total_count = len(campaigns_list)
    if offset is not None:
        campaigns_list = campaigns_list[offset:]
    if limit is not None:
        campaigns_list = campaigns_list[:limit]

    return {
        "results": campaigns_list,
        "total": total_count,
        "limit": limit,
        "offset": offset,
    }


@tool_spec(
    spec={
        'name': 'create_campaign',
        'description': 'Creates a new campaign.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of the campaign.'
                },
                'slug': {
                    'type': 'string',
                    'description': 'The slug of the campaign.'
                },
                'description': {
                    'type': 'string',
                    'description': 'The description of the campaign.'
                },
                'start_year': {
                    'type': 'integer',
                    'description': 'The start year of the campaign.'
                },
                'start_month': {
                    'type': 'integer',
                    'description': 'The start month of the campaign.'
                },
                'start_day': {
                    'type': 'integer',
                    'description': 'The start day of the campaign.'
                },
                'end_year': {
                    'type': 'integer',
                    'description': 'The end year of the campaign.'
                },
                'end_month': {
                    'type': 'integer',
                    'description': 'The end month of the campaign.'
                },
                'end_day': {
                    'type': 'integer',
                    'description': 'The end day of the campaign.'
                },
                'theme': {
                    'type': 'string',
                    'description': 'The theme of the campaign.'
                },
                'resource': {
                    'type': 'string',
                    'description': 'The resource of the campaign.'
                },
                'color_label': {
                    'type': 'string',
                    'description': 'The color label of the campaign.'
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def create_campaign(
    name: str,
    slug: Optional[str] = None,
    description: Optional[str] = None,
    start_year: Optional[int] = None,
    start_month: Optional[int] = None,
    start_day: Optional[int] = None,
    end_year: Optional[int] = None,
    end_month: Optional[int] = None,
    end_day: Optional[int] = None,
    theme: Optional[str] = None,
    resource: Optional[str] = None,
    color_label: Optional[str] = None,
) -> Dict[str, Union[str, int, bool, None]]:
    """
    Creates a new campaign.

    Args:
        name(str): The name of the campaign.
        slug(Optional[str]): The slug of the campaign. Defaults to None.
        description(Optional[str]): The description of the campaign. Defaults to None.
        start_year(Optional[int]): The start year of the campaign. Defaults to None.
        start_month(Optional[int]): The start month of the campaign. Defaults to None.
        start_day(Optional[int]): The start day of the campaign. Defaults to None.
        end_year(Optional[int]): The end year of the campaign. Defaults to None.
        end_month(Optional[int]): The end month of the campaign. Defaults to None.
        end_day(Optional[int]): The end day of the campaign. Defaults to None.
        theme(Optional[str]): The theme of the campaign. Defaults to None.
        resource(Optional[str]): The resource of the campaign. Defaults to None.
        color_label(Optional[str]): The color label of the campaign. Defaults to None.

    Returns:
        Dict[str, Union[str, int, bool, None]]: A dictionary containing the following keys:
        - id(str): The id of the campaign.
        - name(str): The name of the campaign.
        - slug(str): The slug of the campaign.
        - description(str): The description of the campaign.
        - start_year(int): The start year of the campaign.
        - start_month(int): The start month of the campaign.
        - start_day(int): The start day of the campaign.
        - end_year(int): The end year of the campaign.
        - end_month(int): The end month of the campaign.
        - end_day(int): The end day of the campaign.
        - theme(str): The theme of the campaign.
        - resource(str): The resource of the campaign.
        - color_label(str): The color label of the campaign.
        - created_at(str): The date and time the campaign was created.
        - is_archived(bool): Whether the campaign is archived. Always False in created events.

    Raises:
        TypeError: If the name, slug, description, resource, or color label is not a string 
                    or if the start year, start month, start day, end year, end month, or end day is not an integer.
        ValueError: If name is missing or empty or start_month, end_month are not between 1 and 12 
                    or start_day, end_day are not between 1 and 31 
                    or start_date is after end_date
                    or the start year and end year are less than 1900.

    """
    if not name:
        raise ValueError("Name is required")
    
    if not isinstance(name, str):
        raise TypeError("Name must be a string")

    if not name.strip():
        raise ValueError("Name cannot be empty")
    
    campaign_id = str(uuid.uuid4())

    if slug is not None and not isinstance(slug, str):
        raise TypeError("Slug must be a string")
    elif slug is None:
        slug = f"{name.lower().replace(' ', '-')}-{campaign_id}"
    
    if description is not None and not isinstance(description, str):
        raise TypeError("Description must be a string")
    
    if start_year is not None:
        if not isinstance(start_year, int):
            raise TypeError("Start year must be an integer")
        if start_year < 1900:
            raise ValueError("Start year must be greater than 1900")
        
    
    if start_month is not None:
        if not isinstance(start_month, int):
            raise TypeError("Start month must be an integer")
        if start_month < 1 or start_month > 12:
            raise ValueError("Start month must be between 1 and 12")
    
    if start_day is not None:
        if not isinstance(start_day, int):
            raise TypeError("Start day must be an integer")
        if start_day < 1 or start_day > 31:
            raise ValueError("Start day must be between 1 and 31")
    
    if end_year is not None:
        if not isinstance(end_year, int):
            raise TypeError("End year must be an integer")
        if end_year < 1900:
            raise ValueError("End year must be greater than 1900")
    
    if end_month is not None:
        if not isinstance(end_month, int):
            raise TypeError("End month must be an integer")
        if end_month < 1 or end_month > 12:
            raise ValueError("End month must be between 1 and 12")
    
    if end_day is not None:
        if not isinstance(end_day, int):
            raise TypeError("End day must be an integer")
        if end_day < 1 or end_day > 31:
            raise ValueError("End day must be between 1 and 31")

    if start_year is not None and start_month is not None and start_day is not None:
        start_date = datetime(start_year, start_month, start_day)
    else:
        start_date = None

    if end_year is not None and end_month is not None and end_day is not None:
        end_date = datetime(end_year, end_month, end_day)
    else:
        end_date = None

    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise ValueError("Start date must be before end date")

    if resource is not None and not isinstance(resource, str):
        raise TypeError("Resource must be a string")
    
    if color_label is not None and not isinstance(color_label, str):
        raise TypeError("Color label must be a string")

    if theme is not None and not isinstance(theme, str):
        raise TypeError("Theme must be a string")

    if not name.strip():
        raise ValueError("Name cannot be empty")
 
        

    new_campaign = {
        "id": campaign_id,
        "name": name,
        "slug": slug,
        "description": description,
        "start_year": start_year,
        "start_month": start_month,
        "start_day": start_day,
        "end_year": end_year,
        "end_month": end_month,
        "end_day": end_day,
        "theme": theme,
        "resource": resource,
        "color_label": color_label,
        "created_at": datetime.now().isoformat(),
        "is_archived": False,
    }

    DB["campaigns"][campaign_id] = new_campaign
    return new_campaign


@tool_spec(
    spec={
        'name': 'get_campaign_by_id',
        'description': 'Gets a single campaign by its ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'campaign_id': {
                    'type': 'string',
                    'description': 'The id of the campaign.'
                }
            },
            'required': [
                'campaign_id'
            ]
        }
    }
)
def get_campaign(campaign_id: str) -> Optional[Dict[str, Union[str, int, None]]]:
    """
    Gets a single campaign by its ID.

    Args:
        campaign_id(str): The id of the campaign.

    Returns:
        Optional[Dict[str, Union[str, int, None]]]: A dictionary containing the following keys if the campaign exists:
        - id(str): The id of the campaign.
        - name(str): The name of the campaign.
        - type(str): The type of the campaign.
        - start_date(str): The start date of the campaign.
        - end_date(str): The end date of the campaign.
        - status(str): The status of the campaign.
        - budget(float): The budget of the campaign.
        - target_audience(str): The target audience of the campaign.
        - utm_campaign(str): The utm campaign of the campaign.
        - slug(str): The slug of the campaign.
        - description(str): The description of the campaign.
        - start_year(int): The start year of the campaign.
        - start_month(int): The start month of the campaign.
        - start_day(int): The start day of the campaign.
        - end_year(int): The end year of the campaign.
        - end_month(int): The end month of the campaign.
        - end_day(int): The end day of the campaign.
        - theme(str): The theme of the campaign.
        - resource(str): The resource of the campaign.
        - color_label(str): The color label of the campaign.
        - is_archived(bool): Whether the campaign is archived.

    Raises:
        KeyError: If the campaign with the given id is not found.
        TypeError: If the campaign_id is not an integer.
    """

    if not isinstance(campaign_id, str):
        raise TypeError(f"campaign_id must be a string, but got {builtins.type(campaign_id).__name__}.")
    
    if campaign_id not in DB["campaigns"]:
        raise KeyError(f"Campaign with id {campaign_id} not found.")
    return DB["campaigns"].get(campaign_id)


@tool_spec(
    spec={
        'name': 'update_campaign',
        'description': 'Updates a campaign.',
        'parameters': {
            'type': 'object',
            'properties': {
                'campaign_id': {
                    'type': 'string',
                    'description': 'The id of the campaign. Must be a valid UUID.'
                },
                'name': {
                    'type': 'string',
                    'description': 'The name of the campaign.'
                },
                'slug': {
                    'type': 'string',
                    'description': 'The slug of the campaign.'
                },
                'description': {
                    'type': 'string',
                    'description': 'The description of the campaign.'
                },
                'start_year': {
                    'type': 'integer',
                    'description': 'The start year of the campaign.'
                },
                'start_month': {
                    'type': 'integer',
                    'description': 'The start month of the campaign.'
                },
                'start_day': {
                    'type': 'integer',
                    'description': 'The start day of the campaign.'
                },
                'end_year': {
                    'type': 'integer',
                    'description': 'The end year of the campaign.'
                },
                'end_month': {
                    'type': 'integer',
                    'description': 'The end month of the campaign.'
                },
                'end_day': {
                    'type': 'integer',
                    'description': 'The end day of the campaign.'
                },
                'theme': {
                    'type': 'string',
                    'description': 'The theme of the campaign.'
                },
                'resource': {
                    'type': 'string',
                    'description': 'The resource of the campaign.'
                },
                'color_label': {
                    'type': 'string',
                    'description': 'The color label of the campaign.'
                }
            },
            'required': [
                'campaign_id'
            ]
        }
    }
)
def update_campaign(
    campaign_id: str,
    name: Optional[str] = None,
    slug: Optional[str] = None,
    description: Optional[str] = None,
    start_year: Optional[int] = None,
    start_month: Optional[int] = None,
    start_day: Optional[int] = None,
    end_year: Optional[int] = None,
    end_month: Optional[int] = None,
    end_day: Optional[int] = None,
    theme: Optional[str] = None,
    resource: Optional[str] = None,
    color_label: Optional[str] = None,
) -> Optional[Dict[str, Union[str, int, None]]]:
    """
    Updates a campaign.

    Args:
        campaign_id(str): The id of the campaign. Must be a valid UUID.
        name(Optional[str]): The name of the campaign. Defaults to None.
        slug(Optional[str]): The slug of the campaign. Defaults to None.
        description(Optional[str]): The description of the campaign. Defaults to None.
        start_year(Optional[int]): The start year of the campaign. Defaults to None.
        start_month(Optional[int]): The start month of the campaign. Defaults to None.
        start_day(Optional[int]): The start day of the campaign. Defaults to None.
        end_year(Optional[int]): The end year of the campaign. Defaults to None.
        end_month(Optional[int]): The end month of the campaign. Defaults to None.
        end_day(Optional[int]): The end day of the campaign. Defaults to None.
        theme(Optional[str]): The theme of the campaign. Defaults to None.
        resource(Optional[str]): The resource of the campaign. Defaults to None.
        color_label(Optional[str]): The color label of the campaign. Defaults to None.

    Returns:
        Optional[Dict[str, Union[str, int, None]]]: A dictionary containing the following keys if the campaign exists:
        - id(str): The id of the campaign.
        - name(str): The name of the campaign.
        - slug(str): The slug of the campaign.
        - description(str): The description of the campaign.
        - start_year(int): The start year of the campaign.
        - start_month(int): The start month of the campaign.
        - start_day(int): The start day of the campaign.
        - end_year(int): The end year of the campaign.
        - end_month(int): The end month of the campaign.
        - end_day(int): The end day of the campaign.
        - theme(str): The theme of the campaign.
        - resource(str): The resource of the campaign.
        - color_label(str): The color label of the campaign.
        - created_at(str): The date and time the campaign was created.
        - updated_at(str): The date and time the campaign was updated.

    Raises:
        ValueError: If the campaign ID is not found or is None or is not a valid UUID.
                    If the start date is after the end date.
                    If the start_month or start_day is not between 1 and 12 or 1 and 31 respectively.
                    If the end_month or end_day is not between 1 and 12 or 1 and 31 respectively.
        TypeError:  If the campaign ID is not a string.
                    If the name, slug, description, theme, resource, or color label is not a string.
                    If the start_year, start_month, or start_day is not an integer.
                    If the end_year, end_month, or end_day is not an integer.

    """
    if campaign_id is None:
        raise ValueError("Campaign ID is required")
        
    if not isinstance(campaign_id, str):
        raise TypeError("Campaign ID must be a string")
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not bool(re.match(uuid_pattern, campaign_id.lower())):
        raise ValueError("Campaign ID must be a valid UUID")

    if campaign_id not in DB["campaigns"]:
        raise ValueError("Campaign not found")

    campaign = DB["campaigns"].get(campaign_id)
    if name is not None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        campaign["name"] = name
    if slug is not None:
        if not isinstance(slug, str):
            raise TypeError("Slug must be a string")
        campaign["slug"] = slug
    if description is not None:
        if not isinstance(description, str):
            raise TypeError("Description must be a string")
        campaign["description"] = description
    if start_year is not None:
        if not isinstance(start_year, int):
            raise TypeError("Start year must be an integer")
        campaign["start_year"] = start_year
    if start_month is not None:
        if not isinstance(start_month, int):
            raise TypeError("Start month must be an integer")
        if start_month < 1 or start_month > 12:
            raise ValueError("Start month must be between 1 and 12")
        campaign["start_month"] = start_month
    if start_day is not None:
        if not isinstance(start_day, int):
            raise TypeError("Start day must be an integer")      
        if start_day < 1 or start_day > 31:
            raise ValueError("Start day must be between 1 and 31")
        campaign["start_day"] = start_day
    if end_year is not None:
        if not isinstance(end_year, int):
            raise TypeError("End year must be an integer")
        campaign["end_year"] = end_year
    if end_month is not None:
        if not isinstance(end_month, int):
            raise TypeError("End month must be an integer")
        if end_month < 1 or end_month > 12:
            raise ValueError("End month must be between 1 and 12")
        campaign["end_month"] = end_month
    if end_day is not None:
        if not isinstance(end_day, int):
            raise TypeError("End day must be an integer")
        if end_day < 1 or end_day > 31:
            raise ValueError("End day must be between 1 and 31")
        campaign["end_day"] = end_day
    if campaign["start_year"] is not None and campaign["start_month"] is not None and campaign["start_day"] is not None:
        start_date = datetime(campaign["start_year"], campaign["start_month"], campaign["start_day"])
        if campaign["end_year"] is not None and campaign["end_month"] is not None and campaign["end_day"] is not None:
            end_date = datetime(campaign["end_year"], campaign["end_month"], campaign["end_day"])
            if start_date > end_date:
                raise ValueError("Start date must be before end date")
    if theme is not None:
        if not isinstance(theme, str):
            raise TypeError("Theme must be a string")
        campaign["theme"] = theme
    if resource is not None:
        if not isinstance(resource, str):
            raise TypeError("Resource must be a string")
        campaign["resource"] = resource
    if color_label is not None:
        if not isinstance(color_label, str):
            raise TypeError("Color label must be a string")
        campaign["color_label"] = color_label
    campaign["updated_at"] = datetime.now().isoformat()
    DB["campaigns"][campaign_id] = campaign
    return campaign


@tool_spec(
    spec={
        'name': 'archive_campaign',
        'description': "Archives a campaign.",
        'parameters': {
            'type': 'object',
            'properties': {
                'campaign_id': {
                    'type': 'string',
                    'description': 'The id of the campaign. Must be a valid UUID.'
                }
            },
            'required': [
                'campaign_id'
            ]
        }
    }
)
def archive_campaign(campaign_id: str) -> bool:
    """
    Archives a campaign.
    
    Args:
        campaign_id(str): The id of the campaign. Must be a valid UUID.

    Returns:
        bool: True if the campaign was archived successfully, False otherwise.

    Raises:
        TypeError: If the campaign ID is not a string.
        ValueError: If the campaign ID is None.
                    If the campaign ID is not a valid UUID.
                    If campaign_id is not found in the database.
    """
    if campaign_id is None:
        raise ValueError("Campaign ID is required")
    if not isinstance(campaign_id, str):
        raise TypeError("Campaign ID must be a string")
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not bool(re.match(uuid_pattern, campaign_id.lower())):
        raise ValueError("Campaign ID must be a valid UUID")
    if campaign_id not in DB["campaigns"]:
        raise ValueError("Campaign not found")
    
    if campaign_id in DB["campaigns"]:
        DB["campaigns"][campaign_id]["is_archived"] = True
        return True
    return False

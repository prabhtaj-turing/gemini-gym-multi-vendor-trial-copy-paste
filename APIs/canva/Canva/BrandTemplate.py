from common_utils.tool_spec_decorator import tool_spec
# canva/Canva/BrandTemplate.py
from typing import Optional, Dict, Any, List, Union
import sys
import os

sys.path.append("APIs")

from canva.SimulationEngine.db import DB


@tool_spec(
    spec={
        'name': 'get_brand_template',
        'description': 'Retrieve a brand template by its ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'brand_template_id': {
                    'type': 'string',
                    'description': 'The ID of the brand template.'
                }
            },
            'required': [
                'brand_template_id'
            ]
        }
    }
)
def get_brand_template(brand_template_id: str) -> Optional[Dict[str, Union[str, int, Dict]]]:
    """
    Retrieve a brand template by its ID.

    Args:
        brand_template_id (str): The ID of the brand template.

    Returns:
        Optional[Dict[str, Union[str, int, Dict]]]: A dictionary with the key 'brand_template' containing:
            - id (str): The brand template ID.
            - title (str): The brand template title, as shown in the Canva UI.
            - view_url (str): URL to view the brand template.
            - create_url (str): URL to create a design from the template.
            - created_at (int): Unix timestamp when the template was created.
            - updated_at (int): Unix timestamp when the template was last updated.
            - thumbnail (Optional[Dict[str, Union[str, int]]]):
                - width (int): Width of the thumbnail in pixels.
                - height (int): Height of the thumbnail in pixels.
                - url (str): URL to retrieve the thumbnail (expires in 15 minutes).
            Returns None if the brand template is not found.
    """
    brand_templates = DB.get("brand_templates", {})
    template = brand_templates.get(brand_template_id)

    if not template:
        return None

    return {
        "brand_template": {
            "id": template["id"],
            "title": template["title"],
            "view_url": template["view_url"],
            "create_url": template["create_url"],
            "thumbnail": template["thumbnail"],
            "created_at": template["created_at"],
            "updated_at": template["updated_at"],
        }
    }


@tool_spec(
    spec={
        'name': 'get_brand_template_dataset',
        'description': """ Gets the dataset definition of a brand template. If the brand template contains autofill data fields,
        
        this returns an object with the data field names and the type of data they accept. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'brand_template_id': {
                    'type': 'string',
                    'description': 'The brand template ID.'
                }
            },
            'required': [
                'brand_template_id'
            ]
        }
    }
)
def get_brand_template_dataset(
    brand_template_id: str,
) -> Optional[Dict[str, Union[str, Dict]]]:
    """
    Gets the dataset definition of a brand template. If the brand template contains autofill data fields,
    this returns an object with the data field names and the type of data they accept.

    Args:
        brand_template_id (str): The brand template ID.
        
    Returns:
        Optional[Dict[str, Union[str, Dict]]]: A dictionary containing:
            - dataset (Dict): Dataset definition with named data fields, where each field is a dictionary containing:
                - type (str): The type of data the field accepts ('image', 'text', or 'chart').
            Returns None if the brand template is not found or has no dataset.
    """
    brand_templates = DB.get("brand_templates", {})
    template = brand_templates.get(brand_template_id)

    if not template:
        return None

    datasets = template.get("datasets", {})

    if not datasets:
        return None

    return {"dataset": datasets}


@tool_spec(
    spec={
        'name': 'list_brand_templates',
        'description': 'List brand templates with optional filters and sorting.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Search term to filter brand templates by title.'
                },
                'continuation': {
                    'type': 'string',
                    'description': 'Token for pagination (currently unused).'
                },
                'ownership': {
                    'type': 'string',
                    'description': "Ownership filter ('any', 'owned', 'shared')."
                },
                'sort_by': {
                    'type': 'string',
                    'description': "Sort order ('relevance', 'modified_descending', etc.)."
                },
                'dataset': {
                    'type': 'string',
                    'description': "Filter based on dataset presence ('any', 'non_empty', 'empty')."
                }
            },
            'required': []
        }
    }
)
def list_brand_templates(
    query: Optional[str] = None,
    continuation: Optional[str] = None,
    ownership: Optional[str] = "any",
    sort_by: Optional[str] = "relevance",
    dataset: Optional[str] = "any",
) -> Dict[str, Union[str, List]]:
    """
    List brand templates with optional filters and sorting.

    Args:
        query (Optional[str]): Search term to filter brand templates by title.
        continuation (Optional[str]): Token for pagination (currently unused).
        ownership (Optional[str]): Ownership filter ('any', 'owned', 'shared').
        sort_by (Optional[str]): Sort order ('relevance', 'modified_descending', etc.).
        dataset (Optional[str]): Filter based on dataset presence ('any', 'non_empty', 'empty').

    Returns:
        Dict[str, Union[str, List]]: A dictionary containing:
            - continuation (str or None): Token for the next page of results.
            - items (List[Dict]): Each item includes:
                - id (str): Brand template ID.
                - title (str): Title of the template.
                - view_url (str): URL to view the template.
                - create_url (str): URL to create a design from the template.
                - thumbnail (Dict):
                    - width (int): Thumbnail width in pixels.
                    - height (int): Thumbnail height in pixels.
                    - url (str): URL to the thumbnail image.
                - created_at (int): Creation timestamp (Unix time).
                - updated_at (int): Last updated timestamp (Unix time).
    """
    brand_templates = list(DB.get("brand_templates", {}).values())

    if query:
        brand_templates = [
            t for t in brand_templates if query.lower() in t["title"].lower()
        ]

    if dataset == "non_empty":
        brand_templates = [
            t for t in brand_templates if "datasets" in t and t["datasets"]
        ]
    elif dataset == "empty":
        brand_templates = [t for t in brand_templates if not t.get("datasets")]

    # Sorting options
    if sort_by == "modified_descending":
        brand_templates.sort(key=lambda x: x["updated_at"], reverse=True)
    elif sort_by == "modified_ascending":
        brand_templates.sort(key=lambda x: x["updated_at"], reverse=False)
    elif sort_by == "title_descending":
        brand_templates.sort(key=lambda x: x["title"], reverse=True)
    elif sort_by == "title_ascending":
        brand_templates.sort(key=lambda x: x["title"], reverse=False)

    continuation_token = None  # Simulated continuation token logic

    return {
        "continuation": continuation_token,
        "items": [
            {
                "id": t["id"],
                "title": t["title"],
                "view_url": t["view_url"],
                "create_url": t["create_url"],
                "thumbnail": t["thumbnail"],
                "created_at": t["created_at"],
                "updated_at": t["updated_at"],
            }
            for t in brand_templates
        ],
    }

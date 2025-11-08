from common_utils.tool_spec_decorator import tool_spec
# canva/Canva/Asset.py
import time
from typing import Optional, Dict, Any, List, Union
import sys
import os

sys.path.append("APIs")

from canva.SimulationEngine.db import DB


@tool_spec(
    spec={
        'name': 'create_asset_upload_job',
        'description': 'Creates an asset upload job and returns its initial status.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of the asset being uploaded.'
                },
                'tags': {
                    'type': 'array',
                    'description': 'Tags associated with the asset (max 50).',
                    'items': {
                        'type': 'string'
                    }
                },
                'thumbnail_url': {
                    'type': 'string',
                    'description': 'URL to the thumbnail image representing the asset.'
                }
            },
            'required': [
                'name',
                'tags',
                'thumbnail_url'
            ]
        }
    }
)
def create_asset_upload_job(name: str, tags: List[str], thumbnail_url: str) -> str:
    """
    Creates an asset upload job and returns its initial status.

    Args:
        name (str): The name of the asset being uploaded.
        tags (List[str]): Tags associated with the asset (max 50).
        thumbnail_url (str): URL to the thumbnail image representing the asset.

    Returns:
        str: The unique ID of the created upload job.

    Notes:
        This function simulates job creation and metadata. Binary upload and real processing should be
        handled via the /v1/asset-uploads endpoint using a separate POST request with proper headers.
    """
    # job_id = str(uuid.uuid4())
    # DB.setdefault("autofill_jobs", {})[job_id] = {
    #     "id": job_id,
    #     "name": name,
    #     "tags": tags,
    #     "thumbnail": {
    #         "url": thumbnail_url
    #     },
    #     "status": "pending",
    #     "created_at": int(time.time()),
    # }
    # return job_id
    pass


@tool_spec(
    spec={
        'name': 'get_asset_upload_job',
        'description': 'Retrieves the status and result of an asset upload job.',
        'parameters': {
            'type': 'object',
            'properties': {
                'job_id': {
                    'type': 'string',
                    'description': 'The ID of the asset upload job.'
                }
            },
            'required': [
                'job_id'
            ]
        }
    }
)
def get_asset_upload_job(job_id: str) -> Optional[Dict[str, Union[str, Dict]]]:
    """
    Retrieves the status and result of an asset upload job.

    Args:
        job_id (str): The ID of the asset upload job.

    Returns:
        Optional[Dict[str, Union[str, Dict]]]: A dictionary with the key 'job' containing:
            - id (str): ID of the asset upload job.
            - status (str): Status of the upload job. One of:
                - "in_progress"
                - "success"
                - "failed"
            - asset (Optional[Dict[str, Union[str, List[str], int, Dict[str, Union[str, int]]]], None]): Present only if status is "success". Contains:
                - id (str): Asset ID.
                - name (str): Name of the uploaded asset.
                - type (str): Type of the asset (e.g., "image", "video").
                - tags (List[str]): User-facing tags.
                - created_at (int): Unix timestamp when asset was created.
                - updated_at (int): Unix timestamp when asset was last updated.
                - thumbnail (Optional[Dict[str, Union[str, int]]]):
                    - width (int): Width in pixels.
                    - height (int): Height in pixels.
                    - url (str): Temporary URL to the thumbnail (expires in 15 minutes).
            - error (Optional[Dict[str, str]]): Present only if status is "failed". Contains:
                - code (str): One of "file_too_big", "import_failed".
                - message (str): Human-readable explanation of the failure.
    """
    return DB.get("asset_upload_jobs", {}).get(job_id, {})


@tool_spec(
    spec={
        'name': 'get_asset',
        'description': 'Retrieves metadata for a specific asset by its ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'asset_id': {
                    'type': 'string',
                    'description': 'The ID of the asset to retrieve.'
                }
            },
            'required': [
                'asset_id'
            ]
        }
    }
)
def get_asset(asset_id: str) -> Optional[Dict[str, Union[str, Dict]]]:
    """
    Retrieves metadata for a specific asset by its ID.

    Args:
        asset_id (str): The ID of the asset to retrieve.

    Returns:
        Optional[Dict[str, Union[str, Dict]]]: A dictionary with the key 'asset' containing:
            - id (str): The asset ID.
            - name (str): Name of the asset.
            - type (str): Type of the asset (e.g., "image", "video").
            - tags (List[str]): List of user-facing tags assigned to the asset.
            - created_at (int): Timestamp of asset creation (Unix time).
            - updated_at (int): Timestamp of last asset update (Unix time).
            - thumbnail (Optional[Dict[str, Union[str, int]]]):
                - width (int): Width of the thumbnail in pixels.
                - height (int): Height of the thumbnail in pixels.
                - url (str): Temporary URL to retrieve the thumbnail (expires in 15 minutes).
            - import_status (Optional[Dict[str, str]], deprecated):
                - state (str): Import job state ("in_progress", "success", "failed", "error").
            - import_error (Optional[Dict[str, str]], deprecated):
                - code (str): Error code ("file_too_big", "import_failed").
                - message (str): Description of what went wrong.
    """
    return DB.get("assets", {}).get(asset_id, {})


@tool_spec(
    spec={
        'name': 'update_asset',
        'description': 'Updates the metadata of an existing asset and returns the updated asset.',
        'parameters': {
            'type': 'object',
            'properties': {
                'asset_id': {
                    'type': 'string',
                    'description': 'The ID of the asset to update.'
                },
                'name': {
                    'type': 'string',
                    'description': 'New name for the asset (max 50 characters).'
                },
                'tags': {
                    'type': 'array',
                    'description': 'New list of tags for the asset (max 50 tags).',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'asset_id'
            ]
        }
    }
)
def update_asset(
    asset_id: str, name: Optional[str] = None, tags: Optional[List[str]] = None
) -> bool:
    """
    Updates the metadata of an existing asset and returns the updated asset.

    Args:
        asset_id (str): The ID of the asset to update.
        name (Optional[str]): New name for the asset (max 50 characters).
        tags (Optional[List[str]]): New list of tags for the asset (max 50 tags).

    Returns:
        bool: True if the asset was successfully updated, False if the asset was not found.
    """
    # if asset_id in DB.get("assets", {}):
    #     if name is not None and name.strip():
    #         DB["assets"][asset_id]["name"] = name[:50]  # Enforce max length of 50
    #     if tags is not None:
    #         DB["assets"][asset_id]["tags"] = tags[:50]  # Enforce max items of 50
    #     DB["assets"][asset_id]["updated_at"] = int(time.time())
    #     return True
    # return False
    pass


@tool_spec(
    spec={
        'name': 'delete_asset',
        'description': 'Deletes an asset by its ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'asset_id': {
                    'type': 'string',
                    'description': 'The ID of the asset to delete.'
                }
            },
            'required': [
                'asset_id'
            ]
        }
    }
)
def delete_asset(asset_id: str) -> bool:
    """
    Deletes an asset by its ID.

    Args:
        asset_id (str): The ID of the asset to delete.

    Returns:
        bool: True if the asset was successfully deleted, False if the asset was not found.
    """
    if asset_id in DB.get("assets", {}):
        del DB["assets"][asset_id]
        return True
    return False


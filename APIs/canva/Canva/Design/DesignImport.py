from common_utils.tool_spec_decorator import tool_spec
# canva/Canva/Design/DesignImport.py
"""
This module provides functionality for managing design import operations in Canva.

It includes functions for creating design import jobs from file uploads and public URLs,
retrieving import job status and results, and handling various file formats including PDF,
PNG, JPEG, and PowerPoint presentations. The module supports both direct file uploads
with metadata and URL-based imports with comprehensive validation.
"""

import uuid
import time
import base64
import random
import re
from typing import Optional, Dict, Any, List, Union

from canva.SimulationEngine.db import DB
from canva.SimulationEngine.models import DesignModel
from canva.SimulationEngine.utils import generate_canva_design_id


@tool_spec(
    spec={
        'name': 'create_design_import_job',
        'description': 'Creates a design import job from a file upload.',
        'parameters': {
            'type': 'object',
            'properties': {
                'import_metadata': {
                    'type': 'object',
                    'description': 'Metadata from Import-Metadata header with keys:',
                    'properties': {
                        'title_base64': {
                            'type': 'string',
                            'description': 'Base64-encoded design title. Max 50 characters when decoded.'
                        },
                        'mime_type': {
                            'type': 'string',
                            'description': 'MIME type of the file (e.g., "application/pdf").'
                        }
                    },
                    'required': [
                        'title_base64'
                    ]
                }
            },
            'required': [
                'import_metadata'
            ]
        }
    }
)
def create_design_import(
    import_metadata: Dict[str, Union[str, int]],
) -> Dict[str, Union[str, int, Dict, List]]:
    """
    Creates a design import job from a file upload.

    Args:
        import_metadata (Dict[str, Union[str, int]]): Metadata from Import-Metadata header with keys:
            - 'title_base64' (str): Base64-encoded design title. Max 50 characters when decoded.
            - 'mime_type' (Optional[str]): MIME type of the file (e.g., "application/pdf").

    Returns:
        Dict[str, Union[str, int, Dict, List]]: Dictionary containing import job data with keys:
            - 'job' (Dict[str, Union[str, int, Dict, List]]): Design import job details with fields:
                - 'id' (str): Job ID.
                - 'status' (str): Job status - "in_progress", "success", or "failed".
                - 'result' (Optional[Dict[str, Union[str, int, Dict, List]]]): Present if status is "success" with keys:
                    - 'designs' (List[Dict[str, Union[str, int, Dict]]]): List of imported design objects with fields:
                        - 'id' (str): Design ID.
                        - 'title' (Optional[str]): Design title.
                        - 'urls' (Dict[str, str]): Temporary URLs with keys:
                            - 'edit_url' (str): 30-day editing URL.
                            - 'view_url' (str): 30-day viewing URL.
                        - 'created_at' (int): Unix timestamp of creation.
                        - 'updated_at' (int): Unix timestamp of last update.
                        - 'page_count' (Optional[int]): Total number of pages.
                        - 'thumbnail' (Optional[Dict[str, Union[str, int]]]): Thumbnail info with keys:
                            - 'width' (int): Thumbnail width.
                            - 'height' (int): Thumbnail height.
                            - 'url' (str): Thumbnail URL. Expires in 15 minutes.
                - 'error' (Optional[Dict[str, str]]): Present if status is "failed" with keys:
                    - 'code' (str): Error code like "invalid_file", "fetch_failed", "internal_error".
                    - 'message' (str): Human-readable error description.

    Raises:
        ValueError: If import_metadata is not a dict, if title_base64 is missing or invalid,
            if decoded title exceeds 50 characters, or if mime_type is invalid.
    """
    # Input validation
    if not isinstance(import_metadata, dict):
        raise ValueError("import_metadata must be a dictionary")
    
    if "title_base64" not in import_metadata:
        raise ValueError("import_metadata must contain 'title_base64' field")
    
    title_base64 = import_metadata["title_base64"]
    if not isinstance(title_base64, str) or not title_base64:
        raise ValueError("title_base64 must be a non-empty string")
    
    # Decode base64 title
    try:
        title = base64.b64decode(title_base64).decode('utf-8')
    except Exception:
        raise ValueError("title_base64 must be valid base64 encoded string")
    
    # Validate decoded title length
    if len(title) > 50:
        raise ValueError("Decoded title must not exceed 50 characters")
    
    # Validate mime_type if provided
    if "mime_type" in import_metadata:
        mime_type = import_metadata["mime_type"]
        if not isinstance(mime_type, str):
            raise ValueError("mime_type must be a string")
        
        valid_mime_types = [
            "application/pdf", "image/png", "image/jpeg", "image/jpg",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        ]
        if mime_type not in valid_mime_types:
            raise ValueError(f"mime_type must be one of {valid_mime_types}")
    
    job_id = str(uuid.uuid4())
    timestamp = int(time.time())
    
    # Simulate job processing - random success/failure
    job_status = random.choice(["in_progress", "success", "failed"])
    
    job = {
        "id": job_id,
        "status": job_status,
        "import_metadata": import_metadata,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    if job_status == "success":
        # Create mock imported design
        design_id = generate_canva_design_id()
        page_count = random.randint(1, 5)
        
        job["result"] = {
            "designs": [{
                "id": design_id,
                "title": title,
                "urls": {
                    "edit_url": f"https://canva.com/design/{design_id}/edit",
                    "view_url": f"https://canva.com/design/{design_id}/view"
                },
                "created_at": timestamp,
                "updated_at": timestamp,
                "page_count": page_count,
                "thumbnail": {
                    "width": 200,
                    "height": 280,
                    "url": f"https://marketplace.canva.com/thumbnail/{design_id}.jpg"
                }
            }]
        }
        
        # Also add the design to the main designs database
        new_design = {
            "id": design_id,
            "title": title,
            "created_at": timestamp,
            "updated_at": timestamp,
            "page_count": page_count,
            "design_type": {
                "type": "preset",
                "name": "doc"
            },
            "asset_id": "imported_asset",
            "owner": {
                "user_id": "current_user",
                "team_id": "default_team"
            },
            "urls": {
                "edit_url": f"https://canva.com/design/{design_id}/edit",
                "view_url": f"https://canva.com/design/{design_id}/view"
            }
        }
        validated_design = DesignModel.model_validate(new_design)
        validated_design_dict = validated_design.model_dump()
        DB["Designs"][design_id] = validated_design_dict
        
    elif job_status == "failed":
        error_codes = ["invalid_file", "fetch_failed", "internal_error"]
        error_code = random.choice(error_codes)
        job["error"] = {
            "code": error_code,
            "message": f"Import failed: {error_code.replace('_', ' ').title()}"
        }
    
    # Store in database
    if "ImportJobs" not in DB:
        DB["ImportJobs"] = {}
    DB["ImportJobs"][job_id] = job
    
    return {"job": job}


@tool_spec(
    spec={
        'name': 'get_design_import_job',
        'description': 'Retrieves the status and result of a design import job.',
        'parameters': {
            'type': 'object',
            'properties': {
                'job_id': {
                    'type': 'string',
                    'description': 'The ID of the design import job.'
                }
            },
            'required': [
                'job_id'
            ]
        }
    }
)
def get_design_import_job(job_id: str) -> Dict[str, Union[str, int, Dict, List]]:
    """
    Retrieves the status and result of a design import job.

    Args:
        job_id (str): The ID of the design import job.

    Returns:
        Dict[str, Union[str, int, Dict, List]]: Dictionary containing import job status with keys:
            - 'job' (Dict[str, Union[str, int, Dict, List]]): Design import job details with fields:
                - 'id' (str): Job ID.
                - 'status' (str): Job status - "in_progress", "success", or "failed".
                - 'result' (Optional[Dict[str, Union[str, int, Dict, List]]]): Present if status is "success" with keys:
                    - 'designs' (List[Dict[str, Union[str, int, Dict]]]): List of imported designs with fields:
                        - 'id' (str): Design ID.
                        - 'title' (Optional[str]): Design title.
                        - 'urls' (Dict[str, str]): Temporary URLs with keys:
                            - 'edit_url' (str): 30-day validity edit URL.
                            - 'view_url' (str): 30-day validity view URL.
                        - 'created_at' (int): Creation timestamp.
                        - 'updated_at' (int): Last update timestamp.
                        - 'thumbnail' (Optional[Dict[str, Union[str, int]]]): Thumbnail data with keys:
                            - 'width' (int): Width in pixels.
                            - 'height' (int): Height in pixels.
                            - 'url' (str): Thumbnail URL.
                        - 'page_count' (Optional[int]): Number of pages.
                - 'error' (Optional[Dict[str, str]]): Error details if job failed with keys:
                    - 'code' (str): Error code (e.g., "invalid_file").
                    - 'message' (str): Error description.

    Raises:
        ValueError: If job_id is empty or if import job not found.
    """
    # Input validation
    if not isinstance(job_id, str) or not job_id:
        raise ValueError("job_id must be a non-empty string")
    
    # Check if job exists
    if "ImportJobs" not in DB or job_id not in DB["ImportJobs"]:
        raise ValueError(f"Import job with ID {job_id} not found")
    
    job = DB["ImportJobs"][job_id].copy()
    current_time = int(time.time())
    
    # Simulate job progress for "in_progress" jobs
    if job["status"] == "in_progress":
        # After 60 seconds, randomly complete or fail the job
        time_elapsed = current_time - job["created_at"]
        if time_elapsed > 60:
            # Randomly complete or fail
            new_status = random.choice(["success", "failed"])
            job["status"] = new_status
            job["updated_at"] = current_time
            
            if new_status == "success":
                # Create mock imported design
                design_id = generate_canva_design_id()
                page_count = random.randint(1, 5)
                
                # Decode title from metadata
                title = "Imported Design"
                if "import_metadata" in job and "title_base64" in job["import_metadata"]:
                    try:
                        title = base64.b64decode(job["import_metadata"]["title_base64"]).decode('utf-8')
                    except:
                        pass
                
                job["result"] = {
                    "designs": [{
                        "id": design_id,
                        "title": title,
                        "urls": {
                            "edit_url": f"https://canva.com/design/{design_id}/edit",
                            "view_url": f"https://canva.com/design/{design_id}/view"
                        },
                        "created_at": current_time,
                        "updated_at": current_time,
                        "page_count": page_count,
                        "thumbnail": {
                            "width": 200,
                            "height": 280,
                            "url": f"https://marketplace.canva.com/thumbnail/{design_id}.jpg"
                        }
                    }]
                }
                
                # Also add the design to the main designs database
                new_design = {
                    "id": design_id,
                    "title": title,
                    "created_at": current_time,
                    "updated_at": current_time,
                    "page_count": page_count,
                    "design_type": {"type": "preset", "name": "doc"},
                    "asset_id": "imported_asset",
                    "owner": {
                        "user_id": "current_user",
                        "team_id": "default_team"
                    },
                    "urls": {
                        "edit_url": f"https://canva.com/design/{design_id}/edit",
                        "view_url": f"https://canva.com/design/{design_id}/view"
                    }
                }
                DB["Designs"][design_id] = new_design
                
            else:
                error_codes = ["invalid_file", "fetch_failed", "internal_error"]
                error_code = random.choice(error_codes)
                job["error"] = {
                    "code": error_code,
                    "message": f"Import failed: {error_code.replace('_', ' ').title()}"
                }
            
            # Update the job in the database
            DB["ImportJobs"][job_id] = job
    
    # Remove internal fields before returning
    response_job = {k: v for k, v in job.items() if k not in ["import_metadata", "created_at"]}
    
    return {"job": response_job}


@tool_spec(
    spec={
        'name': 'create_url_design_import_job',
        'description': 'Creates a design import job using a public URL.',
        'parameters': {
            'type': 'object',
            'properties': {
                'title': {
                    'type': 'string',
                    'description': 'The title for the imported design. Must be 1-255 characters.'
                },
                'url': {
                    'type': 'string',
                    'description': 'Publicly accessible file URL. Must be 1-2048 characters.'
                },
                'mime_type': {
                    'type': 'string',
                    'description': """ MIME type of the file. Must be 1-100 characters
                    if provided. Auto-detected if not specified. """
                }
            },
            'required': [
                'title',
                'url'
            ]
        }
    }
)
def create_url_import_job(
    title: str, url: str, mime_type: Optional[str] = None
) -> Dict[str, Union[str, int, Dict, List]]:
    """
    Creates a design import job using a public URL.

    Args:
        title (str): The title for the imported design. Must be 1-255 characters.
        url (str): Publicly accessible file URL. Must be 1-2048 characters.
        mime_type (Optional[str]): MIME type of the file. Must be 1-100 characters
            if provided. Auto-detected if not specified.

    Returns:
        Dict[str, Union[str, int, Dict, List]]: Dictionary containing import job data with keys:
            - 'job' (Dict[str, Union[str, int, Dict, List]]): Design import job details with fields:
                - 'id' (str): Job ID.
                - 'status' (str): Job status - "in_progress", "success", or "failed".
                - 'result' (Optional[Dict[str, Union[str, int, Dict, List]]]): Present if status is "success" with keys:
                    - 'designs' (List[Dict[str, Union[str, int, Dict]]]): List of imported designs with fields:
                        - 'id' (str): Design ID.
                        - 'title' (Optional[str]): Design title.
                        - 'urls' (Dict[str, str]): Design URLs with keys:
                            - 'edit_url' (str): Edit URL.
                            - 'view_url' (str): View URL.
                        - 'created_at' (int): Creation timestamp.
                        - 'updated_at' (int): Last update timestamp.
                        - 'thumbnail' (Optional[Dict[str, Union[str, int]]]): Thumbnail info with keys:
                            - 'width' (int): Width in pixels.
                            - 'height' (int): Height in pixels.
                            - 'url' (str): Thumbnail URL.
                        - 'page_count' (Optional[int]): Number of pages.
                - 'error' (Optional[Dict[str, str]]): Error details if job failed with keys:
                    - 'code' (str): Error code like "duplicate_import", "fetch_failed".
                    - 'message' (str): Human-readable error message.

    Raises:
        ValueError: If title or url length is invalid, if URL format is invalid,
            if mime_type length is invalid, or if mime_type value is not supported.
    """
    # Input validation
    if not isinstance(title, str) or not title:
        raise ValueError("title must be a non-empty string")
    if len(title) < 1 or len(title) > 255:
        raise ValueError("title must be between 1 and 255 characters")
    
    if not isinstance(url, str) or not url:
        raise ValueError("url must be a non-empty string")
    if len(url) < 1 or len(url) > 2048:
        raise ValueError("url must be between 1 and 2048 characters")
    
    # Basic URL format validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        raise ValueError("url must be a valid HTTP or HTTPS URL")
    
    if mime_type is not None:
        if not isinstance(mime_type, str):
            raise ValueError("mime_type must be a string")
        if len(mime_type) < 1 or len(mime_type) > 100:
            raise ValueError("mime_type must be between 1 and 100 characters")
        
        valid_mime_types = [
            "application/pdf", "image/png", "image/jpeg", "image/jpg",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        ]
        if mime_type not in valid_mime_types:
            raise ValueError(f"mime_type must be one of {valid_mime_types}")
    
    job_id = str(uuid.uuid4())
    timestamp = int(time.time())
    
    # Simulate job processing - random success/failure
    job_status = random.choice(["in_progress", "success", "failed"])
    
    job = {
        "id": job_id,
        "status": job_status,
        "title": title,
        "url": url,
        "mime_type": mime_type,
        "created_at": timestamp,
        "updated_at": timestamp,
        "job_type": "url_import"
    }
    
    if job_status == "success":
        # Create mock imported design
        design_id = generate_canva_design_id()
        page_count = random.randint(1, 5)
        
        job["result"] = {
            "designs": [{
                "id": design_id,
                "title": title,
                "urls": {
                    "edit_url": f"https://canva.com/design/{design_id}/edit",
                    "view_url": f"https://canva.com/design/{design_id}/view"
                },
                "created_at": timestamp,
                "updated_at": timestamp,
                "page_count": page_count,
                "thumbnail": {
                    "width": 200,
                    "height": 280,
                    "url": f"https://marketplace.canva.com/thumbnail/{design_id}.jpg"
                }
            }]
        }
        
        # Also add the design to the main designs database
        new_design = {
            "id": design_id,
            "title": title,
            "created_at": timestamp,
            "updated_at": timestamp,
            "page_count": page_count,
            "design_type": {"type": "preset", "name": "doc"},
            "asset_id": "imported_asset",
            "owner": {
                "user_id": "current_user",
                "team_id": "default_team"
            },
            "urls": {
                "edit_url": f"https://canva.com/design/{design_id}/edit",
                "view_url": f"https://canva.com/design/{design_id}/view"
            }
        }
        DB["Designs"][design_id] = new_design
        
    elif job_status == "failed":
        error_codes = ["duplicate_import", "fetch_failed", "invalid_url", "unsupported_format"]
        error_code = random.choice(error_codes)
        job["error"] = {
            "code": error_code,
            "message": f"URL import failed: {error_code.replace('_', ' ').title()}"
        }
    
    # Store in database (use same ImportJobs table but mark as URL import)
    if "ImportJobs" not in DB:
        DB["ImportJobs"] = {}
    DB["ImportJobs"][job_id] = job
    
    return {"job": job}


@tool_spec(
    spec={
        'name': 'get_url_design_import_job',
        'description': 'Retrieves the status and result of a URL import job.',
        'parameters': {
            'type': 'object',
            'properties': {
                'job_id': {
                    'type': 'string',
                    'description': 'The ID of the URL import job.'
                }
            },
            'required': [
                'job_id'
            ]
        }
    }
)
def get_url_import_job(job_id: str) -> Dict[str, Union[str, int, Dict, List]]:
    """
    Retrieves the status and result of a URL import job.

    Args:
        job_id (str): The ID of the URL import job.

    Returns:
        Dict[str, Union[str, int, Dict, List]]: Dictionary containing import job status with keys:
            - 'job' (Dict[str, Union[str, int, Dict, List]]): Import job details with fields:
                - 'id' (str): Job ID.
                - 'status' (str): Job status - "in_progress", "success", or "failed".
                - 'result' (Optional[Dict[str, Union[str, int, Dict, List]]]): Present if status is "success" with keys:
                    - 'designs' (List[Dict[str, Union[str, int, Dict]]]): List of imported designs with fields:
                        - 'id' (str): Imported design ID.
                        - 'title' (Optional[str]): Design title.
                        - 'urls' (Dict[str, str]): Design URLs with keys:
                            - 'edit_url' (str): Temporary edit URL.
                            - 'view_url' (str): Temporary view URL.
                        - 'created_at' (int): Creation timestamp.
                        - 'updated_at' (int): Last update timestamp.
                        - 'thumbnail' (Optional[Dict[str, Union[str, int]]]): Thumbnail data with keys:
                            - 'width' (int): Width in pixels.
                            - 'height' (int): Height in pixels.
                            - 'url' (str): Thumbnail URL.
                        - 'page_count' (Optional[int]): Number of pages.
                - 'error' (Optional[Dict[str, str]]): Error details if job failed with keys:
                    - 'code' (str): Error code like "design_import_throttled", "fetch_failed".
                    - 'message' (str): Failure explanation.

    Raises:
        ValueError: If job_id is empty, if import job not found, or if job is not a URL import job.
    """
    # Input validation
    if not isinstance(job_id, str) or not job_id:
        raise ValueError("job_id must be a non-empty string")
    
    # Check if job exists
    if "ImportJobs" not in DB or job_id not in DB["ImportJobs"]:
        raise ValueError(f"Import job with ID {job_id} not found")
    
    job = DB["ImportJobs"][job_id].copy()
    
    # Verify this is a URL import job
    if job.get("job_type") != "url_import":
        raise ValueError(f"Job {job_id} is not a URL import job")
    
    current_time = int(time.time())
    
    # Simulate job progress for "in_progress" jobs
    if job["status"] == "in_progress":
        # After 45 seconds, randomly complete or fail the job
        time_elapsed = current_time - job["created_at"]
        if time_elapsed > 45:
            # Randomly complete or fail
            new_status = random.choice(["success", "failed"])
            job["status"] = new_status
            job["updated_at"] = current_time
            
            if new_status == "success":
                # Create mock imported design
                design_id = generate_canva_design_id()
                page_count = random.randint(1, 5)
                title = job.get("title", "Imported Design")
                
                job["result"] = {
                    "designs": [{
                        "id": design_id,
                        "title": title,
                        "urls": {
                            "edit_url": f"https://canva.com/design/{design_id}/edit",
                            "view_url": f"https://canva.com/design/{design_id}/view"
                        },
                        "created_at": current_time,
                        "updated_at": current_time,
                        "page_count": page_count,
                        "thumbnail": {
                            "width": 200,
                            "height": 280,
                            "url": f"https://marketplace.canva.com/thumbnail/{design_id}.jpg"
                        }
                    }]
                }
                
                # Also add the design to the main designs database
                new_design = {
                    "id": design_id,
                    "title": title,
                    "created_at": current_time,
                    "updated_at": current_time,
                    "page_count": page_count,
                    "design_type": {"type": "preset", "name": "doc"},
                    "asset_id": "imported_asset",
                    "owner": {
                        "user_id": "current_user",
                        "team_id": "default_team"
                    },
                    "urls": {
                        "edit_url": f"https://canva.com/design/{design_id}/edit",
                        "view_url": f"https://canva.com/design/{design_id}/view"
                    }
                }
                DB["Designs"][design_id] = new_design
                
            else:
                error_codes = ["design_import_throttled", "fetch_failed", "invalid_url", "timeout"]
                error_code = random.choice(error_codes)
                job["error"] = {
                    "code": error_code,
                    "message": f"URL import failed: {error_code.replace('_', ' ').title()}"
                }
            
            # Update the job in the database
            DB["ImportJobs"][job_id] = job
    
    # Remove internal fields before returning
    response_job = {k: v for k, v in job.items() 
                   if k not in ["title", "url", "mime_type", "created_at", "job_type"]}
    
    return {"job": response_job}

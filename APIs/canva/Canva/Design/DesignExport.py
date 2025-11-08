from common_utils.tool_spec_decorator import tool_spec
# canva/Canva/Design/DesignExport.py
"""
This module provides functionality for managing design export operations in Canva.

It includes functions for creating design export jobs with various format options (PDF, JPG, PNG, PPTX, GIF, MP4),
retrieving export job status and results, and handling export format validation. The module supports
comprehensive export options including quality settings, page selection, size customization, and format-specific
parameters like transparency and compression. 
"""

import uuid
import time
import random
from typing import Optional, Union, List, Dict, Any

from canva.SimulationEngine.db import DB
from canva.SimulationEngine.custom_errors import InvalidAssetIDError, InvalidTitleError, InvalidDesignIDError


@tool_spec(
    spec={
        'name': 'create_design_export_job',
        'description': 'Creates a design export job.',
        'parameters': {
            'type': 'object',
            'properties': {
                'design_id': {
                    'type': 'string',
                    'description': 'The ID of the design to export.'
                },
                'format': {
                    'type': 'object',
                    'description': 'A set of options that define the format and quality of the design export.',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': """ Export format type. Must be one of:
                                 "pdf", "jpg", "png", "pptx", "gif", "mp4". """
                        },
                        'quality': {
                            'type': 'integer',
                            'description': """ Quality setting when required:
                                 - Integer between 1-100 (compression quality for all formats). """
                        },
                        'pages': {
                            'type': 'array',
                            'description': 'Page numbers to export (1-based index).',
                            'items': {
                                'type': 'integer'
                            }
                        },
                        'export_quality': {
                            'type': 'string',
                            'description': '"regular" or "pro". Default is "regular".'
                        },
                        'size': {
                            'type': 'string',
                            'description': 'Paper size for PDFs. One of "a4", "a3", "letter", "legal".'
                        },
                        'height': {
                            'type': 'integer',
                            'description': 'Height in pixels (min: 40, max: 25000).'
                        },
                        'width': {
                            'type': 'integer',
                            'description': 'Width in pixels (min: 40, max: 25000).'
                        },
                        'lossless': {
                            'type': 'boolean',
                            'description': 'For PNG. If True, export without compression.'
                        },
                        'transparent_background': {
                            'type': 'boolean',
                            'description': 'For PNG. If True, enables transparency.'
                        },
                        'as_single_image': {
                            'type': 'boolean',
                            'description': 'If True, export multipage design as single image.'
                        }
                    },
                    'required': [
                        'type'
                    ]
                }
            },
            'required': [
                'design_id',
                'format'
            ]
        }
    }
)
def create_design_export_job(
    design_id: str,
    format: Dict[str, Union[str, int, bool, List[int]]]
) -> Dict[str, Union[str, Dict]]:
    """
    Creates a design export job.

    Args:
        design_id (str): The ID of the design to export.
        format (Dict[str, Union[str, int, bool, List[int]]]): A set of options that define the format and quality of the design export.
            - 'type' (str): Export format type. Must be one of:
                "pdf", "jpg", "png", "pptx", "gif", "mp4".
            - 'quality' (Optional[int]): Quality setting when required:
                - Integer between 1-100 (compression quality for all formats).
            - 'pages' (Optional[List[int]]): Page numbers to export (1-based index).
            - 'export_quality' (Optional[str]): "regular" or "pro". Default is "regular".
            - 'size' (Optional[str]): Paper size for PDFs. One of "a4", "a3", "letter", "legal".
            - 'height' (Optional[int]): Height in pixels (min: 40, max: 25000).
            - 'width' (Optional[int]): Width in pixels (min: 40, max: 25000).
            - 'lossless' (Optional[bool]): For PNG. If True, export without compression.
            - 'transparent_background' (Optional[bool]): For PNG. If True, enables transparency.
            - 'as_single_image' (Optional[bool]): If True, export multipage design as single image.

    Returns:
        Dict[str, Union[str, Dict]]: Dictionary containing export job data with keys:
            - 'job' (Dict[str, Union[str, int, Dict]]): Export job details with fields:
                - 'id' (str): Export job ID.
                - 'status' (str): Job status - "in_progress", "success", or "failed".
                - 'urls' (Optional[List[str]]): Download URLs for exported pages. Expire in 24 hours.
                - 'error' (Optional[Dict[str, str]]): Error information if job fails with keys:
                    - 'code' (str): Error code - "license_required", "approval_required", 
                      or "internal_failure".
                    - 'message' (str): Human-readable error message.

    Raises:
        ValueError: If design_id or format is invalid, if design not found,
            if format type is invalid, or if format-specific validation fails.
    """
    # Input validation
    if not isinstance(design_id, str) or not design_id:
        raise ValueError("design_id must be a non-empty string")
    if not isinstance(format, dict):
        raise ValueError("format must be a dictionary")
    
    # Check if design exists
    if design_id not in DB["Designs"]:
        raise ValueError(f"Design with ID {design_id} not found")
    
    # Validate format type
    if "type" not in format:
        raise ValueError("format must contain 'type' field")
    
    valid_types = ["pdf", "jpg", "png", "pptx", "gif", "mp4"]
    export_type = format["type"]
    if export_type not in valid_types:
        raise ValueError(f"format.type must be one of {valid_types}. Got: {export_type}")
    
    # Validate format-specific fields
    if "quality" in format:
        quality = format["quality"]
        if not isinstance(quality, int) or quality < 1 or quality > 100:
            raise ValueError("Quality must be an integer between 1 and 100")
    
    if "export_quality" in format:
        if format["export_quality"] not in ["regular", "pro"]:
            raise ValueError("export_quality must be 'regular' or 'pro'")
    
    if "size" in format:
        if format["size"] not in ["a4", "a3", "letter", "legal"]:
            raise ValueError("size must be one of: a4, a3, letter, legal")
    
    if "height" in format:
        height = format["height"]
        if not isinstance(height, int) or height < 40 or height > 25000:
            raise ValueError("height must be an integer between 40 and 25000")
    
    if "width" in format:
        width = format["width"]
        if not isinstance(width, int) or width < 40 or width > 25000:
            raise ValueError("width must be an integer between 40 and 25000")
    
    job_id = str(uuid.uuid4())
    timestamp = int(time.time())
    
    # Simulate job processing - random success/failure for demonstration
    job_status = random.choice(["in_progress", "success", "failed"])
    
    job = {
        "id": job_id,
        "status": job_status,
        "design_id": design_id,
        "format": format,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    if job_status == "success":
        # Generate mock download URLs
        design = DB["Designs"][design_id]
        page_count = design.get("page_count", 1)
        if "pages" in format:
            page_count = len(format["pages"])
        
        job["urls"] = [
            f"https://export.canva.com/files/{job_id}/page_{i+1}.{export_type}"
            for i in range(page_count)
        ]
    elif job_status == "failed":
        error_codes = ["license_required", "approval_required", "internal_failure"]
        error_code = random.choice(error_codes)
        job["error"] = {
            "code": error_code,
            "message": f"Export failed: {error_code.replace('_', ' ').title()}"
        }
    
    # Store in database
    if "ExportJobs" not in DB:
        DB["ExportJobs"] = {}
    DB["ExportJobs"][job_id] = job
    
    return {"job": job}


@tool_spec(
    spec={
        'name': 'get_design_export_job',
        'description': 'Retrieves the status and results of a design export job.',
        'parameters': {
            'type': 'object',
            'properties': {
                'job_id': {
                    'type': 'string',
                    'description': 'The export job ID.'
                }
            },
            'required': [
                'job_id'
            ]
        }
    }
)
def get_design_export_job(job_id: str) -> Dict[str, Union[str, Dict]]:
    """
    Retrieves the status and results of a design export job.

    Args:
        job_id (str): The export job ID.

    Returns:
        Dict[str, Union[str, Dict]]: Dictionary containing export job status with keys:
            - 'job' (Dict[str, Union[str, int, Dict]]): Export job details with fields:
                - 'id' (str): Export job ID.
                - 'status' (str): Current job status - "in_progress", "success", or "failed".
                - 'urls' (Optional[List[str]]): List of downloadable file URLs. Valid for 24 hours.
                - 'error' (Optional[Dict[str, str]]): Error details if export failed with keys:
                    - 'code' (str): Failure reason - "license_required", "approval_required", 
                      or "internal_failure".
                    - 'message' (str): Human-readable failure explanation.

    Raises:
        ValueError: If job_id is empty or if export job not found.
    """
    # Input validation
    if not isinstance(job_id, str) or not job_id:
        raise ValueError("job_id must be a non-empty string")
    
    # Check if job exists
    if "ExportJobs" not in DB or job_id not in DB["ExportJobs"]:
        raise ValueError(f"Export job with ID {job_id} not found")
    
    job = DB["ExportJobs"][job_id].copy()
    current_time = int(time.time())
    
    # Simulate job progress for "in_progress" jobs
    if job["status"] == "in_progress":
        # After 30 seconds, randomly complete or fail the job
        time_elapsed = current_time - job["created_at"]
        if time_elapsed > 30:
            # Randomly complete or fail
            new_status = random.choice(["success", "failed"])
            job["status"] = new_status
            job["updated_at"] = current_time
            
            if new_status == "success":
                # Generate mock download URLs
                design_id = job["design_id"]
                export_type = job["format"]["type"]
                page_count = 1
                if "pages" in job["format"]:
                    page_count = len(job["format"]["pages"])
                elif design_id in DB["Designs"]:
                    design = DB["Designs"][design_id]
                    page_count = design.get("page_count", 1)
                
                job["urls"] = [
                    f"https://export.canva.com/files/{job_id}/page_{i+1}.{export_type}"
                    for i in range(page_count)
                ]
            else:
                error_codes = ["license_required", "approval_required", "internal_failure"]
                error_code = random.choice(error_codes)
                job["error"] = {
                    "code": error_code,
                    "message": f"Export failed: {error_code.replace('_', ' ').title()}"
                }
            
            # Update the job in the database
            DB["ExportJobs"][job_id] = job
    
    # Remove internal fields before returning
    response_job = {k: v for k, v in job.items() if k not in ["design_id", "format", "created_at"]}
    
    return {"job": response_job}



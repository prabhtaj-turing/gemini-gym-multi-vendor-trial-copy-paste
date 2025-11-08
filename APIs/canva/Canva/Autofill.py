from common_utils.tool_spec_decorator import tool_spec
# canva/Canva/Autofill.py

from typing import Optional, Dict, Any, Union
import uuid
import sys
import os

sys.path.append("APIs")

from canva.Canva.BrandTemplate import get_brand_template
from canva.Canva.Design import create_design
import canva


@tool_spec(
    spec={
        'name': 'create_autofill_job',
        'description': 'Creates an asynchronous job to autofill a design from a brand template with input data.',
        'parameters': {
            'type': 'object',
            'properties': {
                'brand_template_id': {
                    'type': 'string',
                    'description': 'ID of the input brand template.'
                },
                'data': {
                    'type': 'object',
                    'description': 'Dictionary of data fields to autofill. Each key maps to a field object with:',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Required. One of "image", "text", or "chart".'
                        },
                        'asset_id': {
                            'type': 'string',
                            'description': 'Required if type is "image".'
                        },
                        'text': {
                            'type': 'string',
                            'description': 'Required if type is "text".'
                        },
                        'chart_data': {
                            'type': 'object',
                            'description': 'Required if type is "chart". Structure:',
                            'properties': {
                                'rows': {
                                    'type': 'array',
                                    'description': 'List of rows, where each row contains:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'cells': {
                                                'type': 'array',
                                                'description': 'List of cells, each with:',
                                                'items': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'type': {
                                                            'type': 'string',
                                                            'description': 'One of "string", "number", "boolean", "date".'
                                                        }
                                                    },
                                                    'required': [
                                                        'type'
                                                    ]
                                                }
                                            }
                                        },
                                        'required': [
                                            'cells'
                                        ]
                                    }
                                }
                            },
                            'required': [
                                'rows'
                            ]
                        }
                    },
                    'required': [
                        'type'
                    ]
                },
                'title': {
                    'type': 'string',
                    'description': "Optional title for the autofilled design. If not provided, defaults to the template's title."
                }
            },
            'required': [
                'brand_template_id',
                'data'
            ]
        }
    }
)
def create_autofill_job(
    brand_template_id: str, data: Dict[str, Union[str, Dict]], title: Optional[str] = None
) -> Dict[str, Union[str, Dict]]:
    """
    Creates an asynchronous job to autofill a design from a brand template with input data.

    Args:
        brand_template_id (str): ID of the input brand template.
        data (Dict[str, Union[str, Dict]]): Dictionary of data fields to autofill. Each key maps to a field object with:
            - type (str): Required. One of "image", "text", or "chart".
            - asset_id (Optional[str]): Required if type is "image".
            - text (Optional[str]): Required if type is "text".
            - chart_data (Optional[Dict[str, Union[str, List]]]): Required if type is "chart". Structure:
                - rows (List[Dict]): List of rows, where each row contains:
                    - cells (List[Dict]): List of cells, each with:
                        - type (str): One of "string", "number", "boolean", "date".
        title (Optional[str]): Optional title for the autofilled design. If not provided, defaults to the template's title.

    Returns:
        Dict[str, Union[str, Dict]]: A dictionary representing the created autofill job, including:
            - id (str): Unique ID of the autofill job.
            - status (str): Status of the job. One of "success", "in_progress", or "failed".
            - result (Optional[Dict[str, Union[str, Dict[str, Union[str, int, Dict[str, Union[str, int]]]]]]): Present only if status is "success". Includes:
                - type (str): "create_design"
                - design (Dict):
                    - id (str): Design ID.
                    - title (str): Design title.
                    - url (str): Permanent URL to the design (if available).
                    - thumbnail (Optional[Dict[str, Union[str, int]]]):
                        - width (int)
                        - height (int)
                        - url (str): Thumbnail URL (expires in 15 minutes).
    """
    template = get_brand_template(brand_template_id)
    asset_id = "test_asset_id" if not 'asset_id' in data else data.get("asset_id")
    if not title:
        title = template.get("brand_template", {}).get("title", None)
    create_design(
        template.get("brand_template", {}).get("design_type", {}),
        asset_id=asset_id,
        title=title,
    )

    job_id = str(uuid.uuid4())
    job_entry = {
        "id": job_id,
        "status": "success",
        "result": {
            "type": "create_design",
            "design": {
                "id": brand_template_id,
                "title": title,
                "url": f"https://www.canva.com/design/{brand_template_id}/edit",
                "thumbnail": canva.SimulationEngine.db.DB["Designs"]
                .get(brand_template_id, {})
                .get("thumbnail", {}),
            },
        },
    }
    canva.SimulationEngine.db.DB["autofill_jobs"][job_id] = job_entry
    return job_entry


@tool_spec(
    spec={
        'name': 'get_autofill_job',
        'description': 'Retrieves the status and results of an autofill job by its ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'job_id': {
                    'type': 'string',
                    'description': 'The ID of the autofill job to retrieve.'
                }
            },
            'required': [
                'job_id'
            ]
        }
    }
)
def get_autofill_job(job_id: str) -> Dict[str, Union[str, Dict]]:
    """
    Retrieves the status and results of an autofill job by its ID.

    Args:
        job_id (str): The ID of the autofill job to retrieve.

    Returns:
        Dict[str, Union[str, Dict]]: If found, returns job details:
            - id (str): Job ID.
            - status (str): Job status ("in_progress", "success", "failed").
            - result (Optional[Dict[str, Union[str, Dict[str, Union[str, int, Dict[str, Union[str, int]]]]]]): Present only if status is "success". Includes:
                - type (str): "create_design"
                - design (Dict):
                    - id (str): Design ID.
                    - title (str): Design title.
                    - url (str, optional): Permanent URL of the design.
                    - thumbnail (Optional[Dict[str, Union[str, int]]]):
                        - width (int)
                        - height (int)
                        - url (str): Thumbnail URL (expires in 15 minutes).
        If not found, returns:
            - error (str): Error message ("Job not found").
    """
    return canva.SimulationEngine.db.DB["autofill_jobs"].get(
        job_id, {"error": "Job not found"}
    )

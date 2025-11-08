"""
Hyper3D Rodin integration functionalities for the Blender API simulation.
"""
from common_utils.tool_spec_decorator import tool_spec
import os
import uuid
from typing import Dict, Optional, List, Union
from pydantic import ValidationError as PydanticValidationError

from blender.SimulationEngine import models, custom_errors, utils
from blender.SimulationEngine.db import DB
from blender.SimulationEngine.models import (GenerateHyper3DModelViaTextResponse, ImportGeneratedAssetArguments,
                                             ImportGeneratedAssetResponse)
from blender.SimulationEngine.utils import update_job_import_failure


@tool_spec(
    spec={
        'name': 'get_hyper3d_status',
        'description': """ Check if Hyper3D Rodin integration is enabled and properly configured in Blender.
        
        This function checks if Hyper3D Rodin integration is enabled in Blender.
        It returns a message indicating whether Hyper3D Rodin features are available.
        The function is also instructed not to emphasize the key type in the returned
        message, but to silently remember it. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_hyper3d_status() -> Dict[str, Union[bool, str]]:
    """
    Check if Hyper3D Rodin integration is enabled and properly configured in Blender.

    This function checks if Hyper3D Rodin integration is enabled in Blender.
    It returns a message indicating whether Hyper3D Rodin features are available.
    The function is also instructed not to emphasize the key type in the returned
    message, but to silently remember it.

    Returns:
        Dict[str, Union[bool, str]]: Details of the Hyper3D Rodin integration status. This dictionary includes the following keys:
            - is_enabled (bool): True if Hyper3D Rodin integration is enabled and configured, False otherwise.
            - mode (str): The current operational mode of Hyper3D Rodin (e.g., "MAIN_SITE", "FAL_AI"). Always present and always one of the allowed values.
            - message (str): A human-readable message about the status and configuration.

    Raises:
        ValidationError: If there's an issue checking the Hyper3D Rodin addon status or configuration within Blender.
            - If Hyper3D service status is not configured in DB.
            - If mode is invalid in Hyper3D status configuration.
            - If is_enabled is missing in Hyper3D status configuration.
            - If message is missing in Hyper3D status configuration.
    """
    if 'hyper3d_service_status' not in DB:
        raise custom_errors.ValidationError("Hyper3D service status not configured in DB.")

    status_config = DB.get('hyper3d_service_status') or {}

    if 'is_enabled' not in status_config:
        raise custom_errors.ValidationError("Hyper3D status configuration is missing 'is_enabled' key.")

    is_enabled = status_config['is_enabled']
    mode_value = status_config.get('mode', '')
    allowed_mode_values = [m.value for m in models.Hyper3DMode]
    if mode_value not in allowed_mode_values:
        raise custom_errors.ValidationError("Invalid value for 'mode' in Hyper3D status configuration.")

    if 'message' not in status_config:
        raise custom_errors.ValidationError("Hyper3D status configuration is missing 'message' key.")
    message_value = status_config['message']

    return {
        "is_enabled": is_enabled,
        "mode": mode_value,
        "message": message_value,
    }


@tool_spec(
    spec={
        'name': 'generate_hyper3d_model_via_text',
        'description': """ Generate 3D asset using Hyper3D by giving description of the desired asset, and import the asset into Blender.
        
        The 3D asset has built-in materials. The generated model has a normalized size, so re-scaling after generation can be useful. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'text_prompt': {
                    'type': 'string',
                    'description': 'A short description of the desired model in **English**.'
                },
                'bbox_condition': {
                    'type': 'array',
                    'description': 'Optional. If given, it has to be a list of floats of length 3. Controls the ratio between [Length, Width, Height] of the model. Defaults to None.',
                    'items': {
                        'type': 'number'
                    }
                }
            },
            'required': [
                'text_prompt'
            ]
        }
    }
)
def generate_hyper3d_model_via_text(text_prompt: str, bbox_condition: Optional[List[float]] = None) -> Dict[str, str]:
    """
    Generate 3D asset using Hyper3D by giving description of the desired asset, and import the asset into Blender.

    The 3D asset has built-in materials. The generated model has a normalized size, so re-scaling after generation can be useful.

    Args:
        text_prompt (str): A short description of the desired model in **English**.
        bbox_condition (Optional[List[float]]): Optional. If given, it has to be a list of floats of length 3. Controls the ratio between [Length, Width, Height] of the model. Defaults to None.

    Returns:
        Dict[str, str]: Response from initiating a model generation task via text. This dictionary contains the following keys:
            - status (str): 'success_queued' if the generation task was successfully submitted, or 'failure' if submission failed.
            - message (str): A descriptive message about the submission outcome.
            - task_uuid (Optional[str]): The task UUID (for MAIN_SITE mode, if applicable) assigned to the generation job. Used for polling status and importing.
            - request_id (Optional[str]): The request ID (for FAL_AI mode, if applicable) assigned to the generation job. Used for polling status and importing.
            - subscription_key (Optional[str]): The subscription key (for MAIN_SITE mode, if applicable) related to the generation job. May be needed for polling.

    Raises:
        Hyper3DAPIError: If there's an issue communicating with the Hyper3D API during task submission or the API returns an error.
        InvalidInputError: If the text_prompt is invalid, empty, or bbox_condition is malformed.
        ObjectNotFoundError: If Hyper3D Rodin integration is not enabled or not configured correctly in Blender.
        ValidationError: If input arguments fail validation.
    """

    # 1. Check Hyper3D Service Status
    hyper3d_status_dict = DB.get('hyper3d_service_status')

    # Case: 'hyper3d_service_status' key missing from DB
    if not (hyper3d_status_dict and hyper3d_status_dict.get('is_enabled')):
        raise custom_errors.ObjectNotFoundError(
            "Hyper3D Rodin integration is not enabled or not configured correctly."
        )

    # 2. Input Validation
    # text_prompt validation
    if not isinstance(text_prompt, str):
        raise custom_errors.ValidationError("Input validation failed: text_prompt must be a string.")
    if not text_prompt.strip():  # Check after ensuring it's a string
        raise custom_errors.InvalidInputError("Text prompt cannot be empty.")

    # bbox_condition validation
    validated_bbox_condition: Optional[List[float]] = None
    if bbox_condition is not None:
        if not isinstance(bbox_condition, list):
            raise custom_errors.ValidationError(
                "Input validation failed: bbox_condition must be a list of floats or None."
            )

        if not all(isinstance(item, (int, float)) for item in bbox_condition):
            raise custom_errors.ValidationError(
                "Input validation failed: bbox_condition items must all be floats."
            )

        if len(bbox_condition) != 3:
            raise custom_errors.InvalidInputError(
                "bbox_condition must be a list of 3 floats."
            )

        validated_bbox_condition = [float(item) for item in bbox_condition]

    # 3. "Submit" Task: Simulate API interaction and prepare job data
    internal_job_id = uuid.uuid4()
    task_uuid_val: Optional[str] = None
    request_id_val: Optional[str] = None
    subscription_key_val: Optional[str] = None
    submission_message: str

    current_mode = hyper3d_status_dict['mode']
    if current_mode == models.Hyper3DMode.MAIN_SITE:
        task_uuid_val = f"task_{uuid.uuid4()}"
        subscription_key_val = f"sub_{uuid.uuid4().hex[:12]}"
        submission_message = f"Hyper3D ({current_mode} Mode) generation task for prompt '{text_prompt}' has been successfully queued."
    elif current_mode == models.Hyper3DMode.FAL_AI:
        request_id_val = f"fal_{uuid.uuid4()}"
        submission_message = f"Hyper3D ({current_mode} Mode) generation task for prompt '{text_prompt}' has been successfully queued."
    else:
        raise custom_errors.ValidationError(
            f"Encountered an unsupported Hyper3D mode: {current_mode}."
        )

    status_val = models.JobOverallStatus.SUCCESS_QUEUED.value

    # 4. Store Job Details in DB
    job_data_dict = {
        "internal_job_id": str(internal_job_id),  # Store as string in the job data dict
        "mode_at_creation": current_mode,
        "text_prompt": text_prompt,
        "bbox_condition": validated_bbox_condition,
        "submission_status": status_val,
        "submission_message": submission_message,
        "task_uuid": task_uuid_val,
        "request_id": request_id_val,
        "subscription_key": subscription_key_val,
        "poll_overall_status": models.JobOverallStatus.PENDING.value,
        "poll_message": "Job status has not been polled yet.",
        "poll_details_specific": None,
        "asset_name_for_import": None,
        "import_status": None,
        "import_message": None,
        "imported_blender_object_id": None,
        "imported_blender_object_name": None,
        "imported_blender_object_type": None,
    }

    try:
        models.Hyper3DJobModel(**job_data_dict)
    except Exception as e:
        raise custom_errors.Hyper3DAPIError(
            f"Failed to create a valid job data structure for Hyper3D task. Details: {e}"
        )

    if 'hyper3d_jobs' not in DB:
        raise custom_errors.ObjectNotFoundError('hyper3d_jobs not found in DB.')

    # Use the uuid.UUID object as the key, consistent with BlenderDB schema
    DB['hyper3d_jobs'][internal_job_id] = job_data_dict

    # 5. Return Response
    response = {
        "status": status_val,
        "message": submission_message,
        "task_uuid": task_uuid_val,
        "request_id": request_id_val,
        "subscription_key": subscription_key_val,
    }

    return GenerateHyper3DModelViaTextResponse(**response).model_dump()


@tool_spec(
    spec={
        'name': 'generate_hyper3d_model_via_images',
        'description': """ Generate 3D asset using Hyper3D by giving images of the wanted asset, and import the generated asset into Blender.
        
        This function generates a 3D asset using Hyper3D by providing images of the
        desired asset, and subsequently imports the generated asset into Blender.
        The 3D asset created comes with built-in materials. The model generated
        has a normalized size, so re-scaling might be beneficial after generation.
        Only one of `input_image_paths` or `input_image_urls` should be provided
        at a time, depending on the current mode of Hyper3D Rodin. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'input_image_paths': {
                    'type': 'array',
                    'description': """ The **absolute** paths of input
                    images. Even if only one image is provided, wrap it into a list.
                    Required if Hyper3D Rodin in MAIN_SITE mode. Defaults to None. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'input_image_urls': {
                    'type': 'array',
                    'description': """ The URLs of input images. Even
                    if only one image is provided, wrap it into a list. Required if
                    Hyper3D Rodin in FAL_AI mode. Defaults to None. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'bbox_condition': {
                    'type': 'array',
                    'description': """ Optional. If given, it has to be a
                    list of ints of length 3. Controls the ratio between
                    [Length, Width, Height] of the model. Defaults to None. """,
                    'items': {
                        'type': 'integer'
                    }
                }
            },
            'required': []
        }
    }
)
def generate_hyper3d_model_via_images(
        input_image_paths: Optional[List[str]] = None,
        input_image_urls: Optional[List[str]] = None,
        bbox_condition: Optional[List[int]] = None  # Type hint aligns with docstring: List[int]
) -> Dict[str, str]:
    """
    Generate 3D asset using Hyper3D by giving images of the wanted asset, and import the generated asset into Blender.

    This function generates a 3D asset using Hyper3D by providing images of the
    desired asset, and subsequently imports the generated asset into Blender.
    The 3D asset created comes with built-in materials. The model generated
    has a normalized size, so re-scaling might be beneficial after generation.
    Only one of `input_image_paths` or `input_image_urls` should be provided
    at a time, depending on the current mode of Hyper3D Rodin.

    Args:
        input_image_paths (Optional[List[str]]): The **absolute** paths of input
            images. Even if only one image is provided, wrap it into a list.
            Required if Hyper3D Rodin in MAIN_SITE mode. Defaults to None.
        input_image_urls (Optional[List[str]]): The URLs of input images. Even
            if only one image is provided, wrap it into a list. Required if
            Hyper3D Rodin in FAL_AI mode. Defaults to None.
        bbox_condition (Optional[List[int]]): Optional. If given, it has to be a
            list of ints of length 3. Controls the ratio between
            [Length, Width, Height] of the model. Defaults to None.

    Returns:
        Dict[str, str]: A dictionary containing details about the submitted model
            generation task. It includes the following keys:
            - status (str): 'success_queued' if the generation task was
                successfully submitted, or 'failure' if submission failed.
            - message (str): A descriptive message about the submission outcome.
            - task_uuid (Optional[str]): The task UUID (for MAIN_SITE mode, if
                applicable) assigned to the generation job. Used for polling
                status and importing.
            - request_id (Optional[str]): The request ID (for FAL_AI mode, if
                applicable) assigned to the generation job. Used for polling
                status and importing.
            - subscription_key (Optional[str]): The subscription key (for MAIN_SITE
                mode, if applicable) related to the generation job. May be
                needed for polling.

    Raises:
        InvalidInputError: If `input_image_paths` or `input_image_urls` are
            invalid (e.g., not a list, incorrect content type),
            `bbox_condition` is malformed (e.g., not a list of 3 integers),
            or image inputs are conflicting (both `input_image_paths` and
            `input_image_urls` provided) or missing when one is required
            based on the Hyper3D mode.
        FileNotFoundError: If any of the specified `input_image_paths` do not
            exist when local image paths are provided.
        ObjectNotFoundError: If Hyper3D Rodin integration is not enabled or
            not configured correctly in the host application (e.g., Blender).
        ValidationError: If Hyper3D Rodin mode is not properly configured.
    """
    # Check Hyper3D service status from DB
    hyper3d_status = DB.get('hyper3d_service_status')
    if not (hyper3d_status and hyper3d_status.get('is_enabled')):
        raise custom_errors.ObjectNotFoundError("Hyper3D Rodin configuration is missing or invalid.")

    current_mode = hyper3d_status.get('mode')

    # Validate that only one image input type is provided
    if input_image_paths is not None and input_image_urls is not None:
        raise custom_errors.InvalidInputError(
            "Only one of `input_image_paths` or `input_image_urls` should be provided."
        )

    # Validate inputs based on the current Hyper3D mode
    if current_mode == models.Hyper3DMode.MAIN_SITE:
        if input_image_urls is not None:
            raise custom_errors.InvalidInputError(
                "`input_image_urls` should not be provided in MAIN_SITE mode. Use `input_image_paths` instead."
            )
        if input_image_paths is None:
            raise custom_errors.InvalidInputError(
                "`input_image_paths` is required for MAIN_SITE mode."
            )
        if not isinstance(input_image_paths, list):
            raise custom_errors.InvalidInputError(
                "`input_image_paths` must be a list of strings."
            )
        if not input_image_paths:
            raise custom_errors.InvalidInputError(
                "`input_image_paths` cannot be an empty list."
            )
        if not all(isinstance(path_val, str) for path_val in input_image_paths):
            raise custom_errors.InvalidInputError(
                "All items in `input_image_paths` must be strings."
            )
        for path_val in input_image_paths:
            if not os.path.exists(path_val):
                raise FileNotFoundError(f"Input image path '{path_val}' not found.")

    elif current_mode == models.Hyper3DMode.FAL_AI:
        if input_image_paths is not None:
            raise custom_errors.InvalidInputError(
                "`input_image_paths` should not be provided in FAL_AI mode. Use `input_image_urls` instead."
            )
        if input_image_urls is None:
            raise custom_errors.InvalidInputError(
                "`input_image_urls` is required for FAL_AI mode."
            )
        if not isinstance(input_image_urls, list):
            raise custom_errors.InvalidInputError(
                "`input_image_urls` must be a list of strings."
            )
        if not input_image_urls:
            raise custom_errors.InvalidInputError(
                "`input_image_urls` cannot be an empty list."
            )
        if not all(isinstance(url_val, str) for url_val in input_image_urls):
            raise custom_errors.InvalidInputError(
                "All items in `input_image_urls` must be strings."
            )

    # Validate bbox_condition if provided
    processed_bbox_condition: Optional[List[float]] = None
    if bbox_condition is not None:
        if not isinstance(bbox_condition, list):
            raise custom_errors.InvalidInputError("`bbox_condition` must be a list of 3 integers.")
        if len(bbox_condition) != 3:
            raise custom_errors.InvalidInputError(
                "`bbox_condition` must be a list of 3 integers."
            )
        if not all(isinstance(item, int) for item in bbox_condition):
            raise custom_errors.InvalidInputError(
                "All items in `bbox_condition` must be integers."
            )
        # Convert to float for storage/use, as Hyper3DJobModel.bbox_condition is List[float]
        processed_bbox_condition = [float(item) for item in bbox_condition]

    # All validations passed, proceed to simulate API submission and create job entry
    internal_job_id = uuid.uuid4()
    generated_task_uuid: Optional[str] = None
    generated_request_id: Optional[str] = None
    generated_subscription_key: Optional[str] = None

    if current_mode == models.Hyper3DMode.MAIN_SITE:
        generated_task_uuid = str(uuid.uuid4())
        generated_subscription_key = str(uuid.uuid4())
    elif current_mode == models.Hyper3DMode.FAL_AI:
        generated_request_id = str(uuid.uuid4())
    else:
        raise custom_errors.ValidationError(
            f"Encountered an unsupported Hyper3D mode: {current_mode}."
        )

    job_data = {
        "internal_job_id": str(internal_job_id),
        "mode_at_creation": current_mode,
        "text_prompt": None,
        "input_image_paths": input_image_paths,
        "input_image_urls": input_image_urls,
        "bbox_condition": processed_bbox_condition,
        "submission_status": models.JobOverallStatus.SUCCESS_QUEUED.value,
        "submission_message": "Hyper3D model generation task successfully submitted.",
        "task_uuid": generated_task_uuid,
        "request_id": generated_request_id,
        "subscription_key": generated_subscription_key,
        "poll_overall_status": models.JobOverallStatus.PENDING.value,
        "poll_message": "Job status not yet polled.",
        "poll_details_specific": None,
        "asset_name_for_import": None,
        "import_status": None,
        "import_message": None,
        "imported_blender_object_id": None,
        "imported_blender_object_name": None,
        "imported_blender_object_type": None,
    }

    DB['hyper3d_jobs'][str(internal_job_id)] = models.Hyper3DJobModel(**job_data).model_dump()

    return {
        "status": "success_queued",
        "message": "Hyper3D model generation task successfully submitted.",
        "task_uuid": generated_task_uuid,
        "request_id": generated_request_id,
        "subscription_key": generated_subscription_key,
    }


@tool_spec(
    spec={
        'name': 'poll_hyper3d_rodin_job_status',
        'description': """ Check if the Hyper3D Rodin generation task is completed.
        
        This function checks the status of a Hyper3D Rodin generation task. Its behavior
        and the interpretation of status depend on the operational mode, inferred from
        which identifier (`subscription_key` or `request_id`) is provided.
        
        For Hyper3D Rodin mode MAIN_SITE (when `subscription_key` is provided):
        The function assesses completion based on a list of statuses related to the job.
        The task is considered done if all these statuses are "Done". If "Failed"
        appears among the statuses, the generating process has failed. This function
        is designed for polling; callers should only proceed if the statuses are
        finally determined (e.g., "Done" or "Canceled").
        
        For Hyper3D Rodin mode FAL_AI (when `request_id` is provided):
        The function assesses completion based on the overall generation task status.
        The task is considered done if this status is "COMPLETED". The task is
        in progress if the status is "IN_PROGRESS". If a status other than
        "COMPLETED", "IN_PROGRESS", or "IN_QUEUE" is encountered, the generating
        process might have failed. This function is designed for polling; callers
        should only proceed if the status is finally determined (e.g., "COMPLETED"
        or a recognized failed state). """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription_key': {
                    'type': 'string',
                    'description': """ The subscription_key given in the generate model step,
                    used for polling in MAIN_SITE mode. Defaults to None. """
                },
                'request_id': {
                    'type': 'string',
                    'description': """ The request_id given in the generate model step,
                    used for polling in FAL_AI mode. Defaults to None. """
                }
            },
            'required': []
        }
    }
)
def poll_rodin_job_status(subscription_key: Optional[str] = None, request_id: Optional[str] = None) -> Dict[str, Union[str, bool, List[str]]]:
    """
    Check if the Hyper3D Rodin generation task is completed.

    This function checks the status of a Hyper3D Rodin generation task. Its behavior
    and the interpretation of status depend on the operational mode, inferred from
    which identifier (`subscription_key` or `request_id`) is provided.

    For Hyper3D Rodin mode MAIN_SITE (when `subscription_key` is provided):
    The function assesses completion based on a list of statuses related to the job.
    The task is considered done if all these statuses are "Done". If "Failed"
    appears among the statuses, the generating process has failed. This function
    is designed for polling; callers should only proceed if the statuses are
    finally determined (e.g., "Done" or "Canceled").

    For Hyper3D Rodin mode FAL_AI (when `request_id` is provided):
    The function assesses completion based on the overall generation task status.
    The task is considered done if this status is "COMPLETED". The task is
    in progress if the status is "IN_PROGRESS". If a status other than
    "COMPLETED", "IN_PROGRESS", or "IN_QUEUE" is encountered, the generating
    process might have failed. This function is designed for polling; callers
    should only proceed if the status is finally determined (e.g., "COMPLETED"
    or a recognized failed state).

    Args:
        subscription_key (Optional[str]): The subscription_key given in the generate model step,
            used for polling in MAIN_SITE mode. Defaults to None.
        request_id (Optional[str]): The request_id given in the generate model step,
            used for polling in FAL_AI mode. Defaults to None.

    Returns:
        Dict[str, Union[str, bool, List[str]]]: A dictionary detailing the current status of the Hyper3D Rodin generation job.
        It contains the following keys:
            - mode_queried (str): Indicates which mode's identifier was used for polling ('MAIN_SITE' or 'FAL_AI').
            - overall_status (str): A summarized status of the job (e.g., 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELED').
            - is_completed (bool): True if the job has reached a terminal state (completed successfully or failed/canceled).
            - is_successful (Optional[bool]): True if the job completed successfully, False if it failed or was canceled; None if not yet completed.
            - message (str): A descriptive message summarizing the current status.
            - details (Optional[Union[List[str], str]]): Mode-specific status details. For MAIN_SITE mode, this is typically a List[str]
                of statuses for individual components of the job (e.g., ["Done", "Processing"]).
                For FAL_AI mode, this is typically a str representing the overall job state
                (e.g., "COMPLETED", "IN_PROGRESS").

    Raises:
        InvalidInputError: If neither subscription_key (for MAIN_SITE mode) nor request_id (for FAL_AI mode)
            is provided, or if both are provided, or if an identifier is invalid (e.g. empty).
        JobNotFoundError: If the job corresponding to the provided key/ID is not found, has expired,
            or does not match the inferred mode.
        InvalidStateError: If the operational mode is not supported.
    """

    # 1. Validate inputs and determine operational mode and identifier
    mode_queried_enum: models.Hyper3DMode = models.Hyper3DMode.MAIN_SITE
    job_identifier_value: str = subscription_key
    job_identifier_field_name: str = 'subscription_key'

    if subscription_key is not None and request_id is not None:
        raise custom_errors.InvalidInputError(
            "Both subscription_key and request_id were provided. Please provide only one."
        )
    elif subscription_key is not None:
        if not isinstance(subscription_key, str) or not subscription_key: # Check for empty string
            raise custom_errors.InvalidInputError("Subscription key provided is invalid.")
    elif request_id is not None:
        if not isinstance(request_id, str) or not request_id: # Check for empty string
            raise custom_errors.InvalidInputError("Request ID provided is invalid.")
        mode_queried_enum = models.Hyper3DMode.FAL_AI
        job_identifier_value = request_id
        job_identifier_field_name = 'request_id'
    else:
        raise custom_errors.InvalidInputError(
            "Neither subscription_key (for MAIN_SITE mode) nor request_id (for FAL_AI mode) was provided."
        )

    # 2. Find the job in the DB
    found_job_data = None
    hyper3d_jobs_in_db = DB.get('hyper3d_jobs', {})

    for job_data_dict in hyper3d_jobs_in_db.values():
        if job_data_dict.get(job_identifier_field_name) == job_identifier_value:
            found_job_data = job_data_dict
            break

    job_not_found_or_mismatch_msg = f"Job not found for {job_identifier_field_name} '{job_identifier_value}' or mode mismatch."

    if not found_job_data:
        raise custom_errors.JobNotFoundError(job_not_found_or_mismatch_msg)

    job_mode_at_creation_str = found_job_data.get('mode_at_creation')
    if job_mode_at_creation_str != mode_queried_enum.value:
        raise custom_errors.JobNotFoundError(job_not_found_or_mismatch_msg)

    # 3. Interpret status based on the operational mode and job's specific details
    job_specific_details: Optional[Union[List[str], str]] = found_job_data.get('poll_details_specific')

    derived_overall_status: models.JobOverallStatus = models.JobOverallStatus.PENDING
    is_job_completed: bool = False
    is_job_successful: Optional[bool] = None
    status_message: str

    if mode_queried_enum == models.Hyper3DMode.MAIN_SITE:
        if not job_specific_details:
            status_message = f"Hyper3D Rodin job ({mode_queried_enum.value}) is pending as task details are unavailable."
        else:
            component_statuses: List[str] = job_specific_details
            failed_state, canceled_state, done_state = "Failed", "Canceled", "Done"

            if failed_state in component_statuses:
                derived_overall_status = models.JobOverallStatus.FAILED
                is_job_completed = True
                status_message = f"Hyper3D Rodin job ({mode_queried_enum.value}) failed."
            elif canceled_state in component_statuses:
                derived_overall_status = models.JobOverallStatus.CANCELED
                is_job_completed = True
                status_message = f"Hyper3D Rodin job ({mode_queried_enum.value}) was canceled."
            elif all(status == done_state for status in component_statuses):
                derived_overall_status = models.JobOverallStatus.COMPLETED
                is_job_completed = True
                is_job_successful = True
                status_message = f"Hyper3D Rodin job ({mode_queried_enum.value}) completed successfully."
            else:
                derived_overall_status = models.JobOverallStatus.IN_PROGRESS
                status_message = f"Hyper3D Rodin job ({mode_queried_enum.value}) is still in progress."

    elif mode_queried_enum == models.Hyper3DMode.FAL_AI:
        if job_specific_details is None:
            status_message = f"Hyper3D Rodin job ({mode_queried_enum.value}) is pending as status detail is unavailable."
        else:
            fal_api_status_str: str = job_specific_details

            if fal_api_status_str == "COMPLETED":
                derived_overall_status = models.JobOverallStatus.COMPLETED
                is_job_completed = True
                is_job_successful = True
                status_message = f"Hyper3D Rodin job ({mode_queried_enum.value}) completed successfully."
            elif fal_api_status_str == "IN_PROGRESS":
                derived_overall_status = models.JobOverallStatus.IN_PROGRESS
                status_message = f"Hyper3D Rodin job ({mode_queried_enum.value}) is in progress."
            elif fal_api_status_str == "IN_QUEUE":
                derived_overall_status = models.JobOverallStatus.PENDING
                status_message = f"Hyper3D Rodin job ({mode_queried_enum.value}) is queued."
            else:
                derived_overall_status = models.JobOverallStatus.FAILED
                is_job_completed = True
                status_message = f"Hyper3D Rodin job ({mode_queried_enum.value}) failed or was canceled."
    else:
        raise custom_errors.InvalidStateError(
            f"Internal error: Unknown operational mode '{mode_queried_enum.value}' encountered.")

    # 4. Construct and return the response dictionary
    return {
        "mode_queried": mode_queried_enum.value,
        "overall_status": derived_overall_status.value,
        "is_completed": is_job_completed,
        "is_successful": is_job_successful,
        "message": status_message,
        "details": job_specific_details
    }


@tool_spec(
    spec={
        'name': 'import_hyper3d_generated_asset',
        'description': """ Import the asset generated by Hyper3D Rodin after the generation task is completed.
        
        This function imports an asset generated by Hyper3D Rodin. It requires specific identifiers
        (`task_uuid` or `request_id`) based on the Hyper3D Rodin mode used for generation.
        Only one of these identifiers should be provided. The function's output details
        the success of the import operation. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of the object in scene.'
                },
                'task_uuid': {
                    'type': 'string',
                    'description': 'For Hyper3D Rodin mode MAIN_SITE: The task_uuid given in the generate model step. Defaults to "null".'
                },
                'request_id': {
                    'type': 'string',
                    'description': 'For Hyper3D Rodin mode FAL_AI: The request_id given in the generate model step. Defaults to "null".'
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def import_generated_asset(name: str, task_uuid: str = "null", request_id: str = "null") -> Dict[str, str]:
    """
    Import the asset generated by Hyper3D Rodin after the generation task is completed.

    This function imports an asset generated by Hyper3D Rodin. It requires specific identifiers
    (`task_uuid` or `request_id`) based on the Hyper3D Rodin mode used for generation.
    Only one of these identifiers should be provided. The function's output details
    the success of the import operation.

    Args:
        name (str): The name of the object in scene.
        task_uuid (str): For Hyper3D Rodin mode MAIN_SITE: The task_uuid given in the generate model step. Defaults to "null".
        request_id (str): For Hyper3D Rodin mode FAL_AI: The request_id given in the generate model step. Defaults to "null".

    Returns:
        Dict[str, str]: A dictionary indicating the result of importing the generated Hyper3D asset. It includes the following keys:
            - status (str): 'success' or 'failure'.
            - message (str): A descriptive message about the import operation.
            - asset_name_in_blender (Optional[str]): The actual name assigned to the imported object in Blender if successful (may differ from input `name` due to uniqueness constraints).
            - blender_object_type (Optional[str]): The type of object created in Blender (e.g., 'MESH').

    Raises:
        InvalidInputError: If required parameters (name and one of task_uuid/request_id appropriate for the mode) are missing, conflicting, or malformed.
        AssetNotReadyError: If the asset generation is not yet completed or has failed, and thus cannot be imported.
        JobNotFoundError: If the job corresponding to the provided task_uuid/request_id is not found or asset data is unavailable.
        BlenderImportError: If there's an issue importing the asset into Blender (e.g., file format issue, Blender internal error).
        ValidationError: If input arguments fail validation.
        SceneNotFoundError: If Scene does not exist.
        DuplicateNameError: If duplicate name found.
    """
    args: ImportGeneratedAssetArguments

    try:
        args = ImportGeneratedAssetArguments(name=name, task_uuid=task_uuid, request_id=request_id)
    except PydanticValidationError as e:
        primary_error_message = "Input validation failed."
        if e.errors():
            primary_error_message = e.errors()[0].get('msg', primary_error_message)
        raise custom_errors.ValidationError(primary_error_message)

    if not args.name:
        raise custom_errors.InvalidInputError("Name cannot be empty.")

    is_task_uuid_effectively_provided = args.task_uuid != "null"
    is_request_id_effectively_provided = args.request_id != "null"

    if not is_task_uuid_effectively_provided and not is_request_id_effectively_provided:
        raise custom_errors.InvalidInputError("Either task_uuid or request_id must be provided.")

    if is_task_uuid_effectively_provided and is_request_id_effectively_provided:
        raise custom_errors.InvalidInputError("Either task_uuid or request_id must be provided, but not both.")

    if is_task_uuid_effectively_provided and args.task_uuid == "":
        raise custom_errors.InvalidInputError("Provided task_uuid cannot be empty.")

    if is_request_id_effectively_provided and args.request_id == "":
        raise custom_errors.InvalidInputError("Provided request_id cannot be empty.")

    search_key_attr: str
    search_value: str
    identifier_desc_for_error: str

    if is_task_uuid_effectively_provided:
        search_key_attr = 'task_uuid'
        search_value = args.task_uuid
        identifier_desc_for_error = f"job with task_uuid '{args.task_uuid}'"
    else:
        search_key_attr = 'request_id'
        search_value = args.request_id
        identifier_desc_for_error = f"job with request_id '{args.request_id}'"

    target_job_internal_id: Optional[str] = None
    job_dict_in_db = None

    hyper3d_jobs_db = DB.get('hyper3d_jobs', {})
    for job_id_str, current_job_dict_ref in hyper3d_jobs_db.items():
        if current_job_dict_ref.get(search_key_attr) == search_value:
            target_job_internal_id = job_id_str
            job_dict_in_db = current_job_dict_ref
            break

    if not (target_job_internal_id and job_dict_in_db):
        raise custom_errors.JobNotFoundError(f"Job with {search_key_attr} '{search_value}' not found.")

    actual_job_mode = job_dict_in_db.get('mode_at_creation')
    if is_task_uuid_effectively_provided and actual_job_mode != models.Hyper3DMode.MAIN_SITE.value:
        msg = (f"Job found with task_uuid '{args.task_uuid}' was created in {actual_job_mode} mode, "
               f"which is inconsistent for task_uuid identifier.")
        raise custom_errors.InvalidInputError(msg)

    if is_request_id_effectively_provided and actual_job_mode != models.Hyper3DMode.FAL_AI.value:
        msg = (f"Job found with request_id '{args.request_id}' was created in {actual_job_mode} mode, "
               f"which is inconsistent for request_id identifier.")
        raise custom_errors.InvalidInputError(msg)

    try:
        job_status_view = utils.get_hyper3d_job_data_dict(target_job_internal_id)
    except custom_errors.JobNotFoundError:
        err_msg = (
            f"Hyper3D job with internal ID '{target_job_internal_id}' was found but could not be retrieved for status check. "
            "Possible data inconsistency.")
        update_job_import_failure(job_dict_in_db, err_msg)
        raise custom_errors.JobNotFoundError(err_msg)

    current_poll_status = job_status_view.get('poll_overall_status', 'UNKNOWN')
    if not job_status_view.get('is_completed'):
        msg = (f"Asset generation for {identifier_desc_for_error} is not complete. "
               f"Current status: {current_poll_status}.")
        update_job_import_failure(job_dict_in_db, msg)
        raise custom_errors.AssetNotReadyError(msg)

    if not job_status_view.get('is_successful'):
        msg = (f"Asset generation for {identifier_desc_for_error} failed or was canceled. "
               f"Current status: {current_poll_status}.")
        update_job_import_failure(job_dict_in_db, msg)
        raise custom_errors.AssetNotReadyError(msg)

    generated_asset_name_in_job = job_dict_in_db.get('asset_name_for_import')
    if not generated_asset_name_in_job:
        msg = "Failed to import asset into Blender: Essential asset information missing from job details."
        update_job_import_failure(job_dict_in_db, msg)
        raise custom_errors.BlenderImportError(msg)

    current_scene_dict = DB.get('current_scene')
    if not current_scene_dict:
        msg = "Failed to import asset: No current scene is active in the system."
        update_job_import_failure(job_dict_in_db, msg)
        raise custom_errors.BlenderImportError(msg)

    current_scene_name = current_scene_dict.get('name')
    if not current_scene_name:
        msg = "Failed to import asset: The current active scene has no name."
        update_job_import_failure(job_dict_in_db, msg)
        raise custom_errors.BlenderImportError(msg)

    scene_objects_dict = current_scene_dict.get('objects', {})
    actual_blender_name = args.name
    if actual_blender_name in scene_objects_dict:
        counter = 1
        while True:
            actual_blender_name = f"{args.name}.{counter:03d}"
            if actual_blender_name not in scene_objects_dict:
                break
            counter += 1
            if counter > 999:
                msg = (
                    f"Failed to generate a unique name for '{args.name}' in scene '{current_scene_name}' after 999 attempts. "
                    "There may be too many objects with similar names.")
                update_job_import_failure(job_dict_in_db, msg)
                raise custom_errors.BlenderImportError(msg)

    new_blender_object_id = str(uuid.uuid4())
    new_blender_object_data = {
        "id": new_blender_object_id,
        "name": actual_blender_name,
        "type": models.BlenderObjectType.MESH.value,
        "location": [0.0, 0.0, 0.0],
        "rotation_euler": [0.0, 0.0, 0.0],
        "scale": [1.0, 1.0, 1.0],
        "dimensions": [2.0, 2.0, 2.0],
        "material_names": [],
        "is_visible": True,
        "is_renderable": True,
        "parent_name": None,
        "vertex_count": None,
        "edge_count": None,
        "face_count": None,
    }

    try:
        utils.add_object_to_scene(current_scene_name, new_blender_object_data)
    except (custom_errors.DuplicateNameError, custom_errors.SceneNotFoundError) as e:
        msg = f"Failed to import asset due to an error adding to scene: {str(e)}"
        update_job_import_failure(job_dict_in_db, msg)
        raise custom_errors.BlenderImportError(msg)

    success_message = (f"Successfully imported asset '{args.name}'. It is named '{actual_blender_name}' "
                       f"in Blender and is of type '{new_blender_object_data['type']}'.")

    if job_dict_in_db:
        job_dict_in_db['import_status'] = models.ExecutionStatus.SUCCESS.value
        job_dict_in_db['import_message'] = success_message
        job_dict_in_db['imported_blender_object_id'] = new_blender_object_id
        job_dict_in_db['imported_blender_object_name'] = actual_blender_name
        job_dict_in_db['imported_blender_object_type'] = new_blender_object_data['type']

    response = {
        "status": "success",
        "message": success_message,
        "asset_name_in_blender": actual_blender_name,
        "blender_object_type": new_blender_object_data['type']
    }

    return ImportGeneratedAssetResponse(**response).model_dump()

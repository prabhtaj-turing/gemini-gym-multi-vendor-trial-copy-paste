
from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, List
from .SimulationEngine import custom_errors, utils, models
from .SimulationEngine.db import DB
from datetime import datetime
from .SimulationEngine.models import (
    Project, 
    CreateProjectArgs, 
    NON_PAUSABLE_STATUSES, 
    ProjectStatus, 
    GetProjectInput, 
    ProjectResponse,
    RestoreProjectResponse
)
import datetime as dt
from typing import Optional, Dict, Any

from pydantic import ValidationError as PydanticValidationError


@tool_spec(
    spec={
        'name': 'create_project',
        'description': """ Creates a new Supabase project.
        
        Creates a new Supabase project. Always ask the user which organization to create the project in.
        The project can take a few minutes to initialize - use `get_project` to check the status. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of the project.'
                },
                'organization_id': {
                    'type': 'string',
                    'description': 'The ID of the organization to create the project in.'
                },
                'confirm_cost_id': {
                    'type': 'string',
                    'description': 'The cost confirmation ID. Call `confirm_cost` first.'
                },
                'region': {
                    'type': 'string',
                    'description': """ The region to create the project in. Defaults to the closest region.
                    Possible values: "us-west-1", "us-east-1", "us-east-2", "ca-central-1",
                    "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "eu-central-2",
                    "eu-north-1", "ap-south-1", "ap-southeast-1", "ap-northeast-1",
                    "ap-northeast-2", "ap-southeast-2", "sa-east-1". Defaults to None. """
                }
            },
            'required': [
                'name',
                'organization_id',
                'confirm_cost_id'
            ]
        }
    }
)
def create_project(name: str, organization_id: str, confirm_cost_id: str, region: Optional[str] = None) -> Dict[str, Any]:
    """Creates a new Supabase project.

    Creates a new Supabase project. Always ask the user which organization to create the project in.
    The project can take a few minutes to initialize - use `get_project` to check the status.

    Args:
        name (str): The name of the project.
        organization_id (str): The ID of the organization to create the project in.
        confirm_cost_id (str): The cost confirmation ID. Call `confirm_cost` first.
        region (Optional[str]): The region to create the project in. Defaults to the closest region.
            Possible values: "us-west-1", "us-east-1", "us-east-2", "ca-central-1",
            "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "eu-central-2",
            "eu-north-1", "ap-south-1", "ap-southeast-1", "ap-northeast-1",
            "ap-northeast-2", "ap-southeast-2", "sa-east-1". Defaults to None.

    Returns:
        Dict[str, Any]: Information about the newly created project. Includes the following keys:
            id (str): The unique identifier for the new project.
            name (str): The name of the new project.
            organization_id (str): The ID of the organization the project was created in.
            region (str): The region where the project is being created.
            status (str): The initial status of the project (e.g., 'CREATING', 'INITIALIZING').
            created_at (str): ISO 8601 timestamp of when the project creation was initiated.

    Raises:
        InvalidInputError: If required inputs (name, organization_id, confirm_cost_id) are empty.
        NotFoundError: If the organization_id does not exist.
        CostConfirmationError: If the confirm_cost_id is invalid, expired, already used, or does not match the intended operation.
        PydanticValidationError: If input arguments fail type validation or enum constraints.
    """
    try:
        validated_args = CreateProjectArgs(
            name=name,
            organization_id=organization_id,
            confirm_cost_id=confirm_cost_id,
            region=region
        )
        # Update local variables from validated args. Pydantic might coerce, but for these types, it's mainly validation.
        name = validated_args.name
        organization_id = validated_args.organization_id
        confirm_cost_id = validated_args.confirm_cost_id
        # Store the validated region (which could be None or a valid region string)
        validated_region_arg = validated_args.region

    except PydanticValidationError as e:
        raise

    # Validate required inputs for non-emptiness (after type validation by Pydantic)
    if not name: # Empty string check
        raise custom_errors.InvalidInputError("Project name cannot be empty.")
    if not organization_id: # Empty string check
        raise custom_errors.InvalidInputError("Organization ID cannot be empty.")
    if not confirm_cost_id: # Empty string check
        raise custom_errors.InvalidInputError("Confirmation cost ID cannot be empty.")

    # Validate organization_id: Check if the organization exists
    organization_entity = utils.get_entity_by_id_from_db(DB, "organizations", organization_id)
    if not organization_entity:
        raise custom_errors.NotFoundError(f"Organization with ID '{organization_id}' not found.")

    # Validate confirm_cost_id:
    if confirm_cost_id not in DB["costs"]:
        raise custom_errors.CostConfirmationError(
            f"Cost confirmation ID '{confirm_cost_id}' is invalid or not found."
        )
    
    cost_details = DB["costs"][confirm_cost_id]
    if cost_details.get("type") != "project":
        raise custom_errors.CostConfirmationError(
            f"Cost confirmation '{confirm_cost_id}' is not for a project creation."
        )

    # Determine the project region using the validated region argument
    project_region: str
    if validated_region_arg is None:
        project_region = utils.PROJECT_CREATION_DEFAULTS["region"]
    else:
        # validated_region_arg is already confirmed to be a valid region string by Pydantic
        project_region = validated_region_arg
    
    project_id = utils.generate_unique_id(prefix="proj_")
    current_time_utc = dt.datetime.now(dt.timezone.utc)

    new_project_db_entry = {
        "id": project_id,
        "name": name,
        "organization_id": organization_id,
        "region": project_region,
        "status": utils.PROJECT_CREATION_DEFAULTS["status"],
        "created_at": current_time_utc.isoformat(),
        "version": None,
    }

    DB["projects"].append(new_project_db_entry)
    del DB["costs"][confirm_cost_id]
    
    response_data = {
        "id": project_id,
        "name": name,
        "organization_id": organization_id,
        "region": project_region,
        "status": utils.PROJECT_CREATION_DEFAULTS["status"],
        "created_at": current_time_utc.isoformat(),
    }

    return response_data

@tool_spec(
    spec={
        'name': 'get_anon_key',
        'description': """ Gets the anonymous API key for a project.
        
        This function gets the anonymous API key for a project. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The ID of the project.'
                }
            },
            'required': [
                'project_id'
            ]
        }
    }
)
def get_anon_key(project_id: str) -> Dict[str, Any]:
    """Gets the anonymous API key for a project.

    This function gets the anonymous API key for a project.

    Args:
        project_id (str): The ID of the project.

    Returns:
        Dict[str, Any]: A dictionary containing the anonymous API key for the project, with the following keys:
            project_id (str): The ID of the project.
            anon_key (str): The anonymous (public) API key.

    Raises:
        NotFoundError: If the project_id does not exist.
        ValidationError: If input arguments fail validation.
    """
    if not project_id or (isinstance(project_id, str) and not project_id.strip()):
        raise custom_errors.ValidationError('The id parameter can not be null or empty')

    if not isinstance(project_id, str):
        raise custom_errors.ValidationError('id must be string type')
    
    # Check if project exists
    projects = utils.get_main_entities(DB, "projects")
    project = utils.get_entity_by_id(projects, project_id)
    if not project:
        raise custom_errors.NotFoundError(f'Project not found: {project_id}')
    
    # Get the anon key (we don't check project status - inactive projects can still have valid keys)
    anon_key = utils.get_entity_from_db(DB, "project_anon_keys", project_id)
    
    if anon_key is None:
        raise custom_errors.ResourceNotFoundError(f'No anon key found for project: {project_id}')

    return {
        "project_id": project_id,
        "anon_key": anon_key,
    }

@tool_spec(
    spec={
        'name': 'pause_project',
        'description': """ Pauses a Supabase project.
        
        Pauses a Supabase project. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The ID of the project to pause.'
                }
            },
            'required': [
                'project_id'
            ]
        }
    }
)
def pause_project(project_id: str) -> Dict[str, Any]:
    """Pauses a Supabase project.

    Pauses a Supabase project.

    Args:
        project_id (str): The ID of the project to pause.

    Returns:
        Dict[str, Any]: A dictionary detailing the outcome of the pause operation. Keys:
            project_id (str): The ID of the project that was targeted for pausing.
            status (str): The resulting status of the project after the pause request (e.g., 'PAUSING', 'INACTIVE').
            message (str): A human-readable message providing details about the pause operation outcome.

    Raises:
        NotFoundError: If the project_id does not exist.
        OperationNotPermittedError: If the project cannot be paused (e.g., already paused, on a free plan that doesn't support pausing, or in an incompatible state).
        ValidationError: If input arguments fail validation.
    """
    if not project_id or (isinstance(project_id, str) and not project_id.strip()):
        raise custom_errors.ValidationError('The id parameter can not be null or empty')

    if not isinstance(project_id, str):
        raise custom_errors.ValidationError('id must be string type')

    # Check if project exists
    projects = utils.get_main_entities(DB, "projects")
    project = utils.get_entity_by_id(projects, project_id)
    if not project:
        raise custom_errors.NotFoundError(f'Project not found: {project_id}')
    
    # Check if project can be paused
    if project["status"] in NON_PAUSABLE_STATUSES:
        raise custom_errors.OperationNotPermittedError(f"Project in {project['status']} status cannot be paused")
    
    # Update project status to INACTIVE, reflects in db because the dictionary is by reference
    project["status"] = ProjectStatus.INACTIVE.value
    
    # Return the pause operation result
    return {
        "project_id": project_id,
        "status": project["status"],
        "message": f"Project {project_id} has been paused successfully"
    }

@tool_spec(
    spec={
        'name': 'get_project_url',
        'description': """ Gets the API URL for a project.
        
        This function gets the API URL for a project. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the project.'
                }
            },
            'required': [
                'project_id'
            ]
        }
    }
)
def get_project_url(project_id: str) -> Dict[str, Any]:
    """Gets the API URL for a project.

    This function gets the API URL for a project.

    Args:
        project_id (str): The unique identifier of the project.

    Returns:
        Dict[str, Any]: A dictionary containing information for accessing the project's API. 
                        It includes 'project_id' (str) and 'api_url' (Optional[str]).
                        'api_url' will be None if the project exists but has no URL configured.

    Raises:
        NotFoundError: If the project_id does not exist.
        ValidationError: If project_id is not a string.
    """
    # Validate that project_id is a string.
    if not isinstance(project_id, str):
        raise custom_errors.ValidationError("Input validation failed: project_id must be a string.")

    # Retrieve the project from the database using the helper utility.
    # utils.get_entity_by_id expects project_id to be a string as per its type hint.
    project = utils.get_entity_by_id(DB['projects'], project_id)

    # If the project does not exist, raise NotFoundError.
    if project is None:
        raise custom_errors.NotFoundError(f"Project with ID '{project_id}' not found.")


    # Retrieve the API URL from its storage location in DB.
    api_url = DB['project_urls'].get(project_id)

    # If the project exists but its URL is not recorded, api_url will be None.
    # The function returns this information rather than raising an error,
    # aligning with a strict interpretation of NotFoundError being only for non-existent projects.
    
    return {
        "project_id": project_id,
        "api_url": api_url, # api_url can be None here
    }


@tool_spec(
    spec={
        'name': 'list_projects',
        'description': """ Lists all Supabase projects for the user.
        
        This function lists all Supabase projects for the user. It helps discover
        the project ID of the project that the user is working on. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def list_projects() -> List[Dict[str, str]]:
    """Lists all Supabase projects for the user.

    This function lists all Supabase projects for the user. It helps discover
    the project ID of the project that the user is working on.

    Returns:
        List[Dict[str, str]]: A list of Supabase project dictionaries. Each dictionary
            contains:
            id (str): The unique identifier for the project (project ID).
            name (str): The name of the project.
            organization_id (str): The ID of the organization the project
                                   belongs to.
            region (str): The region where the project is hosted.
            status (str): The current status of the project (e.g., 'ACTIVE_HEALTHY',
                          'INACTIVE', 'COMING_UP').
            created_at (str): ISO 8601 timestamp of when the project was
                              created.
    """
    # Retrieve all project data from the DB.
    all_projects_data: List[Dict[str, str]] = utils.get_main_entities(DB, "projects")
    
    formatted_projects: List[Dict[str, str]] = []
    
    for project_data in all_projects_data:
        # The 'created_at' in DB should already be an ISO string
        created_at_iso_string: str = project_data["created_at"]

        # Construct the dictionary for the current project with the specified fields.
        # Direct dictionary access (e.g., project_data["id"]) is used, assuming
        # data integrity as per the schema.
        project_info: Dict[str, str] = {
            "id": project_data["id"],
            "name": project_data["name"],
            "organization_id": project_data["organization_id"],
            "region": project_data["region"],
            # 'status' is expected to be a string (e.g., "ACTIVE_HEALTHY")
            # as the ProjectStatus enum in the schema inherits from str.
            "status": project_data["status"],
            "created_at": created_at_iso_string,
        }

        formatted_projects.append(project_info)
        
    return formatted_projects


@tool_spec(
    spec={
        'name': 'generate_typescript_types',
        'description': """ Generates TypeScript types for a project.
        
        This function generates TypeScript type definitions for a project, identified
        by its `project_id`. It processes the project information to produce a
        string containing the TypeScript types. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The ID of the project.'
                }
            },
            'required': [
                'project_id'
            ]
        }
    }
)
def generate_typescript_types(project_id: str) -> Dict[str, Any]:
    """Generates TypeScript types for a project.

    This function generates TypeScript type definitions for a project, identified
    by its `project_id`. It processes the project information to produce a
    string containing the TypeScript types.

    Args:
        project_id (str): The ID of the project.

    Returns:
        Dict[str, Any]: A dictionary containing the generated TypeScript type definitions. It includes the following keys:
            project_id (str): The ID of the project for which types were generated.
            types_content (str): A string containing the TypeScript type definitions.
            generation_status (str): Status of the type generation (e.g., 'SUCCESS', 'FAILED').
            message (Optional[str]): Additional information or error details if generation failed.

    Raises:
        NotFoundError: If the project_id does not exist.
        TypeGenerationError: If there was an error during the type generation process (e.g., database schema introspection failed, unsupported types).
        ValidationError: If input arguments fail validation.
    """
    if project_id is None:
        raise custom_errors.ValidationError("Input validation failed: project_id cannot be null or not a string.")
    if not isinstance(project_id, str):
        raise custom_errors.ValidationError("Input validation failed: project_id must be a string.")
    if not project_id:
        raise custom_errors.ValidationError("Input validation failed: project_id cannot be empty.")

    project = utils.get_entity_by_id(DB.get('projects', []), project_id)
    if not project:
        raise custom_errors.NotFoundError(f"Project with ID '{project_id}' not found.")

    try:
        project_tables = DB.get('tables', {}).get(project_id, [])
        
        if not project_tables:
            return {
                "project_id": project_id,
                "types_content": "",
                "generation_status": "SUCCESS",
                "message": None, 
            }

        ts_interface_blocks = []
        for table_data in project_tables:
            table_name = table_data.get('name')
            if not table_name:
                schema_name_for_error = table_data.get('schema', 'UnknownSchema')
                raise custom_errors.TypeGenerationError(
                    f"Table in project '{project_id}' (schema: '{schema_name_for_error}') found with no name. Schema introspection failed."
                )

            interface_name = table_name
            columns = table_data.get('columns', [])
            
            if not columns:
                ts_interface_blocks.append(f"export interface {interface_name} {{}}\n")
            else:
                properties_ts_lines = []
                for column_data in columns:
                    col_name = column_data.get('name')
                    db_type = column_data.get('data_type')
                    is_nullable = column_data.get('is_nullable', False)

                    if col_name is None or db_type is None: 
                        schema_name_for_error = table_data.get('schema', 'UnknownSchema')
                        table_name_for_error = table_name
                        raise custom_errors.TypeGenerationError(
                            f"Column in table '{schema_name_for_error}.{table_name_for_error}' (project '{project_id}') "
                            f"is missing name or data_type. Schema introspection failed."
                        )
                    
                    # Use the modified _map_db_type_to_typescript which returns None for unsupported types
                    ts_type = utils.map_db_type_to_typescript(db_type)

                    if ts_type is None: # Check for unsupported type marker
                        # Raise the fully contextualized error here
                        raise custom_errors.TypeGenerationError(
                             f"Type generation failed for project {project_id}: Encountered unsupported data type '{db_type}' in table '{table_name}', column '{col_name}'."
                        )

                    ts_type_full = ts_type
                    if is_nullable:
                        ts_type_full += " | null"
                    
                    ts_prop_name = col_name
                    properties_ts_lines.append(f"  {ts_prop_name}: {ts_type_full};")
                
                properties_str = "\n".join(properties_ts_lines)
                ts_interface_blocks.append(f"export interface {interface_name} {{\n{properties_str}\n}}\n")
        
        types_content = "".join(ts_interface_blocks)
        
        DB['project_ts_types'][project_id] = types_content

        return {
            "project_id": project_id,
            "types_content": types_content,
            "generation_status": "SUCCESS",
            "message": None,
        }
    except custom_errors.TypeGenerationError:
        raise

@tool_spec(
    spec={
        'name': 'restore_project',
        'description': """ Restores a Supabase project.
        
        This function restores a Supabase project. It uses the provided project ID
        to identify the project to be restored. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The ID of the project.'
                }
            },
            'required': [
                'project_id'
            ]
        }
    }
)
def restore_project(project_id: str) -> Dict[str, Any]:
    """Restores a Supabase project.

    This function restores a Supabase project. It uses the provided project ID
    to identify the project to be restored.

    Args:
        project_id (str): The ID of the project.

    Returns:
        Dict[str, Any]: A dictionary detailing the status of the restore operation. It includes the following keys:
            project_id (str): The ID of the project being restored.
            status (str): The new status of the project (e.g., 'RESTORING', 'ACTIVE_HEALTHY').
            message (str): A confirmation message.

    Raises:
        NotFoundError: If the project_id does not exist.
        OperationNotPermittedError: If the project cannot be restored (e.g., not paused, or other operational constraints).
        ValidationError: If input arguments fail validation.
    """

    if not isinstance(project_id, str):
        raise custom_errors.ValidationError('Project ID must be a string.')
    if not project_id: # Check for empty string
        raise custom_errors.ValidationError('Project ID cannot be empty.')

    # Retrieve the project from the database.
    project = utils.get_entity_by_id_from_db(DB, "projects", project_id)

    # If the project does not exist, raise NotFoundError.
    if not project:
        raise custom_errors.NotFoundError(f"Project with ID '{project_id}' not found.")

    # Check if the project is in a state that allows restoration.
    # A project must be in 'INACTIVE' status to be restored.
    current_status = project.get("status")
    if current_status != models.ProjectStatus.INACTIVE.value:
        status_for_message = current_status if current_status else "UNKNOWN"
        raise custom_errors.OperationNotPermittedError(
            f"Project '{project_id}' cannot be restored. Project must be in 'INACTIVE' status, "
            f"but current status is '{status_for_message}'."
        )

    # Define the target status for restoration.
    new_status = models.ProjectStatus.RESTORING.value
    
    # Update the project's status in the database.
    # The helper function is expected to correctly set the status to new_status ('RESTORING')
    # in the DB and return a reference to the updated project object.
    updated_project_ref_from_db = utils.update_project_status_and_cascade(DB, project_id, new_status)

    # Ensure the update was successful (helper should return the project object).
    if not updated_project_ref_from_db:
        # This indicates an unexpected internal state or issue with the update mechanism.
        raise custom_errors.OperationNotPermittedError(
            f"An unexpected error occurred while attempting to update project '{project_id}' status to '{new_status}'."
        )
    
    # The status in the response should directly reflect the intended new status.
    # While updated_project_ref_from_db.get("status") should be equal to new_status,
    # using new_status directly here makes the response construction more explicit about the action taken.
    response_status = new_status

    # Prepare the success response.
    response_data = {
        "project_id": project_id,
        "status": response_status, # Explicitly use the intended 'RESTORING' status
        "message": f"Project {project_id} is being restored." 
    }

    return response_data

@tool_spec(
    spec={
        'name': 'get_project',
        'description': """ Gets details for a Supabase project.
        
        Gets details for a Supabase project. This function retrieves information
        for a project identified by its unique ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The project ID.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_project(id: str) -> Dict[str, Any]:
    """Gets details for a Supabase project.

    Gets details for a Supabase project. This function retrieves information
    for a project identified by its unique ID.

    Args:
        id (str): The project ID.

    Returns:
        Dict[str, Any]: Details for the Supabase project. Includes the following keys:
            id (str): The unique identifier for the project (project ID).
            name (str): The name of the project.
            organization_id (str): The ID of the organization the project belongs to.
            region (str): The region where the project is hosted.
            status (str): The current status of the project (e.g., 'ACTIVE_HEALTHY', 'INACTIVE', 'COMING_UP', 'RESTORING').
            version (str): The Postgres version.
            created_at (str): ISO 8601 timestamp of when the project was created.

    Raises:
        NotFoundError: If the project with the specified ID does not exist.
        ValidationError: If input arguments fail validation.
    """
    # Validate input ID using the Pydantic model.
    try:
        validated_input_model = GetProjectInput(id=id)
        project_id_to_use = validated_input_model.id
    except PydanticValidationError as e:
        # Extract the first error message for simplicity, which usually matches test expectations for single field errors.
        if e.errors():
            first_error_msg = e.errors()[0]['msg']
            raise custom_errors.ValidationError(first_error_msg)
        else:
            # Fallback if PydanticValidationError is raised without specific error details (unlikely)
            raise custom_errors.ValidationError("Input validation failed.")


    # Retrieve the list of projects from the DB.
    # DB is a dictionary; 'projects' key is expected to hold a list of project dictionaries or models.
    projects_list = DB.get('projects', [])
    
    # Find the project by its ID using the provided utility function.
    # utils.get_entity_by_id is assumed to return a dictionary if DB['projects'] contains dicts.
    project_data = utils.get_entity_by_id(projects_list, project_id_to_use)

    # If the project with the specified ID is not found, raise NotFoundError.
    if project_data is None:
        raise custom_errors.NotFoundError(f"Project with ID '{project_id_to_use}' not found.")
    
    # Ensure 'version' is a string, converting None to "" as per "Source of Truth" for return types.
    version_value = project_data['version'] if project_data['version'] is not None else ""

    # Construct the response dictionary with the required project details.
    # Attributes are accessed using dictionary key access.
    # 'created_at' should already be an ISO string in the DB
    response_data = {
        "id": project_data['id'],
        "name": project_data['name'],
        "organization_id": project_data['organization_id'],
        "region": project_data['region'],
        "status": project_data['status'],
        "version": version_value,
        "created_at": project_data['created_at'],
    }

    return response_data

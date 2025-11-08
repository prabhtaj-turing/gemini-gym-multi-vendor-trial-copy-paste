from common_utils.tool_spec_decorator import tool_spec
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from pydantic import ValidationError

from .SimulationEngine.models import DeployEdgeFunctionInputArgs, DeployEdgeFunctionResponse, EdgeFunctionStatus

from .SimulationEngine.db import DB
from .SimulationEngine import utils
from .SimulationEngine import custom_errors
from .SimulationEngine.typescript_validator import get_validator, format_diagnostics

@tool_spec(
    spec={
        'name': 'list_edge_functions',
        'description': """ Lists all Edge Functions in a Supabase project.
        
        This function lists all Edge Functions available within a specified Supabase project.
        For each Edge Function, it provides comprehensive details including its unique
        identifier, slug, display name, current version, operational status, and
        timestamps indicating its creation and last update. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The identifier of the Supabase project.'
                }
            },
            'required': [
                'project_id'
            ]
        }
    }
)
def list_edge_functions(project_id: str) -> List[Dict[str, Any]]:
    """Lists all Edge Functions in a Supabase project.

    This function lists all Edge Functions available within a specified Supabase project.
    For each Edge Function, it provides comprehensive details including its unique
    identifier, slug, display name, current version, operational status, and
    timestamps indicating its creation and last update.

    Args:
        project_id (str): The identifier of the Supabase project.

    Returns:
        List[Dict[str, Any]]: A list of Edge Functions. Each dictionary in the list
            represents an Edge Function and contains the following keys:
            id (str): The unique identifier for the Edge Function.
            slug (str): The slug (name) of the Edge Function, used for invocation.
            name (str): The display name of the Edge Function.
            version (str): The current deployed version identifier of the Edge Function.
            status (str): The current status of the Edge Function (e.g., 'ACTIVE_HEALTHY', 'BUILDING', 'ERROR').
            created_at (str): ISO 8601 timestamp indicating when the function was created.
            updated_at (str): ISO 8601 timestamp indicating when the function was last updated or deployed.

    Raises:
        NotFoundError: If the project_id does not exist.
        FeatureNotEnabledError: If Edge Functions are not enabled or available for the project's subscription plan.
        ValidationError: If input arguments fail validation.
    """
    # Validate project_id input: type check
    if not isinstance(project_id, str):
        raise custom_errors.ValidationError("Project ID must be a string.")
    
    # Validate project_id input: empty check after stripping
    # Use the stripped version of project_id for all subsequent operations and messages.
    project_id_stripped = project_id.strip()
    if not project_id_stripped:
        raise custom_errors.ValidationError("Project ID cannot be empty.")
    
    project_id = project_id_stripped

    # Check if the project exists
    project = utils.get_entity_by_id_from_db(DB, "projects", project_id)
    if not project:
        # Corrected message format to match test expectation (removed single quotes around project_id)
        raise custom_errors.NotFoundError(f"Project with ID {project_id} not found.")

    # Check if Edge Functions feature is enabled for the project's organization
    organization_id = project.get("organization_id")
    organization = None
    if organization_id: 
        organization = utils.get_entity_by_id_from_db(DB, "organizations", organization_id)

    edge_functions_feature_enabled = False
    if organization:
        edge_functions_feature_enabled = True
    
    if not edge_functions_feature_enabled:
        raise custom_errors.FeatureNotEnabledError(
            f"Edge Functions are not enabled for project {project_id}."
        )

    # Retrieve edge functions for the project from the DB.
    # DB['edge_functions'] is expected to be a Dict[str, List[Dict[str, Any]]].
    # The `or []` handles cases where the project_id might not be in DB['edge_functions']
    # or its value might be None, ensuring project_edge_functions_data is always a list.
    project_edge_functions_data = DB.get("edge_functions", {}).get(project_id) or []
    
    formatted_functions: List[Dict[str, Any]] = []
    # Ensure project_edge_functions_data is iterable (it should be a list due to `or []`)
    if project_edge_functions_data: # Check if list is not empty before iterating
        for func_data in project_edge_functions_data:
            # Construct the response dictionary for each function.
            # This assumes that func_data conforms to the EdgeFunction model structure.
            # Handle both string and datetime objects for timestamps
            created_at = func_data["created_at"]
            updated_at = func_data["updated_at"]
            
            # Convert datetime objects to ISO format strings if needed
            if hasattr(created_at, 'isoformat'):
                created_at = created_at.isoformat()
            if hasattr(updated_at, 'isoformat'):
                updated_at = updated_at.isoformat()
            
            formatted_functions.append({
                "id": func_data["id"],
                "slug": func_data["slug"],
                "name": func_data["name"],
                "version": func_data["version"],
                "status": func_data["status"], 
                "created_at": created_at,
                "updated_at": updated_at,
            })
        
    return formatted_functions

@tool_spec(
    spec={
        'name': 'deploy_edge_function',
        'description': """ Deploys an Edge Function to a Supabase project.
        
        This function deploys an Edge Function to a specified Supabase project.
        If the function already exists within the project, this operation will create
        a new version of that function. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'ref': {
                    'type': 'string',
                    'description': 'The identifier of the Supabase project.'
                },
                'slug': {
                    'type': 'string',
                    'description': 'The name of the function.'
                },
                'bundleOnly': {
                    'type': 'boolean',
                    'description': 'Whether to bundle only the function or include dependencies. Defaults to True.'
                },
                'verifyJWT': {
                    'type': 'boolean',
                    'description': 'Whether to verify the JWT token. Defaults to True.'
                },
                'importMap': {
                    'type': 'boolean',
                    'description': 'Whether to include the import map. Defaults to True.'
                },
                'ezbrSha256': {
                    'type': 'string',
                    'description': 'The SHA-256 hash of the function. Defaults to None.'
                },
                'entrypoint_path': {
                    'type': 'string',
                    'description': 'The entrypoint of the function. Defaults to "index.ts".'
                },
                'import_map_path': {
                    'type': 'string',
                    'description': 'The import map for the function. Defaults to None.'
                },
                'files': {
                    'type': 'array',
                    'description': """ The files to upload. This should include the
                    entrypoint and any relative dependencies. Each dictionary in the list
                    represents a file and must contain the following keys: """,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {
                                'type': 'string',
                                'description': "The name of the file (e.g., 'index.ts', 'utils/helper.ts')."
                            },
                            'content': {
                                'type': 'string',
                                'description': 'The string content of the file.'
                            }
                        },
                        'required': [
                            'name',
                            'content'
                        ]
                    }
                },
                'entrypoint_path': {
                    'type': 'string',
                    'description': """ The entrypoint of the function.
                    Defaults to "index.ts". """
                },
                'import_map_path': {
                    'type': 'string',
                    'description': """ The import map for the function.
                    Defaults to None. """
                }
            },
            'required': [
                'ref',
                'slug',
                'files'
            ]
        }
    }
)
def deploy_edge_function(
    ref: str, 
    slug: str,
    files: List[Dict[str, str]],
    bundleOnly: Optional[bool] = True, 
    verifyJWT: Optional[bool] = True, 
    importMap: Optional[bool] = True, 
    ezbrSha256: Optional[str] = None, 
    entrypoint_path: Optional[str] = "index.ts", 
    import_map_path: Optional[str] = None) -> Dict[str, Any]:
    """Deploys an Edge Function to a Supabase project.

    This function deploys an Edge Function to a specified Supabase project.
    If the function already exists within the project, this operation will create
    a new version of that function.

    Args:
        ref (str): The identifier of the Supabase project.
        slug (str): The slug of the function.
        files (List[Dict[str, str]]): The files to upload. This should include the
            entrypoint and any relative dependencies. Each dictionary in the list
            represents a file and must contain the following keys:
            name (str): The name of the file (e.g., 'index.ts', 'utils/helper.ts').
            content (str): The string content of the file.
        bundleOnly (Optional[bool]): Whether to bundle only the function or include dependencies. Defaults to True.
        verifyJWT (Optional[bool]): Whether to verify the JWT token. Defaults to True.
        importMap (Optional[bool]): Whether to include the import map. Defaults to True.
        ezbrSha256 (Optional[str]): The SHA-256 hash of the function.
        entrypoint_path (Optional[str]): The entrypoint of the function. Defaults to "index.ts".
        import_map_path (Optional[str]): The import map for the function.
            Defaults to None.
        
    Returns:
        Dict[str, Any]: Details of the deployed Edge Function. This dictionary
            includes the following keys:
            id (str): The unique identifier for the Edge Function.
            slug (str): The slug (name) of the Edge Function, used in its
                invocation URL.
            name (str): The display name of the Edge Function.
            version (str): The identifier for this newly deployed version of the
                Edge Function.
            status (str): The current status of this version's deployment (e.g., 'ACTIVE', 'REMOVED', 'THROTTLED').
            deployment_id (str): A unique identifier for this specific deployment
                operation.

    Raises:
        NotFoundError: If the project ref does not exist.
        InvalidInputError: If 'name' or 'files' are invalid, missing, malformed,
            or if file content is not valid code. This can also be raised if
            'entrypoint_path' or 'import_map_path' point to non-existent files
            within the 'files' list.
        FeatureNotEnabledError: If Edge Functions are not enabled or available for
            the project's current subscription plan.
        ValidationError: If input arguments fail validation.
    """
    try:
        args_data = {
            "project_id": ref,
            "name": slug,
            "slug": slug,
            "bundleOnly": bundleOnly,
            "verifyJWT": verifyJWT,
            "importMap": importMap,
            "ezbrSha256": ezbrSha256,
            "files": files,
            "entrypoint_path": entrypoint_path,
            "import_map_path": import_map_path,
        }
        # Perform Pydantic validation for types and basic structure
        validated_args = DeployEdgeFunctionInputArgs(**args_data)

        # Extract validated data
        project_id = validated_args.project_id
        name = validated_args.slug
        slug = validated_args.slug
        bundleOnly = validated_args.bundleOnly
        verifyJWT = validated_args.verifyJWT
        importMap = validated_args.importMap
        ezbrSha256 = validated_args.ezbrSha256
        files = validated_args.files
        entrypoint_path = validated_args.entrypoint_path
        import_map_path = validated_args.import_map_path
        
    except Exception as e:
        # Handle both Pydantic ValidationError and our mock ValidationError
        if hasattr(e, 'errors'):
            err = e.errors()[0]
            loc = err.get('loc')
            # Get error type string, defaulting to empty string if 'type' key is missing.
            err_type = err.get('type', '')

            # Check for missing field error type (robust for Pydantic v1 'xxx.missing' and Pydantic v2 'missing')
            is_field_missing_error = err_type.endswith('.missing') or err_type == 'missing'

            # Handle missing keys in file items (results in InvalidInputError)
            # This check must come before the more general 'loc' checks for 'files' items if it's to raise InvalidInputError.
            if is_field_missing_error and loc and loc[0] == 'files' and isinstance(loc[1], int) and len(loc) == 3:
                index = loc[1]
                missing_field = loc[2] 
                raise custom_errors.InvalidInputError(f"File entry at index {index} is missing '{missing_field}' key.")

            # Handle type errors and other structural validation errors (results in ValidationError)
            if loc == ('project_id',):
                raise custom_errors.ValidationError("Input validation failed: project_id must be a string.")
            elif loc == ('name',):
                raise custom_errors.ValidationError("Input validation failed: name must be a string.")
            elif loc == ('files',): # Error on 'files' field itself (e.g., not a list)
                raise custom_errors.ValidationError("Input validation failed: files must be a list.")
            elif loc == ('entrypoint_path',):
                raise custom_errors.ValidationError("Input validation failed: entrypoint_path must be a string or null.")
            elif loc == ('import_map_path',):
                raise custom_errors.ValidationError("Input validation failed: import_map_path must be a string or null.")
            elif loc and loc[0] == 'files' and isinstance(loc[1], int): # Errors within 'files' list items
                index = loc[1]
                # This section handles type errors or if a file item is not a dict.
                # Missing fields within file items are handled by the 'is_field_missing_error' block above.
                if len(loc) == 2: # Error on the file item itself (e.g., files[index] is not a dict)
                    raise custom_errors.ValidationError(f"Input validation failed: file entry at index {index} must be a dictionary.")
                elif len(loc) == 3: # Error on a field within a file item dict (e.g., type error for name/content)
                    field_name_in_file = loc[2]
                    if field_name_in_file == 'name':
                        raise custom_errors.ValidationError(f"Input validation failed: file name at index {index} must be a string.")
                    elif field_name_in_file == 'content':
                        raise custom_errors.ValidationError(f"Input validation failed: file content at index {index} must be a string.")
            
            # Fallback for unmapped Pydantic errors
            unhandled_error_msg = f"loc={loc}, type={err_type}, msg={err.get('msg')}"
            raise custom_errors.ValidationError(f"Input validation failed: {unhandled_error_msg}")

    # --- Semantic Validations (after Pydantic type/structure validation) ---

    # Validate project_id existence
    project = utils.get_entity_by_id_from_db(DB, "projects", project_id)
    if not project:
        raise custom_errors.NotFoundError(f"Project with ID '{project_id}' not found.")

    # Check if Edge Functions feature is enabled
    organization = utils.get_entity_by_id_from_db(DB, "organizations", project["organization_id"])
    if not organization:
        raise custom_errors.FeatureNotEnabledError(
            f"Failed to determine feature availability: Organization '{project['organization_id']}' not found or feature check failed."
        )
    
    # Validate slug (semantic)
    if not slug.strip(): 
        raise custom_errors.InvalidInputError("Function slug cannot be empty.")

    # Validate files list (semantic - non-empty)
    if not files:
        raise custom_errors.InvalidInputError("Files list cannot be empty.")
    
    validated_files_for_db = []
    file_names_set = set() 

    # First pass: collect file names and check for duplicates
    for file_model in files:
        if file_model.name in file_names_set:
            raise custom_errors.InvalidInputError(
                f"Duplicate file name '{file_model.name}' found in 'files' list."
            )
        file_names_set.add(file_model.name)

    # Validate entrypoint_path existence in files
    if entrypoint_path not in file_names_set:
        raise custom_errors.InvalidInputError(
            f"Entrypoint file '{entrypoint_path}' not found in provided files."
        )

    # Validate import_map_path existence in files (if provided)
    if import_map_path is not None and import_map_path not in file_names_set:
        raise custom_errors.InvalidInputError(
            f"Import map file '{import_map_path}' not found in provided files."
        )

    # Initialize TypeScript validator
    try:
        validator = get_validator()
    except Exception as e:
        raise custom_errors.InvalidInputError(f"Failed to initialize TypeScript validator: {str(e)}")

    # Second pass: validate file content and extensions
    for file_model in validated_args.files:
        # Skip TypeScript validation for import map files
        if file_model.name.endswith('.json'):
            if not file_model.content.strip():
                raise custom_errors.InvalidInputError(
                    f"File content for '{file_model.name}' cannot be empty or consist only of whitespace."
                )
            try:
                processed_file_dict = file_model.model_dump() 
            except AttributeError:
                processed_file_dict = file_model.dict() 
            validated_files_for_db.append(processed_file_dict)
            continue

        # Validate JavaScript/TypeScript files - MUST BE FIRST CHECK
        if not (file_model.name.endswith('.ts') or file_model.name.endswith('.js')):
            raise custom_errors.InvalidInputError(
                f"File '{file_model.name}' must have a .ts or .js extension."
            )

        # Validate file content
        if not file_model.content.strip():
            raise custom_errors.InvalidInputError(
                f"File content for '{file_model.name}' cannot be empty or consist only of whitespace."
            )

        # Additional validation for function syntax
        if file_model.content.strip().startswith("function"):
            # Check if the function has proper syntax
            if not ("(" in file_model.content and ")" in file_model.content):
                raise custom_errors.InvalidInputError(
                    f"File '{file_model.name}' contains invalid function syntax. Functions must have proper parameter parentheses."
                )
            if not ("{" in file_model.content and "}" in file_model.content):
                raise custom_errors.InvalidInputError(
                    f"File '{file_model.name}' contains invalid function syntax. Functions must have a body enclosed in curly braces."
                )

        # Check for non-JavaScript content
        if not any(keyword in file_model.content for keyword in ["function", "const", "let", "var", "class", "interface", "type", "import", "export"]):
            raise custom_errors.InvalidInputError(
                f"File '{file_model.name}' does not contain valid JavaScript/TypeScript code. The content appears to be non-code text."
            )

        # Validate TypeScript/JavaScript code using the validator
        is_valid, diagnostics = validator.validate(file_model.content)
        if not is_valid:
            error_message = format_diagnostics(diagnostics)
            raise custom_errors.InvalidInputError(
                f"File '{file_model.name}' contains invalid TypeScript/JavaScript code: {error_message}"
            )

        try:
            processed_file_dict = file_model.model_dump() 
        except AttributeError:
            processed_file_dict = file_model.dict() 
        validated_files_for_db.append(processed_file_dict)

    function_slug = utils.name_to_slug(name) 
    
    function_entity_id = None
    project_function_versions = DB.get("edge_functions", {}).get(project_id, [])
    if not isinstance(project_function_versions, list):
        project_function_versions = []
    for func_version in project_function_versions:
        if func_version.get("slug") == function_slug:
            function_entity_id = func_version.get("id")
            break
    
    if function_entity_id is None:
        function_entity_id = utils.generate_unique_id(prefix="fn_")

    version_identifier = utils.generate_unique_id(prefix="v_") 
    deployment_identifier = utils.generate_unique_id(prefix="dep_")
    current_timestamp = datetime.now(timezone.utc)
    
    initial_status = EdgeFunctionStatus.ACTIVE.value

    new_edge_function_version_data = {
        "id": function_entity_id,
        "slug": function_slug,
        "name": name, 
        "version": version_identifier,
        "status": initial_status,
        "created_at": current_timestamp,
        "updated_at": current_timestamp,
        "entrypoint_path": validated_args.entrypoint_path, 
        "import_map_path": validated_args.import_map_path, 
        "files": validated_files_for_db, 
    }

    if project_id not in DB.get("edge_functions", {}): 
        DB.setdefault("edge_functions", {})[project_id] = []
    elif not isinstance(DB["edge_functions"].get(project_id), list): 
         DB["edge_functions"][project_id] = []
         
    DB["edge_functions"][project_id].append(new_edge_function_version_data)

    response_data = {
        "id": function_entity_id,
        "slug": function_slug,
        "name": name,
        "version": version_identifier,
        "status": initial_status,
        "deployment_id": deployment_identifier,
    }

    return DeployEdgeFunctionResponse(**response_data).model_dump()

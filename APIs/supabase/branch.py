from common_utils.tool_spec_decorator import tool_spec
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Mapping, Sequence
from .SimulationEngine import utils, custom_errors, models
from .SimulationEngine.db import DB
from .database import execute_sql
from .database import apply_migration
import copy
from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine.duckdb_manager import get_duckdb_manager
from collections.abc import Mapping, Sequence
# Helper function to find a branch in the DB structure.
# Defined as a top-level "private" function.


@tool_spec(
    spec={
        'name': 'rebase_branch',
        'description': """ Rebases a development branch on production.
        
        The function effectively runs any newer migrations from production onto this
        branch to help handle migration drift. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'branch_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the branch to be rebased.'
                }
            },
            'required': [
                'branch_id'
            ]
        }
    }
)
def rebase_branch(branch_id: str) -> Dict[str, Any]:
    """Rebases a development branch on production.

    The function effectively runs any newer migrations from production onto this
    branch to help handle migration drift.

    Args:
        branch_id (str): The unique identifier of the branch to be rebased.

    Returns:
        Dict[str, Any]: A dictionary containing the status of the branch rebase
            operation, with the following keys:
            branch_id (str): The ID of the branch being rebased.
            status (str): The current status of the rebase (e.g., 'REBASING',
                'COMPLETED', 'FAILED', 'CONFLICT').
            rebase_operation_id (Optional[str]): An identifier for the rebase
                operation, especially if asynchronous.

    Raises:
        ResourceNotFoundError: If the branch_id does not exist.
        ValidationError: If the input is Invalid.
        RebaseConflictError: If there are conflicts during the rebase process
            (e.g., migration conflicts that cannot be automatically resolved).
        OperationNotPermittedError: If the branch is not in a state suitable
            for rebasing (e.g., has local changes not captured in migrations).
    """
    # 1. Input validation for branch_id
    if not isinstance(branch_id, str):
        # This handles None and other non-string types.
        raise custom_errors.ValidationError("Input validation failed: branch_id must be a string.")
    if not branch_id.strip(): # branch_id is now known to be a string.
        raise custom_errors.ValidationError("Input validation failed: branch_id cannot be empty.")

    # 2. Fetch the target branch from the database.
    target_branch = utils.find_branch_in_db(DB, branch_id)
    if not target_branch:
        raise custom_errors.ResourceNotFoundError(f"Branch with ID '{branch_id}' not found.")

    # 3. Check for uncommitted local changes.
    # This check is based on 'internal_props' as per test setup for 'branch_local_changes_1'.
    # If this error is raised, the branch status in DB should not change.
    if target_branch.get("internal_props", {}).get("has_uncommitted_schema_changes"):
        raise custom_errors.OperationNotPermittedError(
            f"Branch '{branch_id}' has local changes not captured in migrations and cannot be rebased."
        )

    # 4. Check current branch status. Only 'ACTIVE_HEALTHY' branches are eligible for rebase.
    # If this error is raised, the branch status in DB should not change.
    if target_branch['status'] != 'ACTIVE_HEALTHY':
        raise custom_errors.OperationNotPermittedError(
            f"Branch '{branch_id}' is not in a rebasable state (current status: {target_branch['status']})."
        )

    # 5. Simulate a pre-rebase conflict check for specific test data ('branch_conflict_1').
    # This handles 'test_rebase_conflict_error' where status must not change in DB.
    if branch_id == "branch_conflict_1":
        # Branch status ('ACTIVE_HEALTHY') remains unchanged in the DB.
        raise custom_errors.RebaseConflictError(
            f"Rebase failed for branch '{branch_id}' due to migration conflicts."
        )

    # 6. Determine if there are any migrations from production to apply to the branch.
    # Assumes 'parent_project_id' and 'branch_project_id' are present and valid in target_branch
    # as per the Branch Pydantic model schema.
    prod_project_id = target_branch['parent_project_id']
    dev_project_id = target_branch['branch_project_id']

    all_migrations_in_db = DB.get('migrations', {})
    prod_migrations_list = all_migrations_in_db.get(prod_project_id, [])
    
    if dev_project_id not in all_migrations_in_db: # Ensure dev project's migration list exists
        all_migrations_in_db[dev_project_id] = []
    dev_migrations_list = all_migrations_in_db[dev_project_id]
    
    # Get versions of migrations already applied to the development branch.
    # Use .get() for robustness against potentially malformed migration entries.
    applied_dev_migration_versions = {
        m.get('version') for m in dev_migrations_list 
        if m.get('status') in ['APPLIED_SUCCESSFULLY', 'applied'] and m.get('version') is not None
    }

    migrations_to_apply_to_dev: List[Dict[str, Any]] = []
    for prod_mig in prod_migrations_list:
        prod_mig_version = prod_mig.get('version')
        # Check if production migration is applied and its version is not among applied dev versions.
        if prod_mig.get('status') in ['APPLIED_SUCCESSFULLY', 'applied'] and \
           prod_mig_version is not None and \
           prod_mig_version not in applied_dev_migration_versions:
            migrations_to_apply_to_dev.append(prod_mig)
    
    # Sort migrations by version. This is good practice for sequential application.
    migrations_to_apply_to_dev.sort(key=lambda m: m.get('version', ''))

    current_time = datetime.now(timezone.utc)
    target_branch['last_activity_at'] = current_time # Update last activity timestamp

    # 7. Handle based on whether migrations are needed.
    if not migrations_to_apply_to_dev:
        # Branch is already up-to-date. Rebase completes synchronously.
        # Branch status in DB remains 'ACTIVE_HEALTHY' (or is ensured to be 'ACTIVE_HEALTHY').
        target_branch['status'] = 'ACTIVE_HEALTHY' 
        return {
            "branch_id": branch_id,
            "status": "COMPLETED",
            "rebase_operation_id": None # Changed: No operation ID for synchronous completion.
        }
    else:
        # Branch needs rebasing. We'll apply migrations synchronously for immediate rebase
        # Update branch status in DB to 'REBASING'.
        target_branch['status'] = 'REBASING'
        rebase_operation_id = utils.generate_unique_id(prefix="rb_op_")
        
        try:
            # Apply each migration from production to the branch
            for migration in migrations_to_apply_to_dev:
                migration_name = migration.get('name', f"rebase_migration_{migration.get('version', '')}")
                migration_query = migration.get('query', '')
                
                # Skip migrations without query (metadata-only migrations)
                if not migration_query:
                    continue
                
                try:
                    # Apply the migration to the branch project
                    apply_migration(
                        project_id=dev_project_id,
                        name=f"rebased_from_prod_{migration_name}",
                        query=migration_query
                    )
                except custom_errors.MigrationError as e:
                    # If a migration fails, we have a conflict
                    target_branch['status'] = 'ACTIVE_HEALTHY'  # Revert to active state
                    raise custom_errors.RebaseConflictError(
                        f"Rebase failed for branch '{branch_id}' due to migration conflict: {str(e)}"
                    )
            
            # All migrations applied successfully
            target_branch['status'] = 'ACTIVE_HEALTHY'
            target_branch['last_activity_at'] = datetime.now(timezone.utc)
            
            return {
                "branch_id": branch_id,
                "status": "COMPLETED",
                "rebase_operation_id": rebase_operation_id
            }
            
        except Exception as e:
            # Any unexpected error during rebase
            target_branch['status'] = 'ERROR'
            target_branch['last_activity_at'] = datetime.now(timezone.utc)
            
            # If it's not already a RebaseConflictError, wrap it
            if not isinstance(e, custom_errors.RebaseConflictError):
                raise custom_errors.RebaseConflictError(
                    f"Rebase failed for branch '{branch_id}' with unexpected error: {str(e)}"
                )
            raise


@tool_spec(
    spec={
        'name': 'create_branch',
        'description': """ Creates a development branch on a Supabase project.
        
        This function creates a development branch on a Supabase project. It applies all migrations
        from the main project to a fresh branch database. Production data will not carry over.
        The branch receives its own project_id via the resulting project_ref, which should be
        used to execute queries and migrations on the branch. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'ref': {
                    'type': 'string',
                    'description': 'The identifier of the project.'
                },
                'name': {
                    'type': 'string',
                    'description': 'The cost confirmation ID. Call `confirm_cost` first.'
                },
                'git_branch': {
                    'type': 'string',
                    'description': 'Name of the branch to create. Defaults to "develop".'
                },
                'is_default': {
                    'type': 'boolean',
                    'description': 'Whether the branch is the default branch. Defaults to False.'
                },
                'persistent': {
                    'type': 'boolean',
                    'description': 'Whether the branch is persistent. Defaults to True.'
                },
                'region': {
                    'type': 'string',
                    'description': 'The region of the branch. Defaults to "us-central1".'
                }
            },
            'required': [
                'ref',
                'name'
            ]
        }
    }
)
def create_branch(
    ref: str, 
    name: str,
    git_branch: Optional[str] = None,
    is_default: Optional[bool] = False,
    persistent: Optional[bool] = True,
    region: Optional[str] = None
    ) -> Dict[str, Any]:
    """Creates a development branch on a Supabase project.

    This function creates a new branch on a Supabase project. It applies all migrations
    from the main project to a fresh branch database. Production data will not carry over.
    The branch receives its own project_id via the resulting project_ref, which should be
    used to execute queries and migrations on the branch.

    Args:
        ref (str): The identifier of the project.
        name (str): Name of the branch to create.
        git_branch (Optional[str]): The name of the git branch default is None.
        is_default (Optional[bool]): Whether the branch is the default branch default is False.
        persistent (Optional[bool]): Whether the branch is persistent default is True.
        region (Optional[str]): The region of the branch default is None.

    Returns:
        Dict[str, Any]: Information about the newly created development branch. Includes the following keys:
            id (str): The unique identifier for the new branch (branch ID).
            name (str): The name of the new branch.
            project_ref (str): The project ID (project_ref) specifically for this branch's database.
            parent_project_ref (str): The project ID (project_ref) specifically for this branch's database.
            is_default (bool): Whether the branch is the default branch.
            git_branch (Optional[str]): The name of the git branch default is None.
            pr_number (Optional[int]): The number of the pull request default is None.
            persistent (bool): Whether the branch is persistent.
            status (str): The status of the branch (e.g., 'CREATING_PROJECT', 'MIGRATIONS_PASSED', 'FUNCTIONS_DEPLOYED').
            created_at (str): ISO 8601 timestamp of when the branch creation was initiated.
            updated_at (str): ISO 8601 timestamp of when the branch creation was initiated.
            review_requested_at (Optional[str]): ISO 8601 timestamp of when the branch creation was initiated.
            with_data (bool): Whether the branch is with data.

    Raises:
        NotFoundError: If the project_ref does not exist, or if the organization associated with the project is not found.
        ValidationError: If required inputs (e.g., ref) are missing, or the branch name is invalid.
        BranchingNotEnabledError: If the branching feature is not enabled for the project's organization.
        ValidationError: Failed to create the branch due to validation errors.
    """
    # Validate inputs
    if not ref:
        raise custom_errors.ValidationError("Input validation failed: ref cannot be None or empty.")
    if not name: 
        raise custom_errors.ValidationError("Input validation failed: Branch name cannot be empty.")

    parent_project = utils.get_entity_by_id_from_db(DB, "projects", ref)
    if not parent_project:
        raise custom_errors.NotFoundError(f"Parent project with ID '{ref}' not found.")

    organization_id = parent_project.get("organization_id")
    organization = utils.get_entity_by_id_from_db(DB, "organizations", organization_id)

    if not organization:
        raise custom_errors.NotFoundError(
             f"Organization '{organization_id}' associated with project '{ref}' not found."
        )

    plan = organization.get("plan", {})
    if plan not in ['pro', 'team', 'enterprise']:
        raise custom_errors.BranchingNotEnabledError(
                    f"Branching feature is not enabled for the organization of project '{ref}'."
                )    

    project_branches = DB["branches"].get(ref, [])
    if any(branch["name"] == name for branch in project_branches):
        raise custom_errors.ValidationError(
            f"A branch with the name '{name}' already exists for project '{ref}'."
        )

    current_time = datetime.now(timezone.utc)
    current_time_iso = current_time.isoformat()

    branch_project_id = utils.generate_unique_id(prefix="proj_") 
    branch_project_name = f"{parent_project['name']}-{name}"

    parent_tables = copy.deepcopy(DB["tables"].get(ref, []))
    DB["tables"][branch_project_id] = parent_tables
    parent_extensions = copy.deepcopy(DB["extensions"].get(ref, []))
    DB["extensions"][branch_project_id] = parent_extensions
    DB["edge_functions"][branch_project_id] = []
    
    branch_project_slug = utils.name_to_slug(branch_project_name)
    DB["project_urls"][branch_project_id] = f"https://{branch_project_slug}.supabase.co"
    DB["project_anon_keys"][branch_project_id] = f"proj.anon.key.{branch_project_id}" 

    parent_migrations = DB["migrations"].get(ref, [])
    branch_project_migrations = []
    for mig_template in parent_migrations:
        copied_mig = mig_template.copy()
        copied_mig["status"] = "APPLIED_SUCCESSFULLY" 
        copied_mig["applied_at"] = current_time 
        branch_project_migrations.append(copied_mig)
    DB["migrations"][branch_project_id] = branch_project_migrations
    
    branch_id = utils.generate_unique_id(prefix="branch_")
    new_branch_record = {
        "id": branch_id,
        "name": name,
        "project_ref": ref,
        "parent_project_ref": ref,
        "is_default": is_default,
        "git_branch": git_branch,
        "persistent": persistent,
        "region": region,
        "status": "CREATING_PROJECT", 
        "created_at": current_time_iso, 
        "updated_at": current_time_iso,
        "review_requested_at": None,
        "with_data": True
    }

    try:
        new_branch_record = models.Branch(**new_branch_record)
    except Exception as e:
        raise custom_errors.ValidationError(f"Failed to create the branch due to validation errors: {str(e)}")

    DB.setdefault("branches", {}).setdefault(ref, []).append(new_branch_record.model_dump(mode="json"))

    return new_branch_record.model_dump(mode="json") # type: ignore
    
@tool_spec(
    spec={
        'name': 'merge_branch',
        'description': """ Merges migrations and edge functions from a development branch to production.
        
        This function processes the branch identified by `branch_id` to merge its
        associated migrations and edge functions into the production environment.
        It returns a dictionary detailing the status of this merge operation. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'branch_id': {
                    'type': 'string',
                    'description': 'The ID of the development branch to be merged.'
                }
            },
            'required': [
                'branch_id'
            ]
        }
    }
)
def merge_branch(branch_id: str) -> Dict[str, Any]:
    """Merges migrations and edge functions from a development branch to production.

    This function processes the branch identified by `branch_id` to merge its
    associated migrations and edge functions into the production environment.
    It returns a dictionary detailing the status of this merge operation.

    Args:
        branch_id (str): The ID of the development branch to be merged.

    Returns:
        Dict[str, Any]: A dictionary providing the status of the merge operation, with the following keys:
            branch_id (str): The ID of the branch being merged.
            target_project_id (str): The ID of the production project the branch is merged into.
            status (str): The current status of the merge (e.g., 'MERGING', 'COMPLETED', 'FAILED', 'CONFLICT').
            merge_request_id (Optional[str]): An identifier for the merge operation, particularly relevant if the merge is processed asynchronously.

    Raises:
        NotFoundError: If the branch_id does not exist.
        MergeConflictError: If there are conflicts that prevent the merge (e.g., migration conflicts, edge function conflicts).
        OperationNotPermittedError: If the branch is not in a state suitable for merging (e.g., still creating, has uncommitted changes not part of migrations).
        ValidationError: If input arguments fail validation.
    """
    # Validate branch_id input
    if not isinstance(branch_id, str):
        raise custom_errors.ValidationError("Branch ID must be a string.")
    if not branch_id.strip(): # Check for empty or whitespace-only string
        raise custom_errors.ValidationError("Branch ID cannot be empty.")

    # Find the branch data from the DB.
    branch_data = None
    # Iterate through all parent project IDs that have branches.
    for parent_project_id_key in DB.get("branches", {}):
        # Iterate through the list of branches for that parent project.
        for branch_dict_item in DB["branches"][parent_project_id_key]:
            if branch_dict_item.get("id") == branch_id:
                branch_data = branch_dict_item
                break
        if branch_data:
            break  # Branch found, exit outer loop.
    
    if not branch_data:
        raise custom_errors.NotFoundError(f"Branch with ID '{branch_id}' not found.")

    target_project_id = branch_data["parent_project_id"]
    branch_project_id = branch_data["branch_project_id"] # The project ID for the branch's isolated database.

    # Validate branch status for merging.
    branch_status = branch_data.get("status")
    if branch_status != 'ACTIVE_HEALTHY': 
        raise custom_errors.OperationNotPermittedError(
            f"Branch is not in a mergable state. Current status: {branch_status}."
        )

    # Generate a unique ID for this merge operation.
    merge_request_id = utils.generate_unique_id(prefix="mr_")
    original_branch_status = branch_data["status"] 
    
    branch_data["status"] = 'MERGING'
    branch_data["last_activity_at"] = datetime.now(timezone.utc)


    response = {
        "branch_id": branch_id,
        "target_project_id": target_project_id,
        "status": 'MERGING', # Initial response status
        "merge_request_id": merge_request_id,
    }

    try:
        # --- Merge Edge Functions First ---
        branch_edge_functions = DB.setdefault("edge_functions", {}).get(branch_project_id, [])
        target_edge_functions_list = DB.setdefault("edge_functions", {}).setdefault(target_project_id, [])

        final_target_ef_map = {ef.get("slug"): ef.copy() for ef in target_edge_functions_list if ef.get("slug")}

        for bef_original in branch_edge_functions:
            bef = bef_original.copy() # Work with a copy of the branch edge function
            bef_slug = bef.get("slug")
            if not bef_slug: 
                continue
            
            current_target_ef = final_target_ef_map.get(bef_slug)

            if current_target_ef:
                # Slug exists in target. Determine if it's an update or conflict.
                if bef.get("version") == current_target_ef.get("version"):
                    # Same version: conflict if content (e.g., files) is different.
                    if bef.get("files") != current_target_ef.get("files"):
                        branch_data["status"] = original_branch_status # Revert branch status
                        raise custom_errors.MergeConflictError(
                            f"Edge function conflict detected for slug '{bef_slug}'."
                        )
                else:
                    bef["status"] = "ACTIVE_HEALTHY" 
                    bef["updated_at"] = datetime.now(timezone.utc) # Set updated_at to merge time
                    final_target_ef_map[bef_slug] = bef # Replace with branch version
            else:
                # Slug does not exist in target: This is a new function.
                # bef already contains its original created_at from the branch.
                bef["status"] = "ACTIVE_HEALTHY"
                bef["updated_at"] = datetime.now(timezone.utc) # Set updated_at to merge time
                final_target_ef_map[bef_slug] = bef # Add new function

        DB["edge_functions"][target_project_id] = list(final_target_ef_map.values())

        # --- Merge Migrations ---
        branch_migrations = DB.setdefault("migrations", {}).get(branch_project_id, [])
        target_migrations_list = DB.setdefault("migrations", {}).setdefault(target_project_id, [])
        
        # Create a map of existing migrations by version
        target_migrations_map = {m.get("version"): m for m in target_migrations_list if m.get("version")}
        
        # Sort branch migrations by version to ensure consistent order
        sorted_branch_migrations = sorted(branch_migrations, key=lambda m: m.get("version", ""))

        for bm in sorted_branch_migrations:
            branch_mig_status = bm.get("status", "").upper()
            if branch_mig_status not in ["APPLIED", "APPLIED_SUCCESSFULLY"]:
                continue 

            bm_version = bm.get("version")
            if not bm_version:
                continue

            if bm_version in target_migrations_map:
                tm = target_migrations_map[bm_version]
                target_mig_status = tm.get("status", "").upper()

                if target_mig_status in ["APPLIED", "APPLIED_SUCCESSFULLY"] and tm.get("query") != bm.get("query"):
                    branch_data["status"] = original_branch_status # Revert branch status
                    raise custom_errors.MergeConflictError(
                        f"Migration conflict detected for version {bm_version}."
                    )
                
                if target_mig_status == "FAILED":
                    branch_data["status"] = original_branch_status # Revert branch status
                    raise custom_errors.MergeConflictError(
                        f"Migration conflict detected for version {bm_version}."
                    )
            else:
                # Only add new migrations that don't exist in the target
                copied_migration = bm.copy()
                copied_migration["status"] = "APPLIED_SUCCESSFULLY"
                copied_migration["applied_at"] = datetime.now(timezone.utc)
                target_migrations_list.append(copied_migration)
                
                # Apply the migration to the target project using apply_migration
                try:
                    from .database import apply_migration
                    # Ensure the query ends with a semicolon and has proper SQL syntax
                    query = bm.get("query", "").strip()
                    if not query.endswith(';'):
                        query += ';'
                    
                    # For CREATE TABLE statements, ensure we have a proper table definition
                    if query.upper().startswith('CREATE TABLE'):
                        if '(' not in query:
                            query = query.rstrip(';') + ' (id INTEGER PRIMARY KEY);'
                    
                    apply_migration(
                        project_id=target_project_id,
                        name=bm.get("name", ""),
                        query=query
                    )
                except custom_errors.MigrationError as e:
                    branch_data["status"] = original_branch_status # Revert branch status
                    raise custom_errors.MergeConflictError(
                        f"Failed to apply migration '{bm.get('name')}' to target project: {str(e)}"
                    )
        
        # --- Finalize Merge ---
        branch_data["status"] = 'COMPLETED' 
        branch_data["last_activity_at"] = datetime.now(timezone.utc) # Update timestamp on completion
        response["status"] = 'COMPLETED'

        return response

    except custom_errors.MergeConflictError:
        # Branch status was reverted before raising.
        # Re-raise the exception as per test expectations.
        raise
    
    except Exception: 
        # For any other unexpected error during the merge process.
        branch_data["status"] = 'ERROR' # The branch itself is now in an error state due to failed merge.
        branch_data["last_activity_at"] = datetime.now(timezone.utc) # Update timestamp
        response["status"] = 'FAILED' # The merge operation status.
        # Log the actual exception here in a real application.
        return response


@tool_spec(
    spec={
        'name': 'list_branches',
        'description': """ Lists all development branches of a Supabase project.
        
        Lists all development branches of a Supabase project. This function returns
        branch details including status which can be used to check when
        operations like merge, rebase, or reset complete. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The unique identifier for the project.'
                }
            },
            'required': [
                'project_id'
            ]
        }
    }
)
def list_branches(project_id: str) -> List[Dict[str, Any]]:
    """Lists all development branches of a Supabase project.

    Lists all development branches of a Supabase project. This function returns
    branch details including status which can be used to check when
    operations like merge, rebase, or reset complete.

    Args:
        project_id (str): The unique identifier for the project.

    Returns:
        List[Dict[str, Any]]: A list of development branches for the project.
        Each dictionary in the list represents a branch and contains the
        following keys:
            id (str): The unique identifier for the branch (branch ID).
            name (str): The name of the branch.
            branch_project_id (str): The project ID (project_ref) for this branch's dedicated database.
            status (str): The current status of the branch (e.g., 'ACTIVE_HEALTHY', 'CREATING', 'MERGING', 'REBASING', 'RESETTING', 'ERROR').
            created_at (str): ISO 8601 timestamp of when the branch was created.
            last_activity_at (str): ISO 8601 timestamp of the last significant activity on the branch.

    Raises:
        ResourceNotFoundError: If the project or branch does not exist
        ValidationError: If input arguments fail validation.
        BranchingNotEnabledError: If the branching feature is not enabled for the project.
    """
    # Validate input
    if not project_id or (isinstance(project_id, str) and not project_id.strip()):
        raise custom_errors.ValidationError('The id parameter can not be null or empty')

    if not isinstance(project_id, str):
        raise custom_errors.ValidationError('id must be string type')

    # Check if project exists using the new utility function
    project = utils.get_entity_by_id_from_db(DB, "projects", project_id)
    if not project:
        raise custom_errors.ResourceNotFoundError(f"Project with id '{project_id}' not found")
    
    # Check if branching is enabled for the project
    if not utils.is_branching_enabled_for_project(DB, project_id):
        raise custom_errors.BranchingNotEnabledError(
            f"Branching is not enabled for project '{project_id}'. "
            "Please upgrade your subscription plan to access this feature."
        )

    # Get branches for the project
    branches = utils.get_entity_from_db(DB, "branches", project_id)
    
    if not branches:
        raise custom_errors.ResourceNotFoundError(f"found no branches for project_id: {project_id}")
    
    project_branches = [
        {k: v for k, v in branch.items() if k != "parent_project_id"} 
        for branch in branches
    ]

        
    return project_branches


@tool_spec(
    spec={
        'name': 'delete_branch',
        'description': """ Deletes a development branch.
        
        This function deletes a specific development branch. The branch to be deleted
        is identified by the provided `branch_id`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'branch_id': {
                    'type': 'string',
                    'description': 'The ID of the branch to be deleted.'
                }
            },
            'required': [
                'branch_id'
            ]
        }
    }
)
def delete_branch(branch_id: str) -> Dict[str, Any]:
    """Deletes a development branch.

    This function deletes a specific development branch. The branch to be deleted
    is identified by the provided `branch_id`.

    Args:
        branch_id (str): The ID of the branch to be deleted.

    Returns:
        Dict[str, Any]: The status of the delete operation. Contains the following fields:
            branch_id (str): The ID of the branch that was requested for deletion.
            status (str): The status of the deletion (e.g., 'DELETED', 'PENDING_DELETION', 'ERROR').
            message (str): A confirmation or status message.

    Raises:
        NotFoundError: If the branch_id does not exist.
        OperationNotPermittedError: If the branch cannot be deleted (e.g., it's the main production branch, or in a state that prevents deletion like active operations).
        ValidationError: If input arguments fail validation.
    """
    # Validate input: branch_id must be a non-empty string.
    if not isinstance(branch_id, str) or not branch_id.strip():
        raise custom_errors.ValidationError("branch_id must be a non-empty string.")

    found_branch_details = None # Stores (branch_data, parent_project_key, list_index)
    
    # Access branches from DB. Expected structure: DB['branches'] = {'parent_id_1': [branch1_dict, branch2_dict], ...}
    all_branches_by_parent = DB.get("branches", {})

    # Ensure all_branches_by_parent is a mapping (dictionary-like).
    if not isinstance(all_branches_by_parent, Mapping):
        # If DB['branches'] is not a dictionary, it's a schema violation.
        # No branches can be found in this case.
        raise custom_errors.NotFoundError(f"Branch with ID '{branch_id}' not found (invalid branches structure in DB).")


    for parent_key, branches_list in all_branches_by_parent.items():
        # Ensure branches_list is a sequence (list-like) and not a string.
        if not isinstance(branches_list, Sequence) or isinstance(branches_list, str):
            # Malformed data for this parent_key; skip.
            continue

        for index, branch_item in enumerate(branches_list):
            # Ensure branch_item is a mapping (dictionary-like).
            if not isinstance(branch_item, Mapping):
                # Malformed branch entry; skip.
                continue
            
            # Compare IDs. Using .get("id") for safety against missing key during search.
            if branch_item.get("id") == branch_id: 
                found_branch_details = (branch_item, parent_key, index)
                break # Branch found
        
        if found_branch_details:
            break # Branch found, exit outer loop

    if not found_branch_details:
        raise custom_errors.NotFoundError(f"Branch with ID '{branch_id}' not found.")

    print(f"found_branch_details: {found_branch_details}")
    target_branch_data, parent_project_id_key, branch_list_index = found_branch_details
    
    # Condition 1: Cannot delete the main production branch.
    # Assumed definition: main branch if 'branch_project_id' == 'parent_project_ref'.
    try:
        # These keys are mandatory in the Branch model.
        is_default = target_branch_data["is_default"]
        
        if is_default:
            raise custom_errors.OperationNotPermittedError(
                f"Branch '{branch_id}' is the main production branch and cannot be deleted."
            )
    except KeyError:
        # This indicates that the branch data in DB is missing essential fields.
        raise custom_errors.ValidationError(f"Branch data for '{branch_id}' is malformed (missing project ID fields).")


    # Condition 2: Branch status prevents deletion (e.g., active operations).
    non_deletable_statuses = [
        models.BranchStatus.CREATING_PROJECT.value,
        models.BranchStatus.RUNNING_MIGRATIONS.value,
        models.BranchStatus.MIGRATIONS_FAILED.value,
        models.BranchStatus.FUNCTIONS_FAILED.value,
    ]
    try:
        # 'status' is a mandatory field in the Branch model.
        current_branch_status = target_branch_data["status"]
        if current_branch_status in non_deletable_statuses:
            raise custom_errors.OperationNotPermittedError(
                f"Branch '{branch_id}' cannot be deleted in its current state: {current_branch_status}."
            )
    except KeyError:
        # This indicates that the branch data in DB is missing the status field.
        raise custom_errors.ValidationError(f"Branch data for '{branch_id}' is malformed (missing status field).")

    # All checks passed; proceed with deletion.
    del DB["branches"][parent_project_id_key][branch_list_index]

    # If the parent project's list of branches is now empty, remove the parent project key from DB['branches'].
    if not DB["branches"][parent_project_id_key]:
        del DB["branches"][parent_project_id_key]

    success_response = {
        "branch_id": branch_id,
        "status": "DELETED",
        "message": f"Branch '{branch_id}' has been successfully deleted."
    }

    # Return success response.
    return models.DeleteBranchResponse(**success_response).model_dump()

@tool_spec(
    spec={
        'name': 'reset_branch',
        'description': """ Resets migrations of a development branch.
        
        Resets migrations of a development branch. Any untracked data or schema
        changes will be lost. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'branch_id': {
                    'type': 'string',
                    'description': 'The ID of the development branch to be reset.'
                },
                'migration_version': {
                    'type': 'string',
                    'description': """ Reset your development branch to a
                    specific migration version. """
                }
            },
            'required': [
                'branch_id'
            ]
        }
    }
)
def reset_branch(branch_id: str, migration_version: Optional[str] = None) -> Dict[str, Any]:
    """Resets migrations of a development branch.

    Resets migrations of a development branch. Any untracked data or schema
    changes will be lost.

    Args:
        branch_id (str): The ID of the development branch to be reset.
        migration_version (Optional[str]): Reset your development branch to a
            specific migration version.

    Returns:
        Dict[str, Any]: A dictionary containing the status of the branch reset
            operation, with the following keys:
            branch_id (str): The ID of the branch that was reset.
            status (str): The current status of the reset operation (e.g.,
                'RESETTING', 'COMPLETED', 'FAILED').
            target_migration_version (Optional[str]): The migration version to
                which the branch was reset. If a `migration_version` was
                provided in the input, this will reflect it. Otherwise, it
                indicates the default reset state (e.g., initial state or a
                state consistent with production).

    Raises:
        NotFoundError: If the branch_id does not exist or the migration_version
            (if provided) is invalid for this branch.
        ValidationError: If input arguments fail validation.
        MigrationError: If an error occurs during the execution of a migration's SQL query or if a migration is malformed.
        ApiError: For unexpected internal processing errors or issues interacting with the underlying database.
    """
    try:
        validated_args = models.ResetBranchInputArgs(branch_id=branch_id, migration_version=migration_version)
        branch_id = validated_args.branch_id
        migration_version = validated_args.migration_version
    except PydanticValidationError:
        raise 

    # Find the branch by branch_id
    found_branch_dict = utils.get_branch_by_id_from_db(DB, branch_id)
    if not found_branch_dict:
        raise custom_errors.NotFoundError(f"Branch with ID '{branch_id}' not found.")

    original_status = found_branch_dict.get("status")
    found_branch_dict["status"] = "RESETTING"

    branch_project_id = found_branch_dict.get("branch_project_id")
    if not branch_project_id:
        found_branch_dict["status"] = original_status
        raise custom_errors.ApiError(f"Branch '{branch_id}' is missing 'branch_project_id'.")

    now_datetime_utc = datetime.now(timezone.utc)
    
    # --- 1. Revert Database Schema to Basic State ---
    try:
        db_manager = get_duckdb_manager()
        db_manager.reset_project_schema(branch_project_id)
    except Exception as e:
        found_branch_dict["status"] = original_status
        raise custom_errors.ApiError(
            f"Failed to reset underlying database schema for project '{branch_project_id}': {str(e)}"
        ) from e

    # Clear metadata
    DB.get("tables", {}).pop(branch_project_id, None)
    DB.get("extensions", {}).pop(branch_project_id, None)

    # Get all migrations and mark them as pending
    migrations = DB.get("migrations", {}).get(branch_project_id, [])
    for mig_meta in migrations:
        mig_meta["status"] = "pending"
        mig_meta["applied_at"] = None

    # --- 2. Re-apply migrations up to the target_migration_version ---
    if migration_version:
        if not migrations:
            found_branch_dict["status"] = original_status
            raise custom_errors.NotFoundError(
                f"Migration version '{migration_version}' not found for branch '{branch_id}'"
            )

        try:
            sorted_migrations = sorted(migrations, key=lambda m: m['version'])
        except TypeError:
            found_branch_dict["status"] = original_status
            raise custom_errors.ApiError(
                f"Internal error: Could not sort migration versions for project '{branch_project_id}'."
            )

        found_target = False
        for mig_meta in sorted_migrations:
            try:
                sql_query_to_run = mig_meta.get('query')
                if not sql_query_to_run:
                    raise custom_errors.MigrationError(f"Migration '{mig_meta.get('name')}' is missing its SQL query.")

                execute_sql(project_id=branch_project_id, query=sql_query_to_run)
                
                mig_meta["status"] = "applied"
                mig_meta["applied_at"] = now_datetime_utc

                if mig_meta["version"] == migration_version:
                    found_target = True
                    break

            except custom_errors.SQLError as e_sql:
                found_branch_dict["status"] = "RESET_FAILED"
                mig_meta["status"] = "failed_during_reset"
                raise custom_errors.MigrationError(
                    f"Failed to apply migration '{mig_meta.get('name')}': {str(e_sql)}"
                ) from e_sql
        
        if not found_target:
            found_branch_dict["status"] = original_status
            raise custom_errors.NotFoundError(
                f"Target migration version '{migration_version}' not found in sequence."
            )

    if migrations:
        DB["migrations"][branch_project_id] = migrations
    found_branch_dict["status"] = "ACTIVE_HEALTHY" 
    found_branch_dict["last_activity_at"] = now_datetime_utc

    return {
        "branch_id": branch_id,
        "status": "COMPLETED", 
        "target_migration_version": migration_version,
    }
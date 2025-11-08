from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
"""
SupaBase API Simulation

This package provides a simulation of the Supabase API functionality.

"""
import importlib
import os
import json
import tempfile
from typing import Dict, Any
from pydantic import ValidationError
from .SimulationEngine.db import DB, load_state, save_state
from .SimulationEngine.models import GetCostInputArgs, ConfirmCostArgs
from .SimulationEngine import custom_errors, utils
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
"list_organizations": "supabase.organization.list_organizations",
"get_organization": "supabase.organization.get_organization",
"list_projects": "supabase.project.list_projects",
"get_project": "supabase.project.get_project",
"create_project": "supabase.project.create_project",
"pause_project": "supabase.project.pause_project",
"restore_project": "supabase.project.restore_project",
"get_project_url": "supabase.project.get_project_url",
"generate_typescript_types": "supabase.project.generate_typescript_types",
"get_anon_key": "supabase.project.get_anon_key",
"get_cost": "supabase.get_cost",
"confirm_cost": "supabase.confirm_cost",
"create_branch": "supabase.branch.create_branch",
"list_branches": "supabase.branch.list_branches",
"delete_branch": "supabase.branch.delete_branch",
"merge_branch": "supabase.branch.merge_branch",
"reset_branch": "supabase.branch.reset_branch",
"rebase_branch": "supabase.branch.rebase_branch",
"list_tables": "supabase.database.list_tables",
"list_extensions": "supabase.database.list_extensions",
"list_migrations": "supabase.database.list_migrations",
"apply_migration": "supabase.database.apply_migration",
"execute_sql": "supabase.database.execute_sql",
"list_edge_functions": "supabase.edge.list_edge_functions",
"deploy_edge_function": "supabase.edge.deploy_edge_function",
"get_logs": "supabase.logs.get_logs",
}

# Utils map
_utils_map = {
    "update_project_status_and_cascade": "supabase.SimulationEngine.utils.update_project_status_and_cascade",
    "get_entity_by_id": "supabase.SimulationEngine.utils.get_entity_by_id",
    "get_entity_from_db": "supabase.SimulationEngine.utils.get_entity_from_db",
    "get_entity_by_id_from_db": "supabase.SimulationEngine.utils.get_entity_by_id_from_db",
    "get_projects_for_organization": "supabase.SimulationEngine.utils.get_projects_for_organization",
    "get_tables_by_project_and_schemas": "supabase.SimulationEngine.utils.get_tables_by_project_and_schemas",
    "generate_unique_id": "supabase.SimulationEngine.utils.generate_unique_id",
    "get_main_entities": "supabase.SimulationEngine.utils.get_main_entities",
    "name_to_slug": "supabase.SimulationEngine.utils.name_to_slug",
    "is_branching_enabled_for_project": "supabase.SimulationEngine.utils.is_branching_enabled_for_project",
    "validate_project_for_sql_execution": "supabase.SimulationEngine.utils.validate_project_for_sql_execution",
    "get_project_postgres_version": "supabase.SimulationEngine.utils.get_project_postgres_version",
    "format_sql_error_message": "supabase.SimulationEngine.utils.format_sql_error_message",
    "get_cost_parameter": "supabase.SimulationEngine.utils.get_cost_parameter",
    "update_cost_parameter": "supabase.SimulationEngine.utils.update_cost_parameter",
    "map_db_type_to_typescript": "supabase.SimulationEngine.utils.map_db_type_to_typescript",
    "update_project_creation_defaults": "supabase.SimulationEngine.utils.update_project_creation_defaults",
    "get_branch_by_id_from_db": "supabase.SimulationEngine.utils.get_branch_by_id_from_db",
    "find_branch_in_db": "supabase.SimulationEngine.utils.find_branch_in_db",
    "create_extension_in_db": "supabase.SimulationEngine.utils.create_extension_in_db",
    "add_cost_information_to_project": "supabase.SimulationEngine.utils.add_cost_information_to_project",
    "create_new_organization": "supabase.SimulationEngine.utils.create_new_organization",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())

# --- Main get_cost function ---
@tool_spec(
    spec={
        'name': 'get_cost',
        'description': """ Gets the cost of creating a new project or branch.
        
        Gets the cost of creating a new project or branch. Never assume organization as costs can be different for each. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'type': {
                    'type': 'string',
                    'description': "The type of item for which the cost is being requested. Must be 'project' or 'branch'."
                },
                'organization_id': {
                    'type': 'string',
                    'description': 'The organization ID.'
                }
            },
            'required': [
                'type',
                'organization_id'
            ]
        }
    }
)
def get_cost(type: str, organization_id: str) -> Dict[str, Any]: 
    """Gets the cost of creating a new project or branch.

    Gets the cost of creating a new project or branch. Never assume organization as costs can be different for each.

    Args:
        type (str): The type of item for which the cost is being requested. Must be 'project' or 'branch'.
        organization_id (str): The organization ID.

    Returns:
        Dict[str, Any]: A dictionary containing details of the cost with the following keys:
            type (str): The type of item for which the cost is calculated (e.g., 'project', 'branch').
            amount (float): The cost amount.
            currency (str): The currency of the cost (e.g., 'USD').
            recurrence (str): The recurrence interval of the cost (e.g., 'monthly', 'one-time').
            description (str): A human-readable description of the cost item.

    Raises:
        NotFoundError: If the organization_id does not exist.
        InvalidInputError: If input 'type' is invalid or org plan data is problematic.
        ValidationError: If inputs fail Pydantic validation.
    """
    try:
        validated_args = GetCostInputArgs(type=type, organization_id=organization_id)
    except ValidationError as e:
        print_log(f"Pydantic validation error: {e}")
        raise

    cost_type = validated_args.type
    org_id = validated_args.organization_id

    if cost_type == 'branch':
        cost_amount = utils.get_cost_parameter('branch_hourly')
        recurrence = 'hourly'
        description = f"Standard cost for one new branch: ${cost_amount:.5f} per hour."
        return {'type': 'branch', 'recurrence': recurrence, 'currency': utils.get_cost_parameter('default_currency'), 'amount': cost_amount, 'description': description}

    elif cost_type == 'project':
        organizations = DB.get('organizations', [])
        org_details = None
        for org in organizations:
            if isinstance(org, dict) and org.get('id') == org_id:
                org_details = org
                break
        if org_details is None:
            raise custom_errors.NotFoundError(f"Organization with ID '{org_id}' not found.")
        
        org_plan = org_details.get('plan')
        if not org_plan: # Ensure plan exists
            raise custom_errors.InvalidInputError(f"Organization '{org_id}' has no plan information.")

        all_projects = DB.get('projects', [])
        active_projects_for_org = [
            p for p in all_projects
            if p.get('organization_id') == org_id and
               p.get('status') not in ['INACTIVE', 'GOING_DOWN', 'REMOVED']
        ]

        project_cost_amount = 0.0
        if org_plan.lower() != 'free': # Use .lower() for case-insensitivity
            if len(active_projects_for_org) > 0: # Cost applies if it's not the first active project on a paid plan
                project_cost_amount = utils.get_cost_parameter('project_monthly')
        
        recurrence = 'monthly'
        description = f"Estimated cost for one new project in organization '{org_details.get('name', org_id)}' (Plan: {org_plan}): ${project_cost_amount:.2f} per month."
        if project_cost_amount == 0 and org_plan.lower() != 'free':
            description = f"The first active project in organization '{org_details.get('name', org_id)}' (Plan: {org_plan}) is included. Next project cost: ${utils.get_cost_parameter('project_monthly'):.2f} per month."
        elif org_plan.lower() == 'free':
             description = f"Projects on the 'free' plan for organization '{org_details.get('name', org_id)}' do not incur direct monthly costs from this calculation (limits may apply)."


        return {'type': 'project', 'recurrence': recurrence, 'currency': utils.get_cost_parameter('default_currency'),'amount': project_cost_amount, 'description': description}
    
    # This else case should not be reached if Pydantic's Literal for 'type' works correctly.
    else: # Should be caught by Pydantic validation on 'type'
        raise custom_errors.InvalidInputError(f"Unknown cost type: {cost_type}")



@tool_spec(
    spec={
        'name': 'confirm_cost',
        'description': """ Ask the user to confirm their understanding of the cost of creating a new project or branch.
        
        This function asks the user to confirm their understanding of the cost of creating a new project or branch.
        It requires that `get_cost` be called first. It returns a unique ID for this confirmation,
        which should be passed to `create_project` or `create_branch`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'type': {
                    'type': 'string',
                    'description': 'The type of item for which the cost is being confirmed. Must be "project" or "branch".'
                },
                'recurrence': {
                    'type': 'string',
                    'description': 'The recurrence pattern of the cost. Must be "hourly" or "monthly".'
                },
                'amount': {
                    'type': 'number',
                    'description': 'The numerical amount of the cost.'
                }
            },
            'required': [
                'type',
                'recurrence',
                'amount'
            ]
        }
    }
)
def confirm_cost(type: str, recurrence: str, amount: float) -> Dict[str, Any]:
    """Ask the user to confirm their understanding of the cost of creating a new project or branch.

    This function asks the user to confirm their understanding of the cost of creating a new project or branch.
    It requires that `get_cost` be called first. It returns a unique ID for this confirmation,
    which should be passed to `create_project` or `create_branch`.

    Args:
        type (str): The type of item for which the cost is being confirmed. Must be "project" or "branch".
        recurrence (str): The recurrence pattern of the cost. Must be "hourly" or "monthly".
        amount (float): The numerical amount of the cost.

    Returns:
        Dict[str, Any]: A dictionary representing the user's confirmation of the cost. Contains the following key:
            confirmation_id (str): A unique ID representing the user's confirmation. This ID must be passed to `create_project` or `create_branch`.

    Raises:
        InvalidInputError: If the provided cost details (type, recurrence, amount) are inconsistent, invalid, or do not match a previously obtained quote from `get_cost`.
        ValidationError: If input arguments fail validation.
    """
    # 1. Input validation using Pydantic model based on inputSchema
    try:
        validated_args = ConfirmCostArgs(type=type, recurrence=recurrence, amount=amount)
    except ValidationError:
        # Changed to InvalidInputError to align with the primary Source of Truth (JSON schema),
        # which implies input inconsistencies/invalidity result in InvalidInputError.
        # The message "Input validation failed" is kept as tests expect this generic message.
        raise custom_errors.InvalidInputError("Input validation failed")

    # 2. Business rule validation for amount (using validated amount)
    if validated_args.amount <= 0:
        raise custom_errors.InvalidInputError("Cost amount must be positive.")

    # 3. Find matching unconfirmed quote
    unconfirmed_quote_id_to_remove = None
    matched_quote_details = None
    
    unconfirmed_costs_map = DB.get('unconfirmed_costs', {})

    for quote_id, cost_details_dict in unconfirmed_costs_map.items():
        quote_type = cost_details_dict.get('type')
        quote_recurrence = cost_details_dict.get('recurrence')
        quote_amount = cost_details_dict.get('amount')

        if quote_type is None or quote_recurrence is None or quote_amount is None:
            continue 

        # Compare with validated arguments
        # Using a small epsilon for float comparison.
        if (isinstance(quote_amount, (int, float)) and
            quote_type == validated_args.type and
            quote_recurrence == validated_args.recurrence and
            abs(quote_amount - validated_args.amount) < 1e-9): # Epsilon for float comparison

            matched_quote_details = cost_details_dict
            unconfirmed_quote_id_to_remove = quote_id
            break

    if not matched_quote_details:
        raise custom_errors.InvalidInputError(
            "No matching unconfirmed cost quote found for the provided details."
        )
    
    # 4. Generate confirmation ID
    confirmation_id = utils.generate_unique_id(prefix="costconf_")

    # 5. Store confirmed cost
    if 'costs' not in DB:
        DB['costs'] = {}

    try:
        confirmed_cost_entry = {
            "type": matched_quote_details['type'],
            "amount": matched_quote_details['amount'], 
            "currency": matched_quote_details['currency'], 
            "recurrence": matched_quote_details['recurrence'],
            "description": matched_quote_details['description'],
            "confirmation_id": confirmation_id
        }
    except KeyError as e:
        # This error indicates an internal issue with the structure of the matched quote.
        # Re-raising as InvalidInputError might be misleading, but it's an existing pattern.
        # A more specific internal error could be considered in a broader refactor.
        raise custom_errors.InvalidInputError(
            f"Matched quote is malformed and cannot be confirmed. Missing field: {str(e)}"
        )

    DB['costs'][confirmation_id] = confirmed_cost_entry

    # 6. Remove from unconfirmed_costs
    if unconfirmed_quote_id_to_remove and unconfirmed_quote_id_to_remove in DB.get('unconfirmed_costs', {}):
        del DB['unconfirmed_costs'][unconfirmed_quote_id_to_remove]

    # 7. Return confirmation ID
    return {"confirmation_id": confirmation_id}

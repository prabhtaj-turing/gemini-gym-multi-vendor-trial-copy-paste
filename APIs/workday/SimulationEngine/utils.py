"""Utility helpers for Workday Strategic Sourcing simulations.

This module centralises common constants and helper functions so that API
modules stay lightweight and avoid duplication.
"""

from typing import Any, Dict, List, Tuple, Union, Optional
from datetime import datetime

import re

from .custom_errors import (ValidationError,InvalidAttributeError, UserPatchForbiddenError)

from workday.SimulationEngine import db



# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

ALLOWED_INCLUDE_VALUES: List[str] = [
    "attachments",
    "supplier_category",
    "supplier_groups",
    "default_payment_term",
    "payment_types",
    "default_payment_type",
    "payment_currencies",
    "default_payment_currency",
    "supplier_classification_values",
]

ALLOWED_FILTER_KEYS: List[str] = [
    "updated_at_from",
    "updated_at_to",
    "external_id_empty",
    "external_id_not_empty",
    "external_id_equals",
    "external_id_not_equals",
    "segmentation_status_equals",
    "name",
    "risk",
]

INCLUDE_MAP: Dict[str, Tuple[str, Tuple[str, ...]]] = {
        "attachments": ("attachments", ("attachments",)),
        "supplier_category": ("supplier_category", ("suppliers", "supplier_categories")),
        "supplier_groups": ("supplier_groups", ("suppliers", "supplier_groups")),
        "default_payment_term": ("default_payment_term", ("payments", "payment_terms")),
        "payment_types": ("payment_types", ("payments", "payment_types")),
        "default_payment_type": ("default_payment_type", ("payments", "payment_types")),
        "payment_currencies": ("payment_currencies", ("payments", "payment_currencies")),
        "default_payment_currency": ("default_payment_currency", ("payments", "payment_currencies")),
        "supplier_classification_values": ("supplier_classification_values", ("suppliers", "supplier_classification_values")),
    }

# ---------------------------------------------------------------------------
# Filtering helpers
# ---------------------------------------------------------------------------

def apply_company_filters(companies: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return companies after applying filters.

    Args:
        companies (List[Dict[str, Any]]): List of supplier company records.
        filters (Dict[str, Any]): Mapping of filter keys to values.

    Returns:
        List[Dict[str, Any]]: Filtered companies maintaining original order.
    """
    
    result: List[Dict[str, Any]] = []
    for company in companies:
        match = True
        
        # Handle both old flat format and new nested format
        if "attributes" in company:
            attributes = company["attributes"]
        else:
            attributes = company
        
        for key, value in filters.items():
            # Equality matches
            if key in {"name", "risk"}:
                if attributes.get(key) != value:
                    match = False
                    break

            # External-ID helpers
            elif key == "external_id_empty":
                external_id = attributes.get("external_id")
                has_external_id = external_id and str(external_id).strip()
                if value and has_external_id:  # Filter wants empty but has value
                    match = False
                    break
                elif not value and not has_external_id:  # Filter wants non-empty but is empty
                    match = False
                    break
                    
            elif key == "external_id_not_empty":
                external_id = attributes.get("external_id")
                has_external_id = external_id and str(external_id).strip()
                if value and not has_external_id:  # Filter wants non-empty but is empty
                    match = False
                    break
                elif not value and has_external_id:  # Filter wants empty but has value
                    match = False
                    break
                    
            elif key == "external_id_equals":
                if attributes.get("external_id") != value:
                    match = False
                    break
                    
            elif key == "external_id_not_equals":
                if attributes.get("external_id") == value:
                    match = False
                    break

            # Segmentation status list equality
            elif key == "segmentation_status_equals":
                accepted = value if isinstance(value, list) else [str(value)]
                if attributes.get("segmentation_status") not in accepted:
                    match = False
                    break

            # Updated-at range
            elif key == "updated_at_from":
                ts = attributes.get("updated_at")
                if ts is None or ts < value:
                    match = False
                    break
                    
            elif key == "updated_at_to":
                ts = attributes.get("updated_at")
                if ts is None or ts > value:
                    match = False
                    break

        if match:
            result.append(company)

    return result 

# ---------------------------------------------------------------------------
# Inclusion helpers
# ---------------------------------------------------------------------------

def collect_included_resources(company: Dict[str, Any], requested: List[str]) -> List[Dict[str, Any]]:
    """Return related resources for company according to _include values.

    Args:
        company (Dict[str, Any]): Supplier company object with expected keys:
            - type (str): Always "supplier_companies".
            - id (str|int): Company identifier.
            - attributes (Dict[str, Any]): Core attributes.
            - relationships (Dict[str, Any]): Relationship linkage objects.
        requested (List[str]): Values supplied via the _include query parameter.

    Returns:
        List[Dict[str, Any]]: Related resource objects with keys:
            - type (str): Resource type.
            - id (str|int): Resource identifier.
            - attributes (Dict[str, Any]): Resource-specific attributes.
            - relationships (Dict[str, Any]): Resource relationships (optional).
            - links (Dict[str, Any]): Resource hyperlinks (optional).
    """

    included: List[Dict[str, Any]] = []
    relationships = company.get("relationships", {})

    for inc in requested:
        rel_key, db_path = INCLUDE_MAP.get(inc, (None, None))
        if not rel_key or rel_key not in relationships:
            continue

        rel_data = relationships[rel_key].get("data")
        if not rel_data:
            continue

        # Handle malformed relationship data - should be list or dict
        if isinstance(rel_data, str):
            continue

        rel_items = rel_data if isinstance(rel_data, list) else [rel_data]

        # Traverse database path
        from . import db  # local import to avoid circular dependencies

        db_section: Any = db.DB
        try:
            for part in db_path:
                db_section = db_section[part]
        except KeyError:
            continue

        for item in rel_items:
            rid = str(item.get("id"))
            resource_obj = None

            if isinstance(db_section, dict):
                resource_obj = db_section.get(rid) or next(
                    (v for v in db_section.values() if str(v.get("id")) == rid), None
                )
            elif isinstance(db_section, list):
                resource_obj = next((v for v in db_section if str(v.get("id")) == rid), None)

            if resource_obj:
                included.append(resource_obj)

    return included


def set_company_relationships(
    company: Dict[str, Any], include_relationships: Dict[str, Any]
) -> None:
    """
    Populate a company object's `relationships` section with included relationship data.

    This helper function updates both:
      1. The `relationships` section of the given `company` dictionary.
      2. The internal simulation database (`db.DB`) so related entities are stored
         in the correct location for later retrieval.

    The function uses a predefined mapping (`include_map`) to determine:
        - How each relationship key should be stored in the company object.
        - Where in the database the related entities should be stored.

    Args:
        company (Dict[str, Any]): The company object to update. Will be modified in place.
        include_relationships (Dict[str, Any]): A mapping of relationship names to their
            associated data (e.g., `{"attachments": [...], "supplier_category": {...}}`).

    Example:
        company = {"id": 1, "relationships": {}}
        include_relationships = {
            "attachments": [{"id": 10, "type": "attachments"}]
        }
        set_included_relationships(company, include_relationships)

    Side Effects:
        - Updates the internal `db.DB` simulation data with the related entity objects.

    Notes:
        - Relationship data must be either a dictionary or a list of dictionaries.
        - Strings and unsupported formats will be skipped silently.
    """

    # Ensure the company has a 'relationships' key
    if "relationships" not in company or not isinstance(
        company.get("relationships"), dict
    ):
        company["relationships"] = {}

    # Local import to avoid circular dependency issues
    from . import db

    # Process each requested relationship
    for relationship_key, relationship_data in include_relationships.items():

        # Get the mapped relationship key and its database path
        mapped_key, db_path = INCLUDE_MAP.get(relationship_key, (None, None))
        if not mapped_key or not db_path:
            continue  # Skip unknown relationships

        # Skip invalid or empty data
        if not relationship_data or isinstance(relationship_data, str):
            continue

        # Normalize to a list of dictionaries
        items: List[Dict[str, Any]] = (
            relationship_data
            if isinstance(relationship_data, list)
            else [relationship_data]
        )

        # Navigate to the correct section in the database, creating missing keys as needed
        db_section: Union[Dict, List] = db.DB
        for part in db_path:
            if part not in db_section or not isinstance(db_section[part], (dict, list)):
                # If it's not present, create a new dict to hold data
                db_section[part] = {}
            db_section = db_section[part]

        # Insert/update each related entity in the DB section
        for item in items:
            if not isinstance(item, dict):
                continue  # Skip malformed entries
            relationship_id = str(item.get("id"))
            if not relationship_id:
                continue  # Skip items without IDs

            if isinstance(db_section, dict):
                db_section[relationship_id] = item
            elif isinstance(db_section, list):
                db_section.append(item)

        company["relationships"][relationship_key] = {"data": items}


def add_included_relationships(contract: Dict, include_relationships: List[str]) -> None:
    """
    Helper function to add included relationships to a contract object.
    Args:
        contract (Dict): The contract object to add relationships to
        include_relationships (List[str]): List of relationship names to include
    """

    if 'relationships' not in contract or not contract['relationships']:
        contract['relationships'] = {}

    for relationship in include_relationships:
        if relationship == 'contract_type':
            contract_type_id = contract.get('type')
            if contract_type_id and contract_type_id in db.DB["contracts"]["contract_types"]:
                contract_type = db.DB["contracts"]["contract_types"][contract_type_id]
                contract['relationships']['contract_type'] = {
                    'data': {
                        'type': 'contract_types',
                        'id': contract_type_id,
                        'attributes': contract_type
                    }
                }

        elif relationship == 'spend_category':
            spend_category_id = contract.get('spend_category_id')
            if spend_category_id and spend_category_id in db.DB.get('spend_categories', {}):
                spend_category = db.DB['spend_categories'][spend_category_id]
                contract['relationships']['spend_category'] = {
                    'data': {
                        'type': 'spend_categories',
                        'id': spend_category_id,
                        'attributes': spend_category
                    }
                }

        elif relationship == 'supplier_company':
            supplier_id = contract.get('supplier_id')
            if supplier_id and supplier_id in db.DB.get('suppliers', {}).get('supplier_companies', {}):
                supplier_company = db.DB['suppliers']['supplier_companies'][supplier_id]
                contract['relationships']['supplier_company'] = {
                    'data': {
                        'type': 'supplier_companies',
                        'id': supplier_id,
                        'attributes': supplier_company
                    }
                }

        elif relationship == 'docusign_envelopes':
            contract['relationships']['docusign_envelopes'] = {
                'data': []
            }

        elif relationship == 'adobe_sign_agreements':
            contract['relationships']['adobe_sign_agreements'] = {
                'data': []
            }



def validate_attributes(attributes: Optional[str]) -> None:
    """
    Validates the attributes parameter for SCIM user resource requests.

    This function ensures that only supported attributes are requested when filtering
    user resource responses. It validates against a predefined set of allowed SCIM
    user attributes including core attributes, meta attributes, and nested attributes.

    Args:
        attributes (Optional[str]): Comma-separated list of attribute names to validate.
            Valid attributes include:
            - Core attributes: userName, name, externalId, active, id, schemas
            - Name sub-attributes: name.familyName, name.givenName
            - Role attributes: roles, roles.value, roles.display, roles.primary, roles.type
            - Meta attributes: meta, meta.resourceType, meta.created, meta.lastModified, meta.location
            If None, no validation is performed.

    Returns:
        None: This function performs validation only and returns nothing.

    Raises:
        InvalidAttributeError: If any attribute in the comma-separated list is not
            in the allowed attributes set. The error message includes the invalid
            attributes and the complete list of allowed attributes.
    """
    if attributes is None:
        return
    
    # Handle empty string - treat as None (no filtering)
    if attributes == "":
        return
    
    # Handle whitespace-only attributes - should raise error
    if attributes.strip() == "":
        raise InvalidAttributeError(
            f"Invalid attributes: . "
            f"Allowed attributes: {', '.join(sorted({'userName', 'name', 'name.familyName', 'name.givenName', 'roles', 'roles.value', 'roles.display', 'roles.primary', 'roles.type', 'meta', 'meta.resourceType', 'meta.created', 'meta.lastModified', 'meta.location', 'externalId', 'active', 'id', 'schemas'}))}"
        )
    
    allowed_attributes = {
        "userName", "name", "name.familyName", "name.givenName", 
        "roles", "roles.value", "roles.display", "roles.primary", "roles.type",
        "meta", "meta.resourceType", "meta.created", "meta.lastModified", "meta.location",
        "externalId", "active", "id", "schemas"
    }
    
    requested_attrs = [attr.strip() for attr in attributes.split(",") if attr.strip()]
    invalid_attrs = [attr for attr in requested_attrs if attr not in allowed_attributes]
    
    if invalid_attrs:
        raise InvalidAttributeError(
            f"Invalid attributes: {', '.join(invalid_attrs)}. "
            f"Allowed attributes: {', '.join(sorted(allowed_attributes))}"
        )


def apply_filter(users: List[Dict[str, Any]], filter_expr: str) -> List[Dict[str, Any]]:
    """
    Applies a SCIM-compliant filter expression to a list of user objects.

    This function serves as the main entry point for filtering user collections based
    on SCIM filter expressions. It supports complex expressions with logical operators,
    comparison operators, and nested conditions with proper error handling.

    Args:
        users (List[Dict[str, Any]]): List of user objects to filter. Each user object
            should be a dictionary containing SCIM user attributes such as userName,
            name, roles, meta, etc.
        filter_expr (str): SCIM filter expression string following RFC 7644 syntax.
            Supports logical operators (and, or, not), comparison operators 
            (eq, ne, co, sw, ew, pr, gt, ge, lt, le), and parentheses for grouping.
            Examples:
            - 'userName eq "john.doe@example.com"'
            - 'active eq true and roles.value eq "admin"'
            - 'not (userName sw "test")'

    Returns:
        List[Dict[str, Any]]: Filtered list of user objects that match the filter
            expression. Returns empty list if no users match the criteria.

    Raises:
        ValueError: If the filter expression is malformed, uses unsupported operators,
            or references unsupported attributes. The error message includes the
            original filter expression and the specific parsing error.
    """
    try:
        # Parse and apply the filter expression
        return parse_and_apply_filter(users, filter_expr)
    except Exception as e:
        raise ValueError(f"Invalid filter expression: {filter_expr}. Error: {str(e)}")


def parse_and_apply_filter(users: List[Dict[str, Any]], filter_expr: str) -> List[Dict[str, Any]]:
    """
    Parses and applies a SCIM filter expression with support for logical operators.

    This function recursively parses SCIM filter expressions, handling logical operators
    (and, or, not) and delegating simple expressions to the appropriate handler. It
    implements proper precedence rules where 'not' has the highest precedence.

    Args:
        users (List[Dict[str, Any]]): List of user objects to filter. Each user should
            contain standard SCIM attributes.
        filter_expr (str): SCIM filter expression to parse and apply. Can contain:
            - Logical operators: 'and', 'or', 'not'
            - Parentheses for grouping: '(expression)'
            - Simple comparison expressions: 'attribute operator value'
            Examples:
            - 'active eq true and userName sw "admin"'
            - 'not (roles.value eq "guest")'
            - '(userName co "test" or userName co "demo") and active eq true'

    Returns:
        List[Dict[str, Any]]: Filtered list of users matching the expression criteria.
            For logical operations:
            - 'and': Returns intersection of both sub-expressions
            - 'or': Returns union of both sub-expressions  
            - 'not': Returns users that don't match the sub-expression

    Raises:
        ValueError: If the filter expression has invalid syntax or references
            unsupported attributes. This is typically propagated from the
            apply_simple_filter function for malformed simple expressions.
    """
    # Simple implementation for common SCIM operators
    # This is a basic parser - a production system would use a proper SCIM filter parser
    
    filter_expr = filter_expr.strip()
    
    # Handle parentheses grouping first
    if filter_expr.startswith("(") and filter_expr.endswith(")"):
        # Remove outer parentheses and process the inner expression
        inner_expr = filter_expr[1:-1].strip()
        return parse_and_apply_filter(users, inner_expr)
    
    # Handle "not" operator first (highest precedence)
    if filter_expr.lower().startswith("not "):
        # Extract the expression after "not "
        inner_expr = filter_expr[4:].strip()
        # Handle parentheses for "not (expression)"
        if inner_expr.startswith("(") and inner_expr.endswith(")"):
            inner_expr = inner_expr[1:-1].strip()
        
        # Get users that match the inner expression
        matching_users = parse_and_apply_filter(users, inner_expr)
        matching_ids = {user.get("id") for user in matching_users}
        
        # Return users that DON'T match the inner expression
        return [user for user in users if user.get("id") not in matching_ids]
    
    # Handle parentheses with logical operators
    if "(" in filter_expr and ")" in filter_expr:
        # Find the first complete parentheses group
        paren_start = filter_expr.find("(")
        paren_count = 0
        paren_end = -1
        for i, char in enumerate(filter_expr[paren_start:], paren_start):
            if char == "(":
                paren_count += 1
            elif char == ")":
                paren_count -= 1
                if paren_count == 0:
                    paren_end = i
                    break
        
        if paren_end != -1:
            # Extract the parts before, inside, and after parentheses
            before_paren = filter_expr[:paren_start].strip()
            inside_paren = filter_expr[paren_start + 1:paren_end].strip()
            after_paren = filter_expr[paren_end + 1:].strip()
            
            # Process the parentheses group
            paren_result = parse_and_apply_filter(users, inside_paren)
            
            # Reconstruct the expression with the parentheses result
            if before_paren and after_paren:
                # Handle cases like "expr and (paren_expr) and expr"
                if before_paren.lower().endswith(" and"):
                    left_expr = before_paren[:-4].strip()
                    left_users = parse_and_apply_filter(users, left_expr)
                    left_ids = {user.get("id") for user in left_users}
                    paren_filtered = [user for user in paren_result if user.get("id") in left_ids]
                elif before_paren.lower().endswith(" or"):
                    left_expr = before_paren[:-3].strip()
                    left_users = parse_and_apply_filter(users, left_expr)
                    # Union of left and paren results
                    seen_ids = set()
                    combined_result = []
                    for user in left_users + paren_result:
                        user_id = user.get("id")
                        if user_id not in seen_ids:
                            seen_ids.add(user_id)
                            combined_result.append(user)
                    paren_filtered = combined_result
                else:
                    paren_filtered = paren_result
                
                # Handle the after part
                if after_paren.lower().startswith("and "):
                    right_expr = after_paren[4:].strip()
                    right_users = parse_and_apply_filter(users, right_expr)
                    right_ids = {user.get("id") for user in right_users}
                    return [user for user in paren_filtered if user.get("id") in right_ids]
                elif after_paren.lower().startswith("or "):
                    right_expr = after_paren[3:].strip()
                    right_users = parse_and_apply_filter(users, right_expr)
                    # Union of paren and right results
                    seen_ids = set()
                    result = []
                    for user in paren_filtered + right_users:
                        user_id = user.get("id")
                        if user_id not in seen_ids:
                            seen_ids.add(user_id)
                            result.append(user)
                    return result
                else:
                    return paren_filtered
            elif before_paren:
                # Handle expressions that end with parentheses
                return paren_result
            elif after_paren:
                # Handle expressions that start with parentheses
                if after_paren.lower().startswith("and "):
                    right_expr = after_paren[4:].strip()
                    right_users = parse_and_apply_filter(users, right_expr)
                    right_ids = {user.get("id") for user in right_users}
                    return [user for user in paren_result if user.get("id") in right_ids]
                elif after_paren.lower().startswith("or "):
                    right_expr = after_paren[3:].strip()
                    right_users = parse_and_apply_filter(users, right_expr)
                    # Union of paren and right results
                    seen_ids = set()
                    result = []
                    for user in paren_result + right_users:
                        user_id = user.get("id")
                        if user_id not in seen_ids:
                            seen_ids.add(user_id)
                            result.append(user)
                    return result
                else:
                    return paren_result
            else:
                return paren_result
    
    # Handle logical operators (and, or) - preserve case for attribute names
    if " and " in filter_expr.lower():
        # Find the position of " and " case-insensitively but preserve original case
        lower_expr = filter_expr.lower()
        and_pos = lower_expr.find(" and ")
        parts = [filter_expr[:and_pos].strip(), filter_expr[and_pos + 5:].strip()]
        left_users = parse_and_apply_filter(users, parts[0])
        right_users = parse_and_apply_filter(users, parts[1])
        # Return intersection of both filters
        left_ids = {user.get("id") for user in left_users}
        return [user for user in right_users if user.get("id") in left_ids]
    
    if " or " in filter_expr.lower():
        # Find the position of " or " case-insensitively but preserve original case
        lower_expr = filter_expr.lower()
        or_pos = lower_expr.find(" or ")
        parts = [filter_expr[:or_pos].strip(), filter_expr[or_pos + 4:].strip()]
        left_users = parse_and_apply_filter(users, parts[0])
        right_users = parse_and_apply_filter(users, parts[1])
        # Return union of both filters
        seen_ids = set()
        result = []
        for user in left_users + right_users:
            user_id = user.get("id")
            if user_id not in seen_ids:
                seen_ids.add(user_id)
                result.append(user)
        return result
    
    # Parse simple expressions like 'attribute operator value'
    return apply_simple_filter(users, filter_expr)


def apply_simple_filter(users: List[Dict[str, Any]], filter_expr: str) -> List[Dict[str, Any]]:
    """
    Applies a simple SCIM filter expression of the form 'attribute operator value'.

    This function handles basic SCIM filter expressions that consist of a single
    attribute, comparison operator, and value. It validates both the attribute
    and operator before applying the filter to the user collection.

    Args:
        users (List[Dict[str, Any]]): List of user objects to filter against.
        filter_expr (str): Simple filter expression in the format 'attribute operator value'.
            Examples:
            - 'userName eq "john.doe@example.com"'
            - 'active eq true'
            - 'roles.value co "admin"'
            - 'meta.created gt "2024-01-01T00:00:00Z"'

    Returns:
        List[Dict[str, Any]]: List of users that satisfy the filter condition.
            Empty list if no users match the criteria.

    Raises:
        ValueError: If the filter expression format is invalid (less than 2 parts for pr operator, less than 3 for others),
            if the attribute is not supported, or if the operator is not recognized.
            Supported operators: eq, ne, co, sw, ew, pr, gt, ge, lt, le.
    """
    # Parse expression like 'userName eq "john.doe@example.com"' or 'externalId pr'
    parts = filter_expr.split()
    if len(parts) < 2:
        raise ValueError(f"Invalid filter format: {filter_expr}")
    
    attribute = parts[0]
    operator = parts[1].lower()
    
    # Special handling for 'pr' (present) operator which doesn't need a value
    if operator == "pr":
        if len(parts) != 2:
            raise ValueError(f"Invalid filter format: {filter_expr}")
        value = None
    else:
        if len(parts) < 3:
            raise ValueError(f"Invalid filter format: {filter_expr}")
        value = " ".join(parts[2:]).strip('"\'')  # Remove quotes
    
    # Validate attribute
    allowed_filter_attributes = {
        "userName", "name", "name.familyName", "name.givenName", 
        "roles", "roles.value", "roles.display", "roles.primary", "roles.type",
        "externalId", "active", 
        "meta", "meta.resourceType", "meta.created", "meta.lastModified", "meta.location",
        "id", "schemas"
    }
    
    if attribute not in allowed_filter_attributes:
        raise ValueError(f"Unsupported filter attribute: {attribute}")
    
    # Validate operator
    allowed_operators = {"eq", "ne", "co", "sw", "ew", "pr", "gt", "ge", "lt", "le"}
    if operator not in allowed_operators:
        raise ValueError(f"Unsupported filter operator: {operator}. Supported operators: {', '.join(sorted(allowed_operators))}")
    
    # Apply filter
    filtered_users = []
    for user in users:
        if evaluate_filter_condition(user, attribute, operator, value):
            filtered_users.append(user)
    
    return filtered_users


def evaluate_filter_condition(user: Dict[str, Any], attribute: str, operator: str, value: str) -> bool:
    """
    Evaluates a single filter condition against a user object.

    This function applies a specific comparison operator to compare a user's attribute
    value against a filter value. It handles different data types (boolean, numeric,
    string) appropriately and supports all SCIM comparison operators.

    Args:
        user (Dict[str, Any]): User object containing SCIM attributes to evaluate against.
        attribute (str): The attribute name to extract from the user object.
            Can be nested (e.g., 'name.givenName', 'roles.value').
        operator (str): Comparison operator to apply. Supported operators:
            - 'eq': Equals (exact match)
            - 'ne': Not equals  
            - 'co': Contains (substring match)
            - 'sw': Starts with (prefix match)
            - 'ew': Ends with (suffix match)
            - 'pr': Present (attribute has non-null value)
            - 'gt', 'ge', 'lt', 'le': Comparison operators for numeric/date values
        value (str): The value to compare against. For 'pr' operator, this is ignored.

    Returns:
        bool: True if the user satisfies the filter condition, False otherwise.
            Returns False if the attribute is not present (except for 'pr' operator).

    Raises:
        None: This function handles all exceptions internally and returns False
            for any evaluation errors to maintain filter robustness.
    """
    # Get the attribute value from the user
    attr_value = get_user_attribute_value(user, attribute)
    
    if operator == "pr":  # present
        if isinstance(attr_value, list):
            return len(attr_value) > 0
        return attr_value is not None
    
    if attr_value is None:
        return False
    
    # Handle list attributes (like roles.value, roles.display, etc.)
    if isinstance(attr_value, list):
        for item in attr_value:
            if evaluate_single_value(item, operator, value):
                return True
        return False
    
    # Handle single values
    return evaluate_single_value(attr_value, operator, value)


def evaluate_single_value(attr_value: Any, operator: str, value: str) -> bool:
    """Helper function to evaluate a single value against the filter condition."""
    # Handle different data types appropriately
    if operator == "eq":  # equals
        if isinstance(attr_value, bool):
            return str(attr_value).lower() == value.lower()
        elif isinstance(attr_value, (int, float)):
            try:
                return float(attr_value) == float(value)
            except ValueError:
                return str(attr_value).lower() == value.lower()
        else:
            return str(attr_value).lower() == value.lower()
    
    elif operator == "ne":  # not equals
        if isinstance(attr_value, bool):
            return str(attr_value).lower() != value.lower()
        elif isinstance(attr_value, (int, float)):
            try:
                return float(attr_value) != float(value)
            except ValueError:
                return str(attr_value).lower() != value.lower()
        else:
            return str(attr_value).lower() != value.lower()
    
    # For string-based operations, convert to string
    attr_str = str(attr_value).lower()
    value_str = value.lower()
    
    if operator == "co":  # contains
        return value_str in attr_str
    elif operator == "sw":  # starts with
        return attr_str.startswith(value_str)
    elif operator == "ew":  # ends with
        return attr_str.endswith(value_str)
    elif operator == "gt":  # greater than
        return compare_values(attr_value, value, "gt")
    elif operator == "ge":  # greater than or equal
        return compare_values(attr_value, value, "ge")
    elif operator == "lt":  # less than
        return compare_values(attr_value, value, "lt")
    elif operator == "le":  # less than or equal
        return compare_values(attr_value, value, "le")
    
    return False


def compare_values(attr_value: Any, filter_value: str, operator: str) -> bool:
    """
    Compares values using relational operators with type-aware comparison logic.

    This function performs intelligent comparison between attribute values and filter
    values, attempting numeric comparison first, then datetime comparison for ISO 8601
    strings, and falling back to lexicographical string comparison.

    Args:
        attr_value (Any): The attribute value from the user object to compare.
            Can be numeric (int, float), string, or other types.
        filter_value (str): The filter value to compare against, always provided as string.
        operator (str): The comparison operator to apply. Must be one of:
            - 'gt': Greater than
            - 'ge': Greater than or equal to
            - 'lt': Less than
            - 'le': Less than or equal to

    Returns:
        bool: Result of the comparison operation. Returns True if the comparison
            is satisfied, False otherwise. Falls back to False if all comparison
            attempts fail due to type incompatibility or parsing errors.

    Raises:
        None: This function handles all exceptions internally and returns False
            for any comparison errors to maintain robustness during filtering.
    """
    try:
        # Try numeric comparison first
        if isinstance(attr_value, (int, float)):
            try:
                filter_num = float(filter_value)
                if operator == "gt":
                    return attr_value > filter_num
                elif operator == "ge":
                    return attr_value >= filter_num
                elif operator == "lt":
                    return attr_value < filter_num
                elif operator == "le":
                    return attr_value <= filter_num
            except ValueError:
                pass
        
        # Try datetime comparison for ISO 8601 strings
        if isinstance(attr_value, str) and is_iso_datetime(attr_value) and is_iso_datetime(filter_value):
            from datetime import datetime
            try:
                attr_dt = datetime.fromisoformat(attr_value.replace('Z', '+00:00'))
                filter_dt = datetime.fromisoformat(filter_value.replace('Z', '+00:00'))
                if operator == "gt":
                    return attr_dt > filter_dt
                elif operator == "ge":
                    return attr_dt >= filter_dt
                elif operator == "lt":
                    return attr_dt < filter_dt
                elif operator == "le":
                    return attr_dt <= filter_dt
            except ValueError:
                pass
        
        # Fall back to lexicographical string comparison
        attr_str = str(attr_value).lower()
        filter_str = filter_value.lower()
        if operator == "gt":
            return attr_str > filter_str
        elif operator == "ge":
            return attr_str >= filter_str
        elif operator == "lt":
            return attr_str < filter_str
        elif operator == "le":
            return attr_str <= filter_str
            
    except Exception:
        # If all comparisons fail, return False
        return False
    
    return False


def is_iso_datetime(value: str) -> bool:
    """
    Checks if a string appears to be an ISO 8601 formatted datetime.

    This function performs a basic pattern check to identify strings that look like
    ISO 8601 datetime format without attempting full parsing. It's used as a
    preliminary check before attempting datetime comparison operations.

    Args:
        value (str): The string value to check for ISO 8601 datetime format.
            Expected format patterns include:
            - YYYY-MM-DDTHH:MM:SS
            - YYYY-MM-DDTHH:MM:SSZ  
            - YYYY-MM-DDTHH:MM:SS+HH:MM

    Returns:
        bool: True if the string appears to match ISO 8601 datetime patterns,
            False otherwise. Returns False for non-string inputs.

    Raises:
        None: This function handles all input types safely and never raises exceptions.
    """
    if not isinstance(value, str):
        return False
    
    # Basic check for ISO 8601 format patterns
    iso_patterns = [
        len(value) >= 19,  # Minimum length for YYYY-MM-DDTHH:MM:SS
        'T' in value,      # Has date/time separator
        '-' in value[:10], # Has date separators
        ':' in value[11:], # Has time separators
    ]
    
    return all(iso_patterns)


def get_user_attribute_value(user: Dict[str, Any], attribute: str) -> Any:
    """
    Extracts the value of a specified attribute from a user object.

    This function handles both simple and nested attribute access for SCIM user objects,
    including special handling for multi-valued attributes like roles. It supports
    dot notation for nested attributes and returns appropriate values for complex
    attributes.

    Args:
        user (Dict[str, Any]): User object containing SCIM attributes.
        attribute (str): The attribute path to extract. Supported formats:
            - Simple attributes: 'userName', 'active', 'id', 'schemas'
            - Nested attributes: 'name.givenName', 'name.familyName'
            - Meta attributes: 'meta.created', 'meta.lastModified', 'meta.resourceType', 'meta.location'
            - Role attributes: 'roles', 'roles.value', 'roles.display', 'roles.primary', 'roles.type'

    Returns:
        Any: The attribute value if found, None if not present. For role attributes,
            returns a list of the specified role field values. For complex attributes
            like 'name' or 'meta', returns the entire sub-object.

    Raises:
        None: This function handles missing attributes gracefully by returning None
            rather than raising exceptions.
    """
    if attribute == "userName":
        return user.get("userName")
    elif attribute == "name":
        return user.get("name")
    elif attribute == "name.familyName":
        return user.get("name", {}).get("familyName")
    elif attribute == "name.givenName":
        return user.get("name", {}).get("givenName")
    elif attribute == "externalId":
        return user.get("externalId")
    elif attribute == "active":
        return user.get("active")
    elif attribute == "id":
        return user.get("id")
    elif attribute == "schemas":
        return user.get("schemas")
    elif attribute == "meta":
        return user.get("meta")
    elif attribute == "meta.resourceType":
        return user.get("meta", {}).get("resourceType")
    elif attribute == "meta.created":
        return user.get("meta", {}).get("created")
    elif attribute == "meta.lastModified":
        return user.get("meta", {}).get("lastModified")
    elif attribute == "meta.location":
        return user.get("meta", {}).get("location")
    elif attribute == "roles":
        roles = user.get("roles", [])
        return [role.get("value", "") for role in roles] if roles else []
    elif attribute == "roles.value":
        roles = user.get("roles", [])
        return [role.get("value", "") for role in roles] if roles else []
    elif attribute == "roles.display":
        roles = user.get("roles", [])
        return [role.get("display", "") for role in roles] if roles else []
    elif attribute == "roles.primary":
        roles = user.get("roles", [])
        return [role.get("primary", False) for role in roles] if roles else []
    elif attribute == "roles.type":
        roles = user.get("roles", [])
        return [role.get("type", "") for role in roles] if roles else []
    
    return None


def apply_sorting(users: List[Dict[str, Any]], sortBy: str, sortOrder: str) -> List[Dict[str, Any]]:
    """
    Applies sorting to a list of user objects based on specified criteria.

    This function sorts the user collection by a specified attribute in either
    ascending or descending order. It supports sorting by key user attributes
    with proper string conversion for consistent sorting behavior.

    Args:
        users (List[Dict[str, Any]]): List of user objects to sort.
        sortBy (str): The attribute to sort by. Supported values:
            - 'id': Sort by SCIM resource identifier
            - 'externalId': Sort by external system identifier
        sortOrder (str): The sort direction. Supported values:
            - 'ascending': Sort in ascending order (A-Z, 0-9)
            - 'descending': Sort in descending order (Z-A, 9-0)

    Returns:
        List[Dict[str, Any]]: New sorted list of user objects. If sortBy is not
            supported, returns the original list unchanged. Empty attributes are
            treated as empty strings for sorting consistency.

    Raises:
        None: This function handles all sorting operations safely and returns
            the original list if any errors occur during sorting.
    """
    reverse = sortOrder.lower() == "descending"
    
    if sortBy == "id":
        return sorted(users, key=lambda x: str(x.get("id", "")), reverse=reverse)
    elif sortBy == "externalId":
        return sorted(users, key=lambda x: str(x.get("externalId", "")), reverse=reverse)
    
    return users


def filter_attributes(users: List[Dict[str, Any]], attributes: str) -> List[Dict[str, Any]]:
    """
    Filters user objects to return only the specified attributes.

    This function creates filtered copies of user objects containing only the
    requested attributes. It handles both simple and nested attributes, with
    special logic for complex attributes like roles and meta objects. The function
    ensures SCIM compliance by always including required fields like schemas and id.

    Args:
        users (List[Dict[str, Any]]): List of user objects to filter.
        attributes (str): Comma-separated list of attribute names to include
            in the filtered response. Supported formats:
            - Simple attributes: 'userName', 'active', 'externalId'
            - Nested attributes: 'name.givenName', 'meta.created'
            - Role sub-attributes: 'roles.value', 'roles.display'
            - Complex attributes: 'name', 'roles', 'meta'

    Returns:
        List[Dict[str, Any]]: List of filtered user objects containing only the
            requested attributes. Each filtered user maintains proper SCIM structure
            and includes mandatory fields (schemas, id) for compliance.

    Raises:
        None: This function handles attribute filtering safely, skipping any
            attributes that don't exist in the source user objects.
    """
    requested_attrs = [attr.strip() for attr in attributes.split(",")]
    filtered_users = []
    
    for user in users:
        filtered_user = {}
        
        for attr in requested_attrs:
            if attr == "userName":
                if "userName" in user:
                    filtered_user["userName"] = user["userName"]
            elif attr == "name":
                if "name" in user:
                    filtered_user["name"] = user["name"]
            elif attr.startswith("name."):
                # Handle name sub-attributes by building up the name object with requested fields
                if "name" in user:
                    if "name" not in filtered_user:
                        filtered_user["name"] = {}
                    
                    # Add the specific field to the name object
                    field_name = attr.split(".", 1)[1]  # Get the field name after "name."
                    if field_name in user["name"] and user["name"][field_name] is not None:
                        filtered_user["name"][field_name] = user["name"][field_name]
            elif attr == "roles":
                if "roles" in user:
                    filtered_user["roles"] = user["roles"]
            elif attr.startswith("roles."):
                # Handle role sub-attributes by building up the roles array with requested fields
                if "roles" in user:
                    if "roles" not in filtered_user:
                        # Initialize roles array with empty objects for each role
                        filtered_user["roles"] = [{} for _ in user["roles"]]
                    
                    # Add the specific field to each role
                    field_name = attr.split(".", 1)[1]  # Get the field name after "roles."
                    for i, role in enumerate(user["roles"]):
                        if field_name in role and role[field_name] is not None:
                            filtered_user["roles"][i][field_name] = role[field_name]
            elif attr == "externalId":
                if "externalId" in user:
                    filtered_user["externalId"] = user["externalId"]
            elif attr == "active":
                if "active" in user:
                    filtered_user["active"] = user["active"]
            elif attr == "id":
                if "id" in user:
                    filtered_user["id"] = user["id"]
            elif attr == "schemas":
                if "schemas" in user:
                    filtered_user["schemas"] = user["schemas"]
            elif attr == "meta":
                if "meta" in user:
                    filtered_user["meta"] = user["meta"]
            elif attr.startswith("meta."):
                # Handle meta sub-attributes by building up the meta object with requested fields
                if "meta" in user:
                    if "meta" not in filtered_user:
                        filtered_user["meta"] = {}
                    
                    # Add the specific field to the meta object
                    field_name = attr.split(".", 1)[1]  # Get the field name after "meta."
                    if field_name in user["meta"] and user["meta"][field_name] is not None:
                        filtered_user["meta"][field_name] = user["meta"][field_name]
        
        # Clean up empty complex objects after processing all attributes
        # Remove empty roles list or list containing only empty objects
        if "roles" in filtered_user:
            # Filter out empty role objects
            filtered_user["roles"] = [role for role in filtered_user["roles"] if role]
            # If all roles were empty, remove the roles key entirely
            if not filtered_user["roles"]:
                del filtered_user["roles"]
        
        # Remove empty name object if no sub-attributes were found
        if "name" in filtered_user and not filtered_user["name"]:
            del filtered_user["name"]
        
        # Remove empty meta object if no sub-attributes were found
        if "meta" in filtered_user and not filtered_user["meta"]:
            del filtered_user["meta"]
        
        # Always include schemas and id for SCIM compliance
        if "schemas" in user:
            filtered_user["schemas"] = user["schemas"]
        if "id" not in filtered_user and "id" in user:
            filtered_user["id"] = user["id"]
            
        filtered_users.append(filtered_user)
    
    return filtered_users


def apply_patch_operation(user: Dict[str, Any], operation, user_id: str) -> Dict[str, Any]:
    """
    Applies a single SCIM PATCH operation to a user object.

    This function processes SCIM PATCH operations (add, remove, replace) on user
    resources, implementing business rules validation and proper attribute handling.
    It enforces security policies like preventing self-deactivation and email
    domain changes.

    Args:
        user (Dict[str, Any]): User object to modify. Should contain standard SCIM
            user attributes like userName, name, active, roles, etc.
        operation: PATCH operation object containing:
            - op (str): Operation type ('add', 'remove', 'replace')
            - path (Optional[str]): Attribute path to modify
            - value (Any): Value for add/replace operations
        user_id (str): The ID of the user being modified, used for business rule
            validation and error messages.

    Returns:
        Dict[str, Any]: Modified user object with the PATCH operation applied.
            The original user object is modified in place and returned.

    Raises:
        UserPatchForbiddenError: If the operation violates business rules:
            - Attempting to set active=False (self-deactivation)
            - Attempting to change email domain (SSO policy violation)
    """

    op = operation.op
    path = operation.path
    value = operation.value
    
    # --- Business Logic Validation ---
    # Check for self-deactivation attempt (simulated as forbidden in this environment)
    if path == "active" and value is False:
        raise UserPatchForbiddenError("Self-deactivation is forbidden")
    
    # Check for userName domain validation
    if path == "userName" and value:
        current_username = user.get("userName", "")
        if "@" in current_username and "@" in str(value):
            current_domain = current_username.split("@")[1].lower()  # Case-insensitive domain comparison
            new_domain = str(value).split("@")[1].lower()  # Case-insensitive domain comparison
            # Enforce no domain change without SSO configuration context
            if new_domain != current_domain:
                raise UserPatchForbiddenError("Email domain change is forbidden by SSO policy")

    # --- Apply Operation ---
    if op == "replace":
        return apply_replace_operation(user, path, value)
    elif op == "add":
        return apply_add_operation(user, path, value)
    elif op == "remove":
        return apply_remove_operation(user, path)
    
    return user


def apply_replace_operation(user: Dict[str, Any], path: Optional[str], value: Any) -> Dict[str, Any]:
    """
    Applies a SCIM PATCH replace operation to a user object.

    This function handles the 'replace' operation type, which updates existing
    attribute values. It supports both simple attribute replacement and nested
    attribute updates, while protecting immutable fields from modification.

    Args:
        user (Dict[str, Any]): User object to modify.
        path (Optional[str]): Attribute path to replace. Can be:
            - None: Replace multiple attributes from value object
            - Simple path: 'userName', 'active', 'externalId'
            - Nested path: 'name.givenName', 'name.familyName'
        value (Any): New value to set. For nested paths, should be the specific
            field value. For None path, should be a dictionary of attributes.

    Returns:
        Dict[str, Any]: Modified user object with replaced values.

    Raises:
        None: This function protects immutable fields (id, schemas, created, resourceType)
            but does not raise exceptions for invalid operations.
    """
    if not path:
        # Replace entire user attributes with value (rare case)
        if isinstance(value, dict):
            for key, val in value.items():
                if key not in ["id", "meta", "schemas"]:  # Protect immutable fields
                    user[key] = val
        return user
    
    # Handle nested paths like "name.givenName"
    path_parts = path.split(".")
    
    if len(path_parts) == 1:
        # Simple attribute replacement
        attr = path_parts[0]
        if attr not in ["id", "schemas"]:  # Protect immutable fields
            user[attr] = value
    
    elif len(path_parts) == 2:
        # Nested attribute replacement
        parent_attr, child_attr = path_parts
        if parent_attr == "name":
            if "name" not in user:
                user["name"] = {}
            user["name"][child_attr] = value
        elif parent_attr == "meta" and child_attr not in ["created", "resourceType"]:
            # Allow updating some meta fields but protect immutable ones
            if "meta" not in user:
                user["meta"] = {}
            user["meta"][child_attr] = value
    
    return user


def apply_add_operation(user: Dict[str, Any], path: Optional[str], value: Any) -> Dict[str, Any]:
    """
    Applies a SCIM PATCH add operation to a user object.

    This function handles the 'add' operation type, which adds new values to
    attributes. For array attributes like roles, it appends to existing values.
    For scalar attributes, it behaves like replace operation.

    Args:
        user (Dict[str, Any]): User object to modify.
        path (Optional[str]): Attribute path for the add operation. Can be:
            - None: Add multiple attributes from value object
            - 'roles': Add role(s) to the roles array
            - Other paths: Treated as replace operations
        value (Any): Value(s) to add. For roles, can be a single role object
            or array of role objects. For other attributes, the new value.

    Returns:
        Dict[str, Any]: Modified user object with added values.

    Raises:
        None: This function protects immutable fields and handles type conversion
            safely without raising exceptions.
    """
    if not path:
        # Add attributes to the user
        if isinstance(value, dict):
            for key, val in value.items():
                if key not in ["id", "meta", "schemas"]:  # Protect immutable fields
                    user[key] = val
        return user
    
    # Handle array additions (like roles)
    if path == "roles" and isinstance(value, (list, dict)):
        if "roles" not in user:
            user["roles"] = []
        
        if isinstance(value, list):
            user["roles"].extend(value)
        else:
            user["roles"].append(value)
    else:
        # For non-array attributes, add behaves like replace
        return apply_replace_operation(user, path, value)
    
    return user


def apply_remove_operation(user: Dict[str, Any], path: str) -> Dict[str, Any]:
    """
    Applies a SCIM PATCH remove operation to a user object.

    This function handles the 'remove' operation type, which deletes attributes
    or nested attribute values from user objects. It protects required and
    immutable fields from removal to maintain data integrity.

    Args:
        user (Dict[str, Any]): User object to modify.
        path (str): Attribute path to remove. Can be:
            - Simple path: 'externalId', 'active' (for optional fields)
            - Nested path: 'name.givenName', 'name.familyName'
            Protected fields that cannot be removed: 'id', 'schemas', 'userName', 'meta'

    Returns:
        Dict[str, Any]: Modified user object with specified attribute removed.

    Raises:
        None: This function safely handles attribute removal, ignoring attempts
            to remove non-existent or protected attributes.
    """
    path_parts = path.split(".")
    
    if len(path_parts) == 1:
        # Remove top-level attribute
        attr = path_parts[0]
        if attr not in ["id", "schemas", "userName", "meta"]:  # Protect required fields
            user.pop(attr, None)
    
    elif len(path_parts) == 2:
        # Remove nested attribute
        parent_attr, child_attr = path_parts
        if parent_attr in user and isinstance(user[parent_attr], dict):
            user[parent_attr].pop(child_attr, None)
    
    return user

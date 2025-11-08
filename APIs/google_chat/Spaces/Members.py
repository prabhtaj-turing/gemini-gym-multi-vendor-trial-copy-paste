# APIs/google_chat/Spaces/Members.py

import os
import re
import sys
from datetime import datetime
from google_chat.SimulationEngine import utils
import builtins
from typing import Any, Dict, List, Optional, Union

from pydantic import ValidationError as PydanticValidationError

from common_utils.print_log import print_log
from common_utils.tool_spec_decorator import tool_spec
from google_chat.SimulationEngine.db import DB
from google_chat.SimulationEngine.custom_errors import (
    AdminAccessFilterError,
    AdminAccessNotAllowedError,
    InvalidFilterError,
    InvalidPageSizeError,
    InvalidParentFormatError,
    InvalidUpdateMaskError,
    MembershipAlreadyExistsError,
    MembershipNotFoundError,
    NoUpdatableFieldsError,
    InvalidPageSizeError,
    AdminAccessFilterError,
    InvalidMemberNameFormatError
)
from google_chat.SimulationEngine.models import (
    MemberTypeEnum,
    MembershipInputModel,
    MembershipPatchModel,
    MembershipUpdateMaskModel,
)

sys.path.append("APIs")

# DB and other external dependencies are assumed to be defined elsewhere and accessible.
# For example, DB might be:
# DB = {
#     "Membership": []
# }

@tool_spec(
    spec={
  'name': 'list_space_members',
  'description': 'Lists memberships in a space.',
  'parameters': {
    'type': 'object',
    'properties': {
      'parent': {
        'type': 'string',
        'description': 'Required. The resource name of the space to list memberships for.\nFormat: spaces/{space}'
      },
      'pageSize': {
        'type': 'integer',
        'description': 'Maximum number of memberships to return.\nIf unspecified, at most 100 are returned. Value must be between 1 and 1000, inclusive, if provided.\nDefaults to None.'
      },
      'pageToken': {
        'type': 'string',
        'description': 'Token to retrieve the next page from a previous response. Defaults to None.'
      },
      'filter': {
        'type': 'string',
        'description': "Query filter string to filter memberships by:\n- role = \"ROLE_MEMBER\" or \"ROLE_MANAGER\"\n- member.type = \"HUMAN\" or \"BOT\"\nYou may also use:\n- member.type != \"BOT\"\n- AND/OR operators (restrictions apply)\nIf 'useAdminAccess' is True and a filter is provided, the filter must include\na condition on 'member.type' (e.g., 'member.type = \"HUMAN\"' or 'member.type != \"BOT\"').\nDefaults to None."
      },
      'showGroups': {
        'type': 'boolean',
        'description': 'If True, includes memberships associated with Google Groups. Defaults to None.'
      },
      'showInvited': {
        'type': 'boolean',
        'description': 'If True, includes memberships in the INVITED state. Defaults to None.'
      },
      'useAdminAccess': {
        'type': 'boolean',
        'description': 'If True, enables admin privileges for the listing operation. Defaults to None.'
      }
    },
    'required': [
      'parent'
    ]
  }
}
)

def list(
    parent: str,
    pageSize: Optional[int] = None,
    pageToken: Optional[str] = None,
    filter: Optional[str] = None,
    showGroups: Optional[bool] = None,
    showInvited: Optional[bool] = None,
    useAdminAccess: Optional[bool] = None,
) -> Dict[str, Union[List, str]]:
    """
    Lists memberships in a space.

    Args:
        parent (str): Required. The resource name of the space to list memberships for.
            Format: spaces/{space}
        pageSize (Optional[int]): Maximum number of memberships to return.
            If unspecified, at most 100 are returned. Value must be between 1 and 1000, inclusive, if provided.
            Defaults to None.
        pageToken (Optional[str]): Token to retrieve the next page from a previous response. Defaults to None.
        filter (Optional[str]): "Query filter string to filter memberships by:
            - role = \"ROLE_MEMBER\" or \"ROLE_MANAGER\"
            - member.type = \"HUMAN\" or \"BOT\"
            You may also use:
            - member.type != \"BOT\"
            - AND/OR operators (restrictions apply)
            If 'useAdminAccess' is True and a filter is provided, the filter must include
            a condition on 'member.type' (e.g., 'member.type = \"HUMAN\"' or 'member.type != \"BOT\"').
            Defaults to None."
        showGroups (Optional[bool]): If True, includes memberships associated with Google Groups. Defaults to None.
        showInvited (Optional[bool]): If True, includes memberships in the INVITED state. Defaults to None.
        useAdminAccess (Optional[bool]): If True, enables admin privileges for the listing operation. Defaults to None.

    Returns:
        Dict[str, Union[List, str]]: A dictionary containing:
            - "memberships" (List[Dict[str, Union[str, Dict]]]): A list of membership objects, where each object contains:
                - "name" (str): Resource name of the membership in format `spaces/{space}/members/{member}`.
                - "state" (str): Membership state, one of: "MEMBERSHIP_STATE_UNSPECIFIED", "JOINED", "INVITED", "NOT_A_MEMBER".
                - "role" (str): Membership role, one of: "MEMBERSHIP_ROLE_UNSPECIFIED", "ROLE_MEMBER", "ROLE_MANAGER".
                - "createTime" (str): Timestamp when the membership was created.
                - "member" (Dict[str, Union[str, bool]]): User details with keys:
                    - "name" (str): Resource name of the user in format `users/{user}`.
                    - "displayName" (str): Display name of the user.
                    - "domainId" (str): Workspace domain ID.
                    - "type" (str): Type of member, one of: "TYPE_UNSPECIFIED", "HUMAN", "BOT".
                    - "isAnonymous" (bool): True if the user is deleted or profile is hidden.
                - "groupMember" (Optional[Dict[str, str]]): Present if membership is for a Google Group:
                    - "name" (str): Resource name of the group in format `groups/{group}`.
            - "nextPageToken" (Optional[str]): A token to retrieve the next page of results. 
                                              Absent if there are no more results.
        If no memberships are found (after filtering), returns {"memberships": []}.

    Raises:
        TypeError: If any argument is of an incorrect type.
        InvalidParentFormatError: If 'parent' is not in the format 'spaces/{{space}}'.
        InvalidPageSizeError: If 'pageSize' is provided and is not between 1 and 1000 (inclusive).
        AdminAccessFilterError: If 'useAdminAccess' is True, 'filter' is provided, but the filter
                                does not include a valid condition on 'member.type'.
    """
    # --- Helper functions moved to utils.py ---
    from .utils import parse_filter, apply_filter
    
    # --- Standard Input Validation ---
    if not isinstance(parent, str):
        raise TypeError("Argument 'parent' must be a string.")
    if not parent: # Check for empty string
        raise InvalidParentFormatError("Argument 'parent' cannot be empty.")
    if not parent.startswith("spaces/"):
        raise InvalidParentFormatError(f"Invalid parent format: '{parent}'. Expected 'spaces/{{space}}'.")
    # Ensure there's something after "spaces/"
    if len(parent.split("spaces/", 1)) < 2 or not parent.split("spaces/", 1)[1]:
        raise InvalidParentFormatError(f"Invalid parent format: '{parent}'. Space ID is missing after 'spaces/'.")


    if pageSize is not None:
        if not isinstance(pageSize, int):
            raise TypeError("Argument 'pageSize' must be an integer if provided.")
        if not (1 <= pageSize <= 1000):
            raise InvalidPageSizeError("Argument 'pageSize' must be between 1 and 1000, inclusive, if provided.")

    if pageToken is not None and not isinstance(pageToken, str):
        raise TypeError("Argument 'pageToken' must be a string if provided.")

    if filter is not None and not isinstance(filter, str):
        raise TypeError("Argument 'filter' must be a string if provided.")

    if showGroups is not None and not isinstance(showGroups, bool):
        raise TypeError("Argument 'showGroups' must be a boolean if provided.")

    if showInvited is not None and not isinstance(showInvited, bool):
        raise TypeError("Argument 'showInvited' must be a boolean if provided.")

    if useAdminAccess is not None and not isinstance(useAdminAccess, bool):
        raise TypeError("Argument 'useAdminAccess' must be a boolean if provided.")

    def default_page_size(ps: Optional[int]) -> int:
        """
        Returns the default page size for pagination when pageSize is not provided.

        This helper function provides a default page size of 100 when no page size
        is specified, or returns the provided page size when it is specified and
        has been validated upstream.

        Args:
            ps (Optional[int]): The page size parameter that has been pre-validated
                upstream. Expected to be None or an integer between 1 and 1000 inclusive.
                - None: Indicates no page size was provided by the user
                - 1-1000: A valid page size that has already been validated

        Returns:
            int: The page size to use for pagination.
                - Returns 100 (default) when ps is None
                - Returns ps when ps is a valid integer (1-1000)

        Raises:
            None: This function does not raise exceptions. It assumes the input
                has been pre-validated by upstream validation logic.
        """
        if ps is None:
            return 100
        # Given prior validation, ps is already 1 <= ps <= 1000 or None.
        # This helper's original logic for ps < 0 is now redundant due to validation.
        # return min(ps, 1000) # Simplified: ps is already <= 1000 if not None
        return ps # If pageSize was provided and validated, use it. If None, it's 100.

    def apply_filter(membership: dict, expressions: List[tuple]) -> bool:
        """
        Applies filter expressions to a membership object and returns whether it matches.

        This helper function evaluates a list of filter expressions against a membership
        dictionary to determine if the membership satisfies all the filtering criteria.
        Only specific fields and operators are supported for security and performance.

        Args:
            membership (dict): The membership dictionary to filter. Expected to contain:
                - "role" (str, optional): Membership role (e.g., "ROLE_MEMBER", "ROLE_MANAGER")
                - "member" (dict, optional): Member details with keys:
                    - "type" (str, optional): Member type (e.g., "HUMAN", "BOT")
            expressions (list): List of filter expressions as tuples (field, operator, value).
                Each tuple should contain:
                - field (str): Field name ("role" or "member.type")
                - operator (str): Comparison operator ("=" or "!=")
                - value (str): Value to compare against

        Returns:
            bool: True if the membership matches all filter expressions, False otherwise.
                Returns True for empty expressions list (no filtering applied).

        Raises:
            TypeError: If membership is not a dictionary or expressions is not a list.
            ValueError: If expressions contains invalid tuple structures.
        """
        # Input validation
        if not isinstance(membership, dict):
            raise TypeError("Argument 'membership' must be a dictionary.")
        
        if not isinstance(expressions, builtins.list):
            raise TypeError("Argument 'expressions' must be a list.")

        for i, expr in enumerate(expressions):
            # Validate each expression is a tuple/list with exactly 3 elements
            if not isinstance(expr, (tuple, builtins.list)) or len(expr) != 3:
                raise ValueError(f"Expression at index {i} must be a tuple/list with exactly 3 elements (field, operator, value).")
            
            field, op, value = expr
            
            # Validate field and operator are strings
            if not isinstance(field, str):
                raise ValueError(f"Field at expression index {i} must be a string, got {type(field).__name__}.")
            if not isinstance(op, str):
                raise ValueError(f"Operator at expression index {i} must be a string, got {type(op).__name__}.")

            # Skip expressions with empty fields (treat as invalid)
            if not field:
                continue

            # Apply filter based on field
            if field == "role":
                field_val = membership.get("role", "")
            elif field == "member.type":
                member_dict = membership.get("member", {})
                if not isinstance(member_dict, dict):
                    field_val = ""  # Gracefully handle invalid member structure
                else:
                    field_val = member_dict.get("type", "")
            else:
                continue # Skip unknown fields

            # Apply comparison based on operator
            if op == "=":
                if field_val != value:
                    return False
            elif op == "!=":
                if field_val == value:
                    return False
            # else: skip unknown operators
        return True

    # --- End of helper functions ---


    # --- Business Logic Input Validation (using helpers) ---
    if useAdminAccess:
        if not filter:
            raise AdminAccessFilterError(
                'When using admin access, the filter must be specified and include a condition '
                'like \'member.type = "HUMAN"\' or \'member.type != "BOT"\'.'
            )

        exprs = parse_filter(filter)
        all_expressions = [expr for group in exprs for expr in group]

        # Check for disallowed member.type clauses
        for field, op, value in all_expressions:
            if field == "member.type" and value == "BOT" and op == "=":
                raise AdminAccessFilterError(
                    'Admin access is not allowed for filters with \'member.type = "BOT"\'. '
                )

        # Check for presence of at least one allowed clause
        type_expr_ok = any(
            (
                field.lower() == "member.type"
                and (
                    (op == "=" and value.upper() == "HUMAN")
                    or (op == "!=" and value.upper() == "BOT")
                )
            )
            for field, op, value in all_expressions
        )
        if not type_expr_ok:
            raise AdminAccessFilterError(
                'When using admin access with a filter, the filter must include a condition '
                'like \'member.type = "HUMAN"\' or \'member.type != "BOT"\'.'
            )

    # --- Core Logic (adapted from original, validation print/returns removed) ---
    print_log(
        f"Members.list called with parent={parent}, pageSize={pageSize}, pageToken={pageToken}, filter={filter}, showGroups={showGroups}, showInvited={showInvited}, useAdminAccess={useAdminAccess}"
    )

    # 1) Parent format already validated.

    # 2) Start with memberships whose resource name begins with f"{parent}/members/"
    all_memberships = []
    for mem in DB.get("Membership", []): # Use .get for safety
        if mem.get("name", "").startswith(f"{parent}/members/"):
            all_memberships.append(mem)

    if useAdminAccess:
        all_memberships = [
            m for m in all_memberships if not m.get("name", "").endswith("/members/app")
        ]

    if filter: # filter is already known to be a string here if not None
        exprs = parse_filter(filter)
        # Convert DNF structure to flat list for our local apply_filter
        flat_exprs = [expr for group in exprs for expr in group]
        all_memberships = [m for m in all_memberships if apply_filter(m, flat_exprs)]

    if showGroups is not None and not showGroups:
        all_memberships = [
            m
            for m in all_memberships
            if not m.get("member", {}).get("name", "").startswith("groups/")
        ]
    if showInvited is not None and not showInvited:
        all_memberships = [
            m for m in all_memberships if m.get("state", "").upper() != "INVITED"
        ]
    
    # 6) Set pageSize and pageToken.
    effective_page_size = pageSize if pageSize is not None else 100
    
    offset = 0
    if pageToken:
        try:
            offset = max(int(pageToken), 0)
        except (ValueError, TypeError):
            offset = 0
    
    # 7) Apply pagination.
    total = len(all_memberships)
    end = offset + effective_page_size
    page_items = all_memberships[offset:end]
    nextPageToken_val = str(end) if end < total else None
    
    response = {"memberships": page_items}
    if nextPageToken_val:
        response["nextPageToken"] = nextPageToken_val

    print_log(f"ListMembershipsResponse: {response}")
    return response


@tool_spec(
    spec={
        'name': 'get_space_member',
        'description': 'Retrieves details about a specific membership in a Chat space.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': """ Required. The resource name of the membership to retrieve.
                    Format:
                    - spaces/{space}/members/{member}
                    - spaces/{space}/members/app (for the app itself)
                    You can use an email address as an alias for {member}, e.g., spaces/{space}/members/user@example.com. """
                },
                'useAdminAccess': {
                    'type': 'boolean',
                    'description': """ If True, runs with the caller's Workspace admin privileges.
                    Note: App memberships (i.e., .../members/app) cannot be fetched with admin access.
                    Defaults to None. """
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def get(name: str, useAdminAccess: Optional[bool] = None) -> Dict[str, Union[str, dict]]:
    """
    Retrieves details about a specific membership in a Chat space.
    
    Args:
        name (str): Required. The resource name of the membership to retrieve.
            Format:
            - spaces/{space}/members/{member}
            - spaces/{space}/members/app (for the app itself)
            You can use an email address as an alias for {member}, e.g., spaces/{space}/members/user@example.com.
        useAdminAccess (Optional[bool]): If True, runs with the caller's Workspace admin privileges.
            Note: App memberships (i.e., .../members/app) cannot be fetched with admin access.
            Defaults to None.
    
    Returns:
        Dict[str, Union[str, dict]]: A dictionary representing the membership with the following keys:
            - 'name' (str): Resource name of the membership.
            - 'state' (str): One of:
                - 'MEMBERSHIP_STATE_UNSPECIFIED'
                - 'JOINED'
                - 'INVITED'
                - 'NOT_A_MEMBER'
            - 'role' (str): One of:
                - 'MEMBERSHIP_ROLE_UNSPECIFIED'
                - 'ROLE_MEMBER'
                - 'ROLE_MANAGER'
            - 'createTime' (str): (Optional) Timestamp when the membership was created.
            - 'deleteTime' (str): (Optional) Timestamp when the membership was deleted.
            - 'member' (Dict[str, Union[str, bool]]): User details:
                - 'name' (str): Format: users/{user}
                - 'displayName' (str): Display name of the user.
                - 'domainId' (str): Workspace domain ID.
                - 'type' (str): One of:
                    - 'TYPE_UNSPECIFIED'
                    - 'HUMAN'
                    - 'BOT'
                - 'isAnonymous' (bool): True if the user is deleted or profile is hidden.
            - 'groupMember' (Dict[str, str], optional): Google Group details:
                - 'name' (str): Format: groups/{group}
        Returns an empty dictionary if the membership is not found or not accessible.

    Raises:
        TypeError: If 'name' is not a string or 'useAdminAccess' is not a boolean (when not None).
        ValueError: If 'name' is empty or None.
        InvalidMemberNameFormatError: If 'name' does not follow the required format.
    """
    # Input validation for name parameter
    if not isinstance(name, str):
        raise TypeError("Argument 'name' must be a string.")
    
    if not name or not name.strip():
        raise ValueError("Argument 'name' cannot be empty or None.")
    
    name = name.strip()
    
    # Validate name format: spaces/{space}/members/{member}
    # Support both regular member names and special "app" member
    # Allow paths like spaces/space_id/members/users/user_id or spaces/space_id/members/app
    import re
    member_name_pattern = r'^spaces/[^/]+/members/[^/]+(/[^/]+)*$'
    
    if not re.match(member_name_pattern, name):
        raise InvalidMemberNameFormatError(
            f"Invalid member name format: '{name}'. "
            "Expected format: 'spaces/{{space}}/members/{{member}}' or 'spaces/{{space}}/members/app'."
        )
    
    # Input validation for useAdminAccess parameter
    if useAdminAccess is not None and not isinstance(useAdminAccess, bool):
        raise TypeError("Argument 'useAdminAccess' must be a boolean if provided.")

    print_log(f"Members.get called with name={name}, useAdminAccess={useAdminAccess}")

    # 1) Locate the membership in DB
    found = None
    for mem in DB["Membership"]:
        if mem.get("name") == name:
            found = mem
            break

    # 2) If not found, return {}
    if not found:
        print_log("Membership not found => {}")
        return {}

    # Check if membership is "app" and useAdminAccess == True
    # The doc says: "Getting app memberships in a space isn't supported when using admin access."
    # So we skip returning details in that scenario
    if useAdminAccess:
        # If the membership name ends with "/members/app", it's the app membership
        if name.endswith("/members/app"):
            print_log("Admin access used for app membership => not supported => {}")
            return {}

    print_log(f"Found membership => {found}")
    return found


@tool_spec(
    spec={
        'name': 'add_space_member',
        'description': 'Creates a membership for a user or group in the specified Chat space.',
        'parameters': {
            'type': 'object',
            'properties': {
                'parent': {
                    'type': 'string',
                    'description': """ The resource name of the space.
                    Format: spaces/{space} """
                },
                'membership': {
                    'type': 'object',
                    'description': "Represents the membership to be created, with the following fields:\nAll fields are optional - provide only the fields you need:\nNote: You must provide either 'member' (for user membership) OR 'groupMember' (for group membership), but not both.",
                    'properties': {
                        'role': {
                            'type': 'string',
                            'description': "Defaults to 'ROLE_MEMBER'. One of:`'MEMBERSHIP_ROLE_UNSPECIFIED', 'ROLE_MEMBER', 'ROLE_MANAGER'"
                        },
                        'state': {
                            'type': 'string',
                            'description': "Defaults to 'INVITED'. One of:`'MEMBERSHIP_STATE_UNSPECIFIED', 'JOINED', 'INVITED', 'NOT_A_MEMBER'"
                        },
                        'deleteTime': {
                            'type': 'string',
                            'description': 'Timestamp of deletion.'
                        },
                        'member': {
                            'type': 'object',
                            'description': 'Member information for user memberships. Provide this OR groupMember, not both:',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Format: users/{user} or users/app'
                                },
                                'displayName': {
                                    'type': 'string',
                                    'description': "The user's display name."
                                },
                                'domainId': {
                                    'type': 'string',
                                    'description': 'Workspace domain ID.'
                                },
                                'type': {
                                    'type': 'string',
                                    'description': "One of:'TYPE_UNSPECIFIED', 'HUMAN', 'BOT'. Defaults to 'TYPE_UNSPECIFIED'."
                                },
                                'isAnonymous': {
                                    'type': 'boolean',
                                    'description': 'True if the user is deleted or profile is hidden.'
                                }
                            },
                            'required': [
                                'name'
                            ]
                        },
                        'groupMember': {
                            'type': 'object',
                            'description': 'Group information for group memberships. Provide this OR member, not both:',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Format: groups/{group}'
                                }
                            },
                            'required': [
                                'name'
                            ]
                        }
                    },
                    'required': []
                },
                'useAdminAccess': {
                    'type': 'boolean',
                    'description': "If True, uses administrator privileges. \nAdmin access cannot be used to create memberships for bots or users outside the domain."
                }
            },
            'required': [
                'parent',
                'membership'
            ]
        }
    }
)

def create(
    parent: str,
    membership: Dict[str, Union[str, Dict[str, Union[str, bool]]]],
    useAdminAccess: Optional[bool] = None
) -> Dict[str, Union[str, Dict[str, Union[str, bool]]]]:
    """
    
    Creates a membership for a user or group in the specified Chat space.

    Args:
        parent (str): The resource name of the space.
            Format: spaces/{space}
        membership (Dict[str, Union[str, Dict[str, Union[str, bool]]]]): Represents the membership to be created, with the following fields:
            All fields are optional - provide only the fields you need:
            Note: You must provide either 'member' (for user membership) OR 'groupMember' (for group membership), but not both.
            - role (Optional[str]): Defaults to 'ROLE_MEMBER'. One of:`'MEMBERSHIP_ROLE_UNSPECIFIED', 'ROLE_MEMBER', 'ROLE_MANAGER'
            - state (Optional[str]): Defaults to 'INVITED'. One of:`'MEMBERSHIP_STATE_UNSPECIFIED', 'JOINED', 'INVITED', 'NOT_A_MEMBER'
            - deleteTime (Optional[str]): Timestamp of deletion.
            - member (Optional[Dict[str, Union[str, bool]]]): Member information for user memberships. Provide this OR groupMember, not both:
                - name (str): Format: users/{user} or users/app
                - displayName (Optional[str]): The user's display name.
                - domainId (Optional[str]): Workspace domain ID.
                - type (Optional[str]): One of:'TYPE_UNSPECIFIED', 'HUMAN', 'BOT'. Defaults to 'TYPE_UNSPECIFIED'.
                - isAnonymous (Optional[bool]): True if the user is deleted or profile is hidden.
            - groupMember (Optional[Dict[str, str]]): Group information for group memberships. Provide this OR member, not both:
                - name (str): Format: groups/{group}
            Note: You must provide either 'member' (for user membership) OR 'groupMember' (for group membership), but not both.
        useAdminAccess (Optional[bool]): If True, uses administrator privileges. 
            Admin access cannot be used to create memberships for bots or users outside the domain.

    Returns:
        Dict[str, Union[str, Dict[str, Union[str, bool]]]]: The created membership object with the following structure:
            - name (str): Auto-generated resource name for the membership (format: spaces/{space}/members/{member}).
            - state (str): Membership state. Defaults to 'INVITED' if not provided. One of:
                'MEMBERSHIP_STATE_UNSPECIFIED', 'JOINED', 'INVITED', 'NOT_A_MEMBER'.
            - role (str): Membership role. Defaults to 'ROLE_MEMBER' if not provided. One of:
                'MEMBERSHIP_ROLE_UNSPECIFIED', 'ROLE_MEMBER', 'ROLE_MANAGER'.
            - member (Dict[str, Union[str, bool]]): Member information for user memberships, containing:
                - name (str): Format: users/{user} or users/app (required).
                - displayName (Optional[str]): The user's display name.
                - domainId (Optional[str]): Workspace domain ID.
                - type (str): One of: 'TYPE_UNSPECIFIED', 'HUMAN', 'BOT' (required). Defaults to 'TYPE_UNSPECIFIED'.
                - isAnonymous (Optional[bool]): True if the user is deleted or profile is hidden.
            - groupMember (Optional[Dict[str, str]]): Group information for group memberships, containing:
                - name (str): Format: groups/{group} (required).
            - createTime (str): Timestamp when the membership was created (auto-generated).
            - deleteTime (Optional[str]): Timestamp of deletion, if applicable.

    Raises:
        TypeError: If 'parent' is not a string, 'membership' is not a dictionary,
                   or 'useAdminAccess' is not a boolean (if provided).
        InvalidParentFormatError: If 'parent' format is invalid.
        PydanticValidationError: If 'membership' dictionary does not conform to the expected structure
                                 or contains invalid values for its fields.
        AdminAccessNotAllowedError: If 'useAdminAccess' is True and an attempt is made to create
                                    a membership for a BOT.
        MembershipAlreadyExistsError: If the membership to be created already exists.
    """
    # --- Input Validation ---
    if not isinstance(parent, str):
        raise TypeError("Parent must be a string.")
    if not isinstance(membership, dict):
        raise TypeError("Membership must be a dictionary.")
    if useAdminAccess is not None and not isinstance(useAdminAccess, bool):
        raise TypeError("useAdminAccess must be a boolean or None.")

    parts = parent.split("/")
    if len(parts) != 2 or parts[0] != "spaces":
        raise InvalidParentFormatError("Invalid parent format. Expected 'spaces/{space}'.")

    try:
        validated_membership_model = MembershipInputModel(**membership)
    except PydanticValidationError as e:
        raise e

    # Convert Pydantic model to dict to work with it similar to the original function
    # This also applies defaults specified in the Pydantic model
    # Use mode='json' to serialize enums to strings for proper API response format
    membership_data = validated_membership_model.model_dump(exclude_none=True, mode='json')

    # Validate that either member or groupMember is provided, but not both
    has_member = validated_membership_model.member is not None
    # Business logic validation using validated data
    if useAdminAccess is True and has_member:
        if validated_membership_model.member.type == MemberTypeEnum.BOT:
            raise AdminAccessNotAllowedError(
                "Admin access cannot be used to create memberships for a Chat app (BOT)."
            )

    # --- Core Logic (preserved from original, adapted for validated data) ---
    # Auto-generate membership name
    # Extract member ID from full member name (users/USER123 -> USER123)
    if validated_membership_model.member:
        mem_name = validated_membership_model.member.name
        # Extract just the ID part from users/USER123 or users/app
        if mem_name.startswith("users/"):
            member_id = mem_name.split("/", 1)[1]  # Get everything after "users/"
        else:
            member_id = mem_name
        membership_name = f"{parent}/members/{member_id}"
    elif validated_membership_model.groupMember:
        group_name = validated_membership_model.groupMember.name
        # Extract just the ID part from groups/GROUP123
        if group_name.startswith("groups/"):
            group_id = group_name.split("/", 1)[1]  # Get everything after "groups/"
        else:
            group_id = group_name
        membership_name = f"{parent}/members/{group_id}"
    
    membership_data["name"] = membership_name

    # Check for existing membership
    # Assume DB is accessible globally or passed appropriately in a real application
    global DB  # Using global DB as per original code's context
    for m in DB["Membership"]:
        if m.get("name") == membership_name:
            raise MembershipAlreadyExistsError(f"Membership '{membership_name}' already exists.")

    # Set auto-filled fields (role and state defaults are handled by Pydantic model)
    membership_data.setdefault("createTime", datetime.now().isoformat() + "Z")
    
    # If 'role' or 'state' were not in the input 'membership' dict,
    # Pydantic defaults ensure they are in 'membership_data'.
    # If they were in input, Pydantic validated them.

    DB["Membership"].append(membership_data)
    # print(f"Membership created => {membership_data}") # Original had a print
    return membership_data


@tool_spec(
    spec={
        'name': 'update_space_member',
        'description': 'Updates a membership.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'Resource name of the membership to update. Format: spaces/{space}/members/{member}'
                },
                'updateMask': {
                    'type': 'string',
                    'description': "Comma-separated list of fields to update. Supported values: 'role'"
                },
                'membership': {
                    'type': 'object',
                    'description': 'Dictionary containing the updated membership fields. Supported structure:',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'Resource name of the membership. Format: spaces/{space}/members/{member}'
                        },
                        'role': {
                            'type': 'string',
                            'description': 'One of "MEMBERSHIP_ROLE_UNSPECIFIED", "ROLE_MEMBER", "ROLE_MANAGER".'
                        },
                        'state': {
                            'type': 'string',
                            'description': 'One of "MEMBERSHIP_STATE_UNSPECIFIED", "JOINED", "INVITED", "NOT_A_MEMBER".'
                        },
                        'createTime': {
                            'type': 'string',
                            'description': 'Timestamp when the membership was created.'
                        },
                        'deleteTime': {
                            'type': 'string',
                            'description': 'Timestamp when the membership was deleted.'
                        },
                        'member': {
                            'type': 'object',
                            'description': 'Member details with the following structure:',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Format: users/{user}'
                                },
                                'displayName': {
                                    'type': 'string',
                                    'description': 'Display name of the user.'
                                },
                                'domainId': {
                                    'type': 'string',
                                    'description': 'Workspace domain ID.'
                                },
                                'type': {
                                    'type': 'string',
                                    'description': 'One of "TYPE_UNSPECIFIED", "HUMAN", "BOT".'
                                },
                                'isAnonymous': {
                                    'type': 'boolean',
                                    'description': 'True if user is deleted or hidden.'
                                }
                            },
                            'required': [
                                'name',
                                'type'
                            ]
                        },
                        'groupMember': {
                            'type': 'object',
                            'description': 'group information with the following structure:',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Format: groups/{group}'
                                }
                            },
                            'required': [
                                'name'
                            ]
                        }
                    },
                    'required': [
                        'name'
                    ]
                },
                'useAdminAccess': {
                    'type': 'boolean',
                    'description': 'If True, runs the method using administrator privileges.'
                }
            },
            'required': [
                'name',
                'updateMask',
                'membership'
            ]
        }
    }
)

def patch(
    name: str, updateMask: str, membership: Dict[str, Union[str, Dict[str, Union[str, bool]]]], useAdminAccess: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Updates a membership.

    Args:
        name (str): Resource name of the membership to update. Format: spaces/{space}/members/{member}
        updateMask (str): Comma-separated list of fields to update. Supported values: 'role'
        membership (Dict[str, Union[str, Dict[str, Union[str, bool]]]]): Dictionary containing the updated membership fields. Supported structure:
            - name (str): Resource name of the membership. Format: spaces/{space}/members/{member}
            - role (Optional[str]): One of "MEMBERSHIP_ROLE_UNSPECIFIED", "ROLE_MEMBER", "ROLE_MANAGER".
            - state (Optional[str]): One of "MEMBERSHIP_STATE_UNSPECIFIED", "JOINED", "INVITED", "NOT_A_MEMBER".
            - createTime (Optional[str]): Timestamp when the membership was created.
            - deleteTime (Optional[str]): Timestamp when the membership was deleted.
            - member (Optional[Dict[str, Any]]): Member details with the following structure:
                - name (str): Format: users/{user}
                - displayName (Optional[str]): Display name of the user.
                - domainId (Optional[str]): Workspace domain ID.
                - type (str): One of "TYPE_UNSPECIFIED", "HUMAN", "BOT".
                - isAnonymous (Optional[bool]): True if user is deleted or hidden.
            - groupMember (Optional[Dict[str, Any]]): group information with the following structure:
                - name (str): Format: groups/{group}
        useAdminAccess (Optional[bool]): If True, runs the method using administrator privileges.

    Returns:
        Dict[str, Any]: The updated membership resource with the following structure:
            - name (str): Resource name of the membership.
                Format: spaces/{space}/members/{member}
            - role (str): The membership role. One of:
                - 'MEMBERSHIP_ROLE_UNSPECIFIED'
                - 'ROLE_MEMBER'
                - 'ROLE_MANAGER'
            - state (str): Membership state. One of:
                - 'MEMBERSHIP_STATE_UNSPECIFIED'
                - 'JOINED'
                - 'INVITED'
                - 'NOT_A_MEMBER'
            - createTime (str): Timestamp when the membership was created.
            - deleteTime (str): Optional. Timestamp when the membership was deleted.
            - member (Dict[str, Any]): User details:
                - name (str): Resource name of the user. Format: users/{user}
                - displayName (str): Display name of the user.
                - domainId (str): Workspace domain ID.
                - type (str): Type of member. One of:
                    - 'TYPE_UNSPECIFIED'
                    - 'HUMAN'
                    - 'BOT'
                - isAnonymous (bool): True if the user is deleted or profile is hidden.
            - groupMember (Dict[str, Any]): Optional. Group details:
                - name (str): Resource name of the group. Format: groups/{group}

    Raises:
        TypeError: If any argument is of an incorrect type.
        ValueError: If 'name' is empty or None.
        InvalidMemberNameFormatError: If 'name' does not follow the required format
            'spaces/{space}/members/{member}'.
        InvalidUpdateMaskError: If 'updateMask' is invalid or contains unsupported fields.
        NoUpdatableFieldsError: If the 'membership' dictionary is invalid or contains no updatable fields.
        MembershipNotFoundError: If the specified membership does not exist.
        AdminAccessNotAllowedError: If admin access is used to modify app memberships,
            which is not permitted.
    """
    print_log(f"Members.patch called with name={name}, updateMask={updateMask}, membership={membership}, useAdminAccess={useAdminAccess}")
    
    # Input validation for name parameter
    if not isinstance(name, str):
        raise TypeError("Argument 'name' must be a string.")
    
    if not name or not name.strip():
        raise ValueError("Argument 'name' cannot be empty or None.")
    
    name = name.strip()
    
    # Validate name format: spaces/{space}/members/{member}
    # Support both regular member names and special "app" member
    # Allow paths like spaces/space_id/members/users/user_id or spaces/space_id/members/app
    import re
    member_name_pattern = r'^spaces/[^/]+/members/[^/]+(/[^/]+)*$'
    
    if not re.match(member_name_pattern, name):
        raise InvalidMemberNameFormatError(
            f"Invalid member name format: '{name}'. "
            "Expected format: 'spaces/{{space}}/members/{{member}}' or 'spaces/{{space}}/members/app'."
        )
    
    # Input validation for updateMask parameter
    if not isinstance(updateMask, str):
        raise TypeError("Argument 'updateMask' must be a string.")
    
    # Input validation for membership parameter
    if not isinstance(membership, dict):
        raise TypeError("Argument 'membership' must be a dictionary.")
    
    # Input validation for useAdminAccess parameter
    if useAdminAccess is not None and not isinstance(useAdminAccess, bool):
        raise TypeError("Argument 'useAdminAccess' must be a boolean if provided.")
    
    # Validate updateMask with a Pydantic model
    try:
        validated_update_mask = MembershipUpdateMaskModel(updateMask=updateMask)
    except PydanticValidationError as e:
        print_log(f"Invalid updateMask: {e}")
        raise InvalidUpdateMaskError(str(e))
    
    # Validate membership with a Pydantic model
    try:
        validated_membership = MembershipPatchModel(**membership)
    except PydanticValidationError as e:
        print_log(f"Invalid membership: {e}")
        raise NoUpdatableFieldsError(str(e))
    
    # Locate the membership in DB
    found = None
    for mem in DB["Membership"]:
        if mem.get("name") == name:
            found = mem
            break

    # If not found, raise error
    if not found:
        print_log("Membership not found.")
        raise MembershipNotFoundError(f"Membership '{name}' not found")
    
    # Check if membership is "app" and useAdminAccess == True
    # App memberships cannot be modified with admin access
    if useAdminAccess and name.endswith("/members/app"):
        print_log("Admin access used for app membership => not supported => {}")
        raise AdminAccessNotAllowedError("Admin access cannot be used to modify app memberships")
    
    # Determine which fields to update based on the updateMask
    fields_to_update = [field.strip() for field in updateMask.split(',')]
    
    # Apply each field update
    updated = False
    membership_data = validated_membership.model_dump(exclude_none=True)
    
    for field in fields_to_update:
        if field == 'role' and 'role' in membership_data:
            found['role'] = membership_data['role']
            updated = True
            print_log(f"Updated {field} to {membership_data[field]}")
    
    # If no fields were updated, this is unexpected (validation should have caught this)
    if not updated:
        print_log("No fields were updated despite valid updateMask and membership")
        return {}
    
    # 6) Return the updated membership
    print_log(f"Updated membership => {found}")
    return found


@tool_spec(
    spec={
        'name': 'remove_space_member',
        'description': 'Deletes a membership from a space.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': """ Required. Resource name of the membership to delete.
                    Format: spaces/{space}/members/{member}
                    Example values:
                    - spaces/AAA/members/user@example.com
                    - spaces/AAA/members/app """
                },
                'useAdminAccess': {
                    'type': 'boolean',
                    'description': """ Optional. If True, uses Workspace admin privileges.
                    Note: Deleting app memberships using admin access is not supported. """
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def delete(name: str, useAdminAccess: Optional[bool] = None) -> Dict[str, Union[str, Dict[str, Union[str, bool]]]]:
    """
    Deletes a membership from a space. 

    Args:
        name (str): Required. Resource name of the membership to delete.
            Format: spaces/{space}/members/{member}
            Example values:
            - spaces/AAA/members/user@example.com
            - spaces/AAA/members/app
        useAdminAccess (Optional[bool]): If True, uses Workspace admin privileges. Defaults to None.
            Note: Deleting app memberships using admin access is not supported.

    Returns:
        Dict[str, Union[str, Dict[str, Union[str, bool]]]]: The deleted membership resource with the following fields:
            - name (str): Resource name of the membership.
                Format: spaces/{space}/members/{member}
            - state (str): One of:
                - 'MEMBERSHIP_STATE_UNSPECIFIED'
                - 'JOINED'
                - 'INVITED'
                - 'NOT_A_MEMBER'
            - role (str): One of:
                - 'MEMBERSHIP_ROLE_UNSPECIFIED'
                - 'ROLE_MEMBER'
                - 'ROLE_MANAGER'
            - createTime (str): Timestamp when the membership was created.
            - deleteTime (str): (Optional) Timestamp when the membership was deleted.
            - member (Dict[str, Any]): User details:
                - name (str): Format: users/{user}
                - displayName (str): Output only.
                - domainId (str): Output only.
                - type (str): One of:
                    - 'TYPE_UNSPECIFIED'
                    - 'HUMAN'
                    - 'BOT'
                - isAnonymous (bool): True if the user is deleted or profile is hidden.
            - groupMember (Dict[str, Any]): Optional. Group details:
                - name (str): Format: groups/{group}

        Returns an empty dictionary if the membership is not found or deletion is disallowed.

    Raises:
        TypeError: If any argument is of an incorrect type.
        InvalidParentFormatError: If 'name' is not in the expected format 'spaces/{space}/members/{member}'.
    """
    # --- Input Validation ---
    if not isinstance(name, str):
        raise TypeError("Argument 'name' must be a string.")
    
    if not name:  # Check for empty string
        raise InvalidParentFormatError("Argument 'name' cannot be empty.")
    
    if useAdminAccess is not None and not isinstance(useAdminAccess, bool):
        raise TypeError("Argument 'useAdminAccess' must be a boolean if provided.")

    # Validate name format: spaces/{space}/members/{member}
    if not name.startswith("spaces/"):
        raise InvalidParentFormatError(f"Invalid name format: '{name}'. Expected format: 'spaces/{{space}}/members/{{member}}'.")
    
    # Split and validate the structure
    parts = name.split("/")
    if len(parts) < 4 or parts[0] != "spaces" or parts[2] != "members":
        raise InvalidParentFormatError(f"Invalid name format: '{name}'. Expected format: 'spaces/{{space}}/members/{{member}}'.")
    
    # Ensure space ID and member ID are not empty
    if not parts[1] or not parts[3]:
        raise InvalidParentFormatError(f"Invalid name format: '{name}'. Space ID and member ID cannot be empty.")

    # 1) Find the membership in the database.
    target = None
    for m in DB["Membership"]:
        if m.get("name") == name:
            target = m
            break

    if not target:
        print_log("Membership not found.")
        return {}

    # 2) If useAdminAccess is true, then deleting an app membership is not supported.
    if useAdminAccess and name.endswith("/members/app"):
        print_log("Deleting app memberships using admin access is not supported.")
        return {}

    # 3) Remove the membership from DB
    DB["Membership"].remove(target)
    print_log(f"Deleted membership: {target}")
    return target

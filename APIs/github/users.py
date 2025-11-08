from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
from pydantic import ValidationError
from typing import Dict, Union, Optional, List, Any
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _get_raw_item_by_id
from .SimulationEngine.custom_errors import AuthenticationError, InvalidInputError
import re
import shlex
from common_utils.utils import validate_email_util
from common_utils.custom_errors import InvalidEmailError


@tool_spec(
    spec={
        'name': 'get_authenticated_user',
        'description': """ Get details of the authenticated user.
        
        Gets details of the authenticated user. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_me() -> Dict[str, Union[str, int, None]]:
    """Get details of the authenticated user.

    Gets details of the authenticated user.

    Returns:
        Dict[str, Union[str, int, None]]: A dictionary containing the authenticated user's details with the following keys:
            login (str): The user's username.
            id (int): The unique ID of the user.
            node_id (str): The global node ID of the user.
            name (Optional[str]): The user's full name.
            email (Optional[str]): The user's publicly visible email address.
            company (Optional[str]): The user's company.
            location (Optional[str]): The user's location.
            bio (Optional[str]): The user's biography.
            public_repos (int): The number of public repositories.
            public_gists (int): The number of public gists.
            followers (int): The number of followers.
            following (int): The number of users the user is following.
            created_at (str): ISO 8601 timestamp for when the account was created.
            updated_at (str): ISO 8601 timestamp for when the account was last updated.
            type (str): The type of account, e.g., 'User' or 'Organization'.

    Raises:
        AuthenticationError: If the request is not authenticated or if the authenticated user cannot be found.
    """
    authenticated_user_id = DB.get('CurrentUser').get('id')

    if authenticated_user_id is None:
        raise AuthenticationError("User is not authenticated.")
    
    user_data = _get_raw_item_by_id(DB, "Users", authenticated_user_id)

    if user_data is None:
        raise AuthenticationError(f"Authenticated user with ID {authenticated_user_id} not found.")
    
    return_data = {
        'login': user_data.get('login'),
        'id': user_data.get('id'),
        'node_id': user_data.get('node_id'),
        'name': user_data.get('name'),
        'email': user_data.get('email'),
        'company': user_data.get('company'),
        'location': user_data.get('location'),
        'bio': user_data.get('bio'),
        'public_repos': user_data.get('public_repos'),
        'public_gists': user_data.get('public_gists'),
        'followers': user_data.get('followers'),
        'following': user_data.get('following'),
        'created_at': user_data.get('created_at'),
        'updated_at': user_data.get('updated_at'),
        'type': user_data.get('type'),
    }
    return return_data


@tool_spec(
    spec={
        'name': 'search_users',
        'description': """ Search for GitHub users.
        
        Find users via various criteria. This method returns up to 100 results per page.
        The query can contain any combination of search keywords and qualifiers to narrow down the results.
        
        When no sort is specified, results are sorted by best match. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'q': {
                    'type': 'string',
                    'description': """ The search query string. Can contain any combination of search keywords and qualifiers.
                    For example: `q=tom+repos:>42+followers:>1000`.
                    Supported qualifiers:
                    - `in:login,name,email`: Restricts search to specified fields.
                    - `repos:n`: Filters by repository count. Can use `>`, `<`, `>=`, `<=`, and `..` ranges.
                    - `followers:n`: Filters by follower count. Can use `>`, `<`, `>=`, `<=`, and `..` ranges.
                    - `created:YYYY-MM-DD`: Filters by creation date. Can use `>`, `<`, `>=`, `<=`, and `..` ranges.
                    - `location:LOCATION`: Filters by location in the user's profile.
                    - `type:user|org`: Restricts search to users or organizations.
                    - `language:LANGUAGE`: Filters by the predominant language in the user's repositories. """
                },
                'sort': {
                    'type': 'string',
                    'description': """ The field to sort the search results by. Can be one of 'followers', 'repositories', 'joined'.
                    Defaults to None (best match). """
                },
                'order': {
                    'type': 'string',
                    'description': "The order of sorting ('asc' or 'desc'). Defaults to 'desc'."
                },
                'page': {
                    'type': 'integer',
                    'description': 'The page number for paginated results. Defaults to 1.'
                },
                'per_page': {
                    'type': 'integer',
                    'description': 'The number of results to return per page (max 100). Defaults to 30.'
                }
            },
            'required': [
                'q'
            ]
        }
    }
)
def search_users(q: str, sort: Optional[str] = None, order: Optional[str] = "desc", page: Optional[int] = 1, per_page: Optional[int] = 30) -> Dict[str, Any]:
    """Search for GitHub users.

    Find users via various criteria. This method returns up to 100 results per page.
    The query can contain any combination of search keywords and qualifiers to narrow down the results.

    When no sort is specified, results are sorted by best match.

    Args:
        q (str): The search query string. Can contain any combination of search keywords and qualifiers.
            For example: `q=tom+repos:>42+followers:>1000`.
            Supported qualifiers:
            - `in:login,name,email`: Restricts search to specified fields.
            - `repos:n`: Filters by repository count. Can use `>`, `<`, `>=`, `<=`, and `..` ranges.
            - `followers:n`: Filters by follower count. Can use `>`, `<`, `>=`, `<=`, and `..` ranges.
            - `created:YYYY-MM-DD`: Filters by creation date. Can use `>`, `<`, `>=`, `<=`, and `..` ranges.
            - `location:LOCATION`: Filters by location in the user's profile.
            - `type:user|org`: Restricts search to users or organizations.
            - `language:LANGUAGE`: Filters by the predominant language in the user's repositories.
        sort (Optional[str]): The field to sort the search results by. Can be one of 'followers', 'repositories', 'joined'.
            Defaults to None (best match).
        order (Optional[str]): The order of sorting ('asc' or 'desc'). Defaults to 'desc'.
        page (Optional[int]): The page number for paginated results. Defaults to 1.
        per_page (Optional[int]): The number of results to return per page (max 100). Defaults to 30.

    Returns:
        Dict[str, Any]: A dictionary containing user search results with the following keys:
            total_count (int): The total number of users found.
            incomplete_results (bool): Indicates if the search timed out before finding all results.
            items (List[Dict[str, Union[str, int, float]]]): A list of user objects matching the search criteria. Each user object in the list has the following fields:
                login (str): The user's username.
                id (int): The unique ID of the user.
                node_id (str): The global node ID of the user.
                type (str): The type of account, e.g., 'User' or 'Organization'.
                score (float): The search score associated with the user.

    Raises:
        InvalidInputError: If the search query 'q' is missing or invalid, or if pagination parameters are incorrect.
        RateLimitError: If the API rate limit is exceeded.
    """

    # --- Input Validation ---
    if not q or not q.strip():
        raise InvalidInputError("Search query 'q' cannot be empty.")

    if 'email:' in q:
        email = q.split('email:')[1].split(' ')[0]
        validate_email_util(email, "email")
    valid_sort_fields = ['followers', 'repositories', 'joined']
    if sort is not None and sort not in valid_sort_fields:
        raise InvalidInputError(
            f"Invalid 'sort' parameter. Must be one of {valid_sort_fields}."
        )

    valid_order_values = ['asc', 'desc']
    if order not in valid_order_values:
        raise InvalidInputError(
            f"Invalid 'order' parameter. Must be 'asc' or 'desc'."
        )

    if page is not None:
        if not isinstance(page, int) or page < 1:
            raise InvalidInputError(
                "Page number must be a positive integer."
            )
    
    if per_page is not None:
        if not isinstance(per_page, int) or per_page < 1:
            raise InvalidInputError(
                "Results per page must be a positive integer."
            )
        if per_page > 100:
            # This limit is common in APIs like GitHub's.
            raise InvalidInputError("Maximum 'per_page' is 100.")

    # --- Data Fetching and Filtering ---
    all_users_from_db = DB.get('Users', [])

    # This regex is improved to handle simple values and quoted values
    qualifier_pattern = re.compile(r'(\w+):("([^"]*)"|([^"\s]+))')
    
    qualifiers = {}
    search_terms_str = q

    # Before processing, check for mismatched quotes
    if search_terms_str.count('"') % 2 != 0:
        raise InvalidInputError("Invalid query syntax: Mismatched quotes.")

    for match in qualifier_pattern.finditer(q):
        key = match.group(1).lower()
        # group(3) is for quoted values, group(4) for unquoted
        value = match.group(3) if match.group(3) is not None else match.group(4)
        qualifiers[key] = value
        # Remove the qualifier from the string to isolate search terms
        search_terms_str = search_terms_str.replace(match.group(0), '', 1)

    # The remaining parts of the query are the search terms
    search_terms = [term.lower() for term in search_terms_str.split() if term]

    # Filter users based on qualifiers and search terms
    matched_users = []
    search_warnings = []  # Collect warnings to return to agent
    for user_data in all_users_from_db:
        # Check qualifiers
        qualifiers_match = True
        for key, value in qualifiers.items():
            field_map = {
                'repos': 'public_repos',
                'followers': 'followers',
                'location': 'location',
                'type': 'type',
                'language': 'language', # Assumes a 'language' field from a repo aggregation
                'created': 'created_at',
            }
            
            # The 'in' qualifier is handled with search terms, not here.
            if key == 'in' or key not in field_map:
                continue

            field_name = field_map[key]
            user_value = user_data.get(field_name)

            # --- Type and Location Check (Exact Match) ---
            if key in ['type', 'location']:
                # Strip quotes for location search
                if not user_value or value.lower() not in user_value.lower():
                    qualifiers_match = False
                    break
                continue
            
            # --- Date Check ---
            if key == 'created' and user_value:
                # Naive implementation: assuming YYYY-MM-DD format and string comparison
                # A more robust solution would parse dates properly.
                if value.startswith('<='):
                    if not user_value <= value[2:]: qualifiers_match = False
                elif value.startswith('>='):
                    if not user_value >= value[2:]: qualifiers_match = False
                elif value.startswith('<'):
                    if not user_value < value[1:]: qualifiers_match = False
                elif value.startswith('>'):
                    if not user_value > value[1:]: qualifiers_match = False
                elif '..' in value:
                    low, high = value.split('..')
                    if not (low <= user_value <= high): qualifiers_match = False
                else: # exact date match
                    if not user_value.startswith(value): qualifiers_match = False
                if not qualifiers_match: break
                continue

            # --- Numeric Check (repos, followers) ---
            if key in ['repos', 'followers']:
                numeric_user_value = user_data.get(field_map[key], 0)
                
                # Range check (e.g., 10..50)
                try:
                    if '..' in value:
                        low_str, high_str = value.split('..')
                        low = int(low_str) if low_str != '*' else float('-inf')
                        high = int(high_str) if high_str != '*' else float('inf')
                        if not (low <= numeric_user_value <= high):
                            qualifiers_match = False
                    else:
                        # Inequality check (e.g., >10, <=50)
                        op_match = re.match(r'([<>]?=?)(.*)', value)
                        if op_match:
                            op, num_str = op_match.groups()
                            num = int(num_str)
                            
                            if op == '>' and not numeric_user_value > num: qualifiers_match = False
                            elif op == '>=' and not numeric_user_value >= num: qualifiers_match = False
                            elif op == '<' and not numeric_user_value < num: qualifiers_match = False
                            elif op == '<=' and not numeric_user_value <= num: qualifiers_match = False
                            elif op == '' and not numeric_user_value == num: qualifiers_match = False
                except ValueError as e:
                    # Log warning about malformed numeric qualifier but continue by excluding this user
                    warning_msg = f"Failed to parse {key} qualifier '{value}' for user '{user_data.get('login', 'unknown')}', excluding from search results: {e}"
                    search_warnings.append(warning_msg)
                    print_log(f"Warning: {warning_msg}")
                    qualifiers_match = False
                    
                if not qualifiers_match:
                    break

        if not qualifiers_match:
            continue

        # This logic now ensures that *all* search terms must be present in the
        # login, name, or email for a user to be matched.
        search_fields = ['login', 'name', 'email', 'location'] # Default
        if 'in' in qualifiers:
            fields_to_search = qualifiers['in'].split(',')
            search_fields = [f for f in fields_to_search if f in ['login', 'name', 'email', 'location']]

        all_terms_found = True
        if search_terms:
            text_to_search = []
            for field in search_fields:
                field_value = user_data.get(field)
                if field_value:
                    text_to_search.append(str(field_value).lower())
            
            combined_text = " ".join(text_to_search)
            for term in search_terms:
                # Use substring matching for user search
                # This allows matching terms within usernames with underscores
                if term not in combined_text:
                    all_terms_found = False
                    break
        
        if all_terms_found:
            matched_users.append(user_data)
            
    total_count = len(matched_users)

    # --- Sorting ---
    if sort is None:
        # Default sort by "best match" (score)
        matched_users.sort(key=lambda u: u.get('score', 0), reverse=True)
    else:
        # Map API sort fields to internal DB field names.
        # Assumes these fields exist in the user_data dictionaries if sorting is requested.
        sort_key_map = {
            'followers': 'followers',
            'repositories': 'public_repos',
            'joined': 'created_at'  # Assumed to be an ISO 8601 date string for lexicographical sort.
        }
        sort_field_in_db = sort_key_map[sort]
        
        # Determine sort order: 'desc' by default if 'order' is not 'asc'.
        # This means if 'order' is None (default) or 'desc', sorting is descending.
        is_reverse_sort = (order != 'asc')
        
        # This sort operation assumes that if a sort field is specified,
        # all user_data dictionaries in matched_users contain that field with comparable values.
        # A KeyError will be raised if a field is missing, indicating data inconsistency.
        # A TypeError may occur if field values are not comparable (e.g. mixing None and str).
        # Handle potential None values in sort keys
        matched_users.sort(
            key=lambda u: u.get(sort_field_in_db, 0 if sort_field_in_db != 'created_at' else ''), 
            reverse=is_reverse_sort
        )


    # --- Pagination ---
    # Apply default pagination parameters if not provided, similar to GitHub API behavior.
    current_page = page if page is not None else 1
    # If per_page was None, it defaults to 30. If it was specified, it was already validated.
    items_per_page = per_page if per_page is not None else 30 

    start_index = (current_page - 1) * items_per_page
    end_index = start_index + items_per_page
    paginated_users_data = matched_users[start_index:end_index]

    # --- Formatting Output ---
    response_items = []
    for user_data in paginated_users_data:
        # Transform raw user data to the specified output item structure.
        # Assumes 'login', 'id', 'node_id', 'type' fields exist in user_data.
        # A KeyError will be raised if any of these essential fields are missing.
        item = {
            'login': user_data['login'],
            'id': user_data['id'],
            'node_id': user_data['node_id'],
            'type': user_data['type'],
            'score': user_data.get('score', 1.0)  # Assign a fixed search score as per typical search result structures.
        }
        response_items.append(item)


    # Construct the final response dictionary.
    result = {
        'total_count': total_count,
        'incomplete_results': False,  # No timeout simulation is implemented for this function.
        'items': response_items
    }
    
    # Include warnings if any occurred so the agent can understand issues
    if search_warnings:
        result['warnings'] = search_warnings
        result['skipped_users'] = len(search_warnings)
    
    return result

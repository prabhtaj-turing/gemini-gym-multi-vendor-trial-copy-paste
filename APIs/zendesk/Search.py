from common_utils.tool_spec_decorator import tool_spec
# zendesk/Search.py

from typing import Any, Dict, Optional
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _parse_search_query, _search_tickets, _search_users, _search_organizations, _search_groups, _sort_results, _get_side_loaded_data


@tool_spec(
    spec={
        'name': 'search',
        'description': """ Search for tickets, users, groups, and organizations using Zendesk's query syntax.
        
        This function implements the Zendesk Support API /api/v2/search endpoint which allows
        searching across tickets, users, groups, and organizations using property keywords and operators.
        
        Note: The special keyword "me" for assignee/requester
        fields returns tickets with assignee_id=1 or requester_id=1 respectively, as there is
        no authentication/session management system. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The search query string using Zendesk's query syntax.
                    Search Rules:
                    - Searches across tickets, users, and organizations by default
                    - Use "type:ticket", "type:user", or "type:organization" to limit scope
                    - Multiple terms are combined with AND logic
                    - Use "OR" keyword for multiple filters like "status:open OR pending type:ticket"
                    - Use quotes for exact phrase matching: "exact phrase"
                    - Use wildcards (*) for pattern matching like "email*"
                    - Use minus (-) for negation like "-status:closed"
                    - Combine filters and text like "priority:urgent server down"
                    
                    Supported Filter Fields:
                    
                    For Tickets:
                    - status: new, open, pending, hold, solved, closed
                    - priority: low, normal, high, urgent (supports >, <, >=, <= operators)
                    - ticket_type: problem, incident, question, task
                    - assignee: user_id, "me"(returns tickets with assignee_id=1), "none"
                    - requester: user_id
                    - organization: organization_id, "none"
                    - group: group_id, "none"
                    - tags: tag_name, "none"
                    - subject: text search in ticket subject
                    - description: text search in ticket description
                    - created: date or relative time (>2hours, >1day, >1week)
                    - updated: date or relative time
                    
                    For Users:
                    - role: end-user, agent, admin
                    - email: email pattern or domain (@example.com)
                    - name: text search in user name
                    - organization: organization_id, "none"
                    - tags: tag_name, "none"
                    - verified: true, false
                    - active: true, false
                    - created: date or relative time
                    - updated: date or relative time
                    
                    For Organizations:
                    - name: text search in organization name
                    - tags: tag_name, "none"
                    - created: date or relative time
                    - updated: date or relative time
                    
                    For Groups:
                    - name: text search in group name
                    - description: text search in group description
                    - created: date or relative time
                    - updated: date or relative time
                    
                    Relative Time Format:
                    - Supports: hours/h, minutes/min, days/d, weeks/w, months, years/y """
                },
                'sort_by': {
                    'type': 'string',
                    'description': 'Field to sort results by. Value can be created_at, updated_at, priority, status, ticket_type'
                },
                'sort_order': {
                    'type': 'string',
                    'description': 'Sort order. Value can be asc, desc. Defaults to desc.'
                },
                'page': {
                    'type': 'integer',
                    'description': 'Page number for pagination. Defaults to 1.'
                },
                'per_page': {
                    'type': 'integer',
                    'description': 'Number of results per page (1-100). Defaults to 100.'
                },
                'include': {
                    'type': 'string',
                    'description': 'Side-load related data. Comma-separated list like "users", or "users,organizations", "users,groups", "users,organizations,groups".'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def list_search_results(query: str, sort_by: Optional[str] = None, sort_order: Optional[str] = None, page: int = 1, per_page: int = 100, include: Optional[str] = None) -> Dict[str, Any]:
    """Search for tickets, users, groups and organizations using Zendesk's query syntax.

    This function implements the Zendesk Support API /api/v2/search endpoint which allows
    searching across tickets, users, groups, and organizations using property keywords and operators.
    
    Note: The special keyword "me" for assignee/requester
    fields returns tickets with assignee_id=1 or requester_id=1 respectively, as there is
    no authentication/session management system.

    Args:
        query (str): The search query string using Zendesk's query syntax.
            
            Search Rules:
            - Searches across tickets, users, groups, and organizations by default
            - Use "type:ticket", "type:user", "type:group", or "type:organization" to limit scope
            - Multiple terms are combined with AND logic
            - Use "OR" keyword for multiple filters like "status:open OR pending type:ticket"
            - Use quotes for exact phrase matching: "exact phrase"
            - Use wildcards (*) for pattern matching like "email*"
            - Use minus (-) for negation like "-status:closed"
            - Combine filters and text like "priority:urgent server down"
            
            Supported Filter Fields:
            
            For Tickets:
            - status: new, open, pending, hold, solved, closed
            - priority: low, normal, high, urgent (supports >, <, >=, <= operators)
            - ticket_type: problem, incident, question, task
            - assignee: user_id, "me"(returns tickets with assignee_id=1), "none"
            - requester: user_id
            - organization: organization_id, "none"
            - group: group_id, "none"
            - tags: tag_name, "none"
            - subject: text search in ticket subject
            - description: text search in ticket description
            - created: date or relative time (>2hours, >1day, >1week)
            - updated: date or relative time
            
            For Users:
            - role: end-user, agent, admin
            - email: email pattern or domain (@example.com)
            - name: text search in user name
            - organization: organization_id, "none"
            - tags: tag_name, "none"
            - verified: true, false
            - active: true, false
            - created: date or relative time
            - updated: date or relative time
            
            For Organizations:
            - name: text search in organization name
            - tags: tag_name, "none"
            - created: date or relative time
            - updated: date or relative time
            
            For Groups:
            - name: text search in group name
            - description: text search in group description
            - created: date or relative time
            - updated: date or relative time

            Relative Time Format:
            - Supports: hours/h, minutes/min, days/d, weeks/w, months, years/y
        sort_by (Optional[str]): Field to sort results by. Value can be created_at, updated_at, priority, status, ticket_type
        sort_order (Optional[str]): Sort order. Value can be asc, desc. Defaults to desc.
        page (int): Page number for pagination. Defaults to 1.
        per_page (int): Number of results per page (1-100). Defaults to 100.
        include (Optional[str]): Side-load related data. Comma-separated list like "users", or "users,organizations", "users,groups", "users,organizations,groups".

    Returns:
        Dict[str, Any]: A dictionary containing search results with the following structure:
            results (List[Dict[str, Any]]): Array of search result objects. Each result contains:
                id (int): Unique identifier for the object.
                url (str): API URL for the object.
                result_type (str): Type of object ("ticket", "user", "organization", "groups").
                created_at (str): Creation timestamp (ISO 8601 format).
                updated_at (str): Last update timestamp (ISO 8601 format).
                
                For tickets:
                    subject (str): Ticket subject line.
                    description (str): Ticket description.
                    status (str): Ticket status ("new", "open", "pending", "hold", "solved", "closed").
                    priority (str): Ticket priority ("low", "normal", "high", "urgent").
                    ticket_type (str): Ticket type ("problem", "incident", "question", "task").
                    assignee_id (Optional[int]): ID of assigned agent.
                    requester_id (Optional[int]): ID of ticket requester.
                    organization_id (Optional[int]): ID of associated organization.
                    group_id (Optional[int]): ID of assigned group.
                    tags (List[str]): Array of tags applied to the ticket.
                
                For users:
                    name (str): User's full name.
                    email (str): User's email address.
                    role (str): User role ("end-user", "agent", "admin").
                    active (bool): Whether the user account is active.
                    verified (bool): Whether the user's email is verified.
                    phone (str): User's phone number.
                    organization_id (Optional[int]): ID of user's organization.
                    tags (List[str]): Array of tags applied to the user.
                
                For organizations:
                    name (str): Organization name.
                    details (str): Organization details.
                    notes (str): Organization notes.
                    tags (List[str]): Array of tags applied to the organization.

                For groups:
                    name (str): Group name.
                    description (str): Group description.

            count (int): Total number of results found.
            page (int): Current page number.
            per_page (int): Number of results per page.
            next_page (Optional[str]): URL for next page (if exists).
            previous_page (Optional[str]): URL for previous page (if exists).
            
            When include parameter is used:
                users (Optional[List[Dict[str, Any]]]): Side-loaded user objects when "users" included.
                organizations (Optional[List[Dict[str, Any]]]): Side-loaded organization objects when "organizations" included.            
                groups (Optional[List[Dict[str, Any]]]):  Side-loaded groups objects when "groups" included.

    Raises:
        TypeError: When any parameter has an incorrect type (e.g., non-string query, 
            non-integer page/per_page).
        ValueError: When parameter values are invalid:
            - Trying to access search results beyond the 1000 record limit
            - page < 1
            - per_page < 1 or per_page > 100  
            - sort_by not in valid options
            - sort_order not 'asc' or 'desc'
    """
    
    # Input type validation
    if not isinstance(query, str):
        raise TypeError(f"query must be a string, got {type(query).__name__}")
    
    if sort_by is not None and not isinstance(sort_by, str):
        raise TypeError(f"sort_by must be a string or None, got {type(sort_by).__name__}")
    
    if sort_order is not None and not isinstance(sort_order, str):
        raise TypeError(f"sort_order must be a string or None, got {type(sort_order).__name__}")
    
    if not isinstance(page, int):
        raise TypeError(f"page must be an integer, got {type(page).__name__}")
    
    if not isinstance(per_page, int):
        raise TypeError(f"per_page must be an integer, got {type(per_page).__name__}")
    
    if include is not None and not isinstance(include, str):
        raise TypeError(f"include must be a string or None, got {type(include).__name__}")
    
    # Input value validation
    if page < 1:
        raise ValueError("page must be >= 1")
    
    if per_page < 1 or per_page > 100:
        raise ValueError("per_page must be between 1 and 100")
    
    if sort_by is not None and sort_by not in ["created_at", "updated_at", "priority", "status", "ticket_type"]:
        raise ValueError(f"sort_by must be one of: created_at, updated_at, priority, status, ticket_type. Got: {sort_by}")
    
    if sort_order is not None and sort_order not in ["asc", "desc"]:
        raise ValueError(f"sort_order must be 'asc' or 'desc'. Got: {sort_order}")
    
    # Parse the query string
    parsed_query = _parse_search_query(query)
    
    # Hard result limit check (Zendesk API limitation)
    max_results = 1000
    start_index = (page - 1) * per_page
    if start_index >= max_results:
        raise ValueError("422 Unprocessable Entity: Search results are limited to 1000 records. Please refine your search query to get fewer results.")
    
    # Get all data from different collections
    tickets = DB["tickets"].values()
    users = DB["users"].values()
    organizations = DB["organizations"].values()
    groups = DB.get("groups", {}).values()  # Use get() to avoid KeyError if groups doesn't exist
    
    results = []
    
    # Search each collection based on parsed query
    if not parsed_query.get("type_filter") or "ticket" in parsed_query.get("type_filter", []):
        ticket_results = _search_tickets(tickets, parsed_query)
        results.extend(ticket_results)
    
    if not parsed_query.get("type_filter") or "user" in parsed_query.get("type_filter", []):
        user_results = _search_users(users, parsed_query)
        results.extend(user_results)
    
    if not parsed_query.get("type_filter") or "organization" in parsed_query.get("type_filter", []):
        org_results = _search_organizations(organizations, parsed_query)
        results.extend(org_results)
    
    if not parsed_query.get("type_filter") or "group" in parsed_query.get("type_filter", []):
        group_results = _search_groups(groups, parsed_query)
        results.extend(group_results)
    
    # Apply sorting
    if sort_by:
        reverse = sort_order == "desc" if sort_order else True
        results = _sort_results(results, sort_by, reverse)
    
    # Apply pagination
    total_count = len(results)
    # Use the start_index calculated earlier for hard limit check
    end_index = start_index + per_page
    page_results = results[start_index:end_index]
    
    # Build response
    response = {
        "results": page_results,
        "count": total_count,
        "page": page,
        "per_page": per_page
    }
    
    # Add side-loaded data if requested
    if include:
        side_loaded_data = _get_side_loaded_data(include, page_results)
        response.update(side_loaded_data)
    
    # Add pagination URLs
    if page > 1:
        response["previous_page"] = f"?page={page - 1}&per_page={per_page}"
    
    if end_index < total_count:
        response["next_page"] = f"?page={page + 1}&per_page={per_page}"
    
    return response


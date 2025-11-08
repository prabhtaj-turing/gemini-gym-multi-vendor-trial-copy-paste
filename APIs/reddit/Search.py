from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine.db import DB
from typing import Dict, Any, Optional
import time

"""Simulation of the Reddit /search endpoint."""


@tool_spec(
    spec={
        'name': 'get_search',
        'description': 'Searches for content based on the provided query and parameters.',
        'parameters': {
            'type': 'object',
            'properties': {
                'q': {
                    'type': 'string',
                    'description': 'The search query string (maximum 512 characters).'
                },
                'after': {
                    'type': 'string',
                    'description': 'A cursor for paginating results after a certain point. Defaults to None.'
                },
                'before': {
                    'type': 'string',
                    'description': 'A cursor for paginating results before a certain point. Defaults to None.'
                },
                'category': {
                    'type': 'string',
                    'description': 'The category to filter search results by (maximum 5 characters). Defaults to None.'
                },
                'count': {
                    'type': 'integer',
                    'description': 'The number of results already seen. Defaults to 0.'
                },
                'include_facets': {
                    'type': 'boolean',
                    'description': 'Whether to include facet information in the results. Defaults to False.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of results to return (must be between 1 and 100). Defaults to 25.'
                },
                'restrict_sr': {
                    'type': 'boolean',
                    'description': 'Whether to restrict the search to the current subreddit (if applicable). Defaults to False.'
                },
                'show': {
                    'type': 'string',
                    'description': "A string to filter results by a specific type (e.g., 'all'). Defaults to None."
                },
                'sort': {
                    'type': 'string',
                    'description': 'The sorting method for results (\'relevance\', \'hot\', \'top\', \'new\', \'comments\'). Defaults to "relevance".'
                },
                'sr_detail': {
                    'type': 'boolean',
                    'description': 'Whether to include detailed information about the subreddit. Defaults to False.'
                },
                't': {
                    'type': 'string',
                    'description': "The time filter for top or controversial sorts ('hour', 'day', 'week', 'month', 'year', 'all'). Defaults to None."
                },
                'type': {
                    'type': 'string',
                    'description': "Comma-separated string of types to search for ('sr', 'link', 'user'). Defaults to None (all types)."
                }
            },
            'required': [
                'q'
            ]
        }
    }
)
def get_search(
    q: str,
    after: Optional[str] = None,
    before: Optional[str] = None,
    category: Optional[str] = None,
    count: int = 0,
    include_facets: bool = False,
    limit: int = 25,
    restrict_sr: bool = False,
    show: Optional[str] = None,
    sort: str = "relevance",
    sr_detail: bool = False,
    t: Optional[str] = None,
    type: Optional[str] = None
) -> Dict[str, Any]:
    """Searches for content based on the provided query and parameters.

    Args:
        q (str): The search query string (maximum 512 characters).
        after (Optional[str], optional): A cursor for paginating results after a certain point. Defaults to None.
        before (Optional[str], optional): A cursor for paginating results before a certain point. Defaults to None.
        category (Optional[str], optional): The category to filter search results by (maximum 5 characters). Defaults to None.
        count (int, optional): The number of results already seen. Defaults to 0.
        include_facets (bool, optional): Whether to include facet information in the results. Defaults to False.
        limit (int, optional): The maximum number of results to return (must be between 1 and 100). Defaults to 25.
        restrict_sr (bool, optional): Whether to restrict the search to the current subreddit (if applicable). Defaults to False.
        show (Optional[str], optional): A string to filter results by a specific type (e.g., 'all'). Defaults to None.
        sort (str, optional): The sorting method for results ('relevance', 'hot', 'top', 'new', 'comments'). Defaults to "relevance".
        sr_detail (bool, optional): Whether to include detailed information about the subreddit. Defaults to False.
        t (Optional[str], optional): The time filter for top or controversial sorts ('hour', 'day', 'week', 'month', 'year', 'all'). Defaults to None.
        type (Optional[str], optional): Comma-separated string of types to search for ('sr', 'link', 'user'). Defaults to None (all types).

    Returns:
        Dict[str, Any]: A dictionary representing a listing of items.
            The dictionary contains the following keys:
            - "kind" (str): Always "Listing".
            - "data" (dict): A dictionary containing the listing data, with the following keys:
                - "modhash" (str): An empty string.
                - "children" (list): A list of result items, where each item is a dictionary.
                - "after" (str or None): The ID of the 'data' attribute of the last item in the 'children' list, or None if the 'children' list is empty.
                - "before" (str or None): The ID of the 'data' attribute of the first item in the 'children' list, or None if the 'children' list is empty.

    Raises:
        ValueError: If the query string exceeds 512 characters.
        ValueError: If the category exceeds 5 characters.
        ValueError: If count is negative.
        ValueError: If limit is not between 1 and 100.
        ValueError: If sort is not one of 'relevance', 'hot', 'top', 'new', 'comments'.
        ValueError: If t is provided and is not one of 'hour', 'day', 'week', 'month', 'year', 'all'.
    """
    # Validate parameters
    if len(q) > 512:
        raise ValueError("Query string must be no longer than 512 characters")
        
    if category and len(category) > 5:
        raise ValueError("Category must be no longer than 5 characters")
        
    if count < 0:
        raise ValueError("Count must be a positive integer")
        
    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")
    if sort not in ["relevance", "hot", "top", "new", "comments"]:
        raise ValueError("Invalid sort method")
    if t and t not in ["hour", "day", "week", "month", "year", "all"]:
        raise ValueError("Invalid time filter")

    # Initialize results
    results = []
    current_time = int(time.time())
    time_threshold = current_time - {
        "hour": 3600,
        "day": 86400,
        "week": 604800,
        "month": 2592000,
        "year": 31536000,
        "all": float('inf')
    }.get(t, float('inf'))

    # Determine which types to search
    search_types = ["sr", "link", "user"]  # Default to all types
    if type:
        search_types = [t.strip() for t in type.split(",")]

    # Search in subreddits
    if "sr" in search_types:
        subreddits = DB.get("subreddits", {})
        if isinstance(subreddits, dict):
            for subreddit_id, subreddit in subreddits.items():
                if not isinstance(subreddit, dict):
                    continue
                    
                if time_threshold and t != "all":
                    subreddit_time = subreddit.get("created_utc", 0)
                    if subreddit_time < time_threshold:
                        continue

                if any(term.lower() in subreddit.get("display_name", "").lower() or 
                        term.lower() in subreddit.get("description", "").lower() 
                        for term in q.split()):
                    # Add the ID to the subreddit data for pagination
                    subreddit_with_id = subreddit.copy()
                    subreddit_with_id["id"] = subreddit_id
                    results.append({
                        "kind": "t5",
                        "data": subreddit_with_id
                    })

    # Search in posts/links
    if "link" in search_types:
        links = DB.get("links", {})
        
        # Handle both old list format and new dictionary format
        if isinstance(links, list):
            # Old format: links is a list
            for i, post in enumerate(links):
                if not isinstance(post, dict):
                    continue
                    
                if time_threshold and t != "all":
                    post_time = post.get("created_utc", 0)
                    if post_time < time_threshold:
                        continue

                if any(term.lower() in post.get("title", "").lower() or
                        term.lower() in post.get("text", "").lower()
                        for term in q.split()):
                    # Add the ID to the post data for pagination
                    post_with_id = post.copy()
                    # Use existing ID if present, otherwise generate one
                    if "id" not in post_with_id:
                        post_with_id["id"] = f"t3_{i}"
                    results.append({
                        "kind": "t3",
                        "data": post_with_id
                    })
        else:
            # New format: links is a dictionary
            for post_id, post in links.items():
                # Skip if post is not a dictionary
                if not isinstance(post, dict):
                    continue
                    
                if time_threshold and t != "all":
                    post_time = post.get("created_utc", 0)
                    if post_time < time_threshold:
                        continue

                if any(term.lower() in post.get("title", "").lower() or
                        term.lower() in post.get("text", "").lower()
                        for term in q.split()):
                    # Add the ID to the post data for pagination
                    post_with_id = post.copy()
                    post_with_id["id"] = post_id
                    results.append({
                        "kind": "t3",
                        "data": post_with_id
                    })

    # Search in users
    if "user" in search_types:
        users = DB.get("users", {})
        if isinstance(users, dict):
            for user_id, user in users.items():
                if not isinstance(user, dict):
                    continue
                    
                if time_threshold and t != "all":
                    user_time = user.get("created_utc", 0)
                    if user_time < time_threshold:
                        continue
                        
                if any(term.lower() in user.get("name", "").lower() or
                        term.lower() in user.get("description", "").lower()
                        for term in q.split()):
                    # Add the ID to the user data for pagination
                    user_with_id = user.copy()
                    user_with_id["id"] = user_id
                    results.append({
                        "kind": "t2",
                        "data": user_with_id
                    })

    # Apply sorting
    if sort == "relevance":
        # Sort by total frequency of query term matches across all fields
        def calculate_relevance_score(item):
            data = item["data"]
            fields = [
                data.get("title", "").lower(),
                data.get("text", "").lower(), 
                data.get("name", "").lower(),
                data.get("display_name", "").lower(),
                data.get("description", "").lower()
            ]
            
            total_score = 0
            for term in q.split():
                term_lower = term.lower()
                for field in fields:
                    total_score += field.count(term_lower)
            
            return total_score
        
        results.sort(key=calculate_relevance_score, reverse=True)
    elif sort == "hot":
        pass
    elif sort == "top":
        # Sort by score (upvotes minus downvotes)
        results.sort(key=lambda x: x["data"].get("score", 0), reverse=True)
    elif sort == "new":
        # Sort by creation date
        results.sort(key=lambda x: x["data"].get("created_utc", 0), reverse=True)
    elif sort == "comments":
        # Sort by number of comments
        results.sort(key=lambda x: x["data"].get("num_comments", 0), reverse=True)

    # Apply pagination
    if after:
        after_index = next((i for i, r in enumerate(results) if r["data"].get("id") == after), -1)
        if after_index >= 0:
            results = results[after_index + 1:]
    if before:
        before_index = next((i for i, r in enumerate(results) if r["data"].get("id") == before), len(results))
        if before_index < len(results):
            results = results[:before_index]
            
    # Apply limit
    results = results[:limit]
    
    # Build response in Listing format
    response = {
        "kind": "Listing",
        "data": {
            "modhash": "",  # Empty modhash in simulation
            "children": results,
            "after": results[-1]["data"].get("id") if results else None,
            "before": results[0]["data"].get("id") if results else None
        }
    }
    
    return response
"""
Utility functions for the Instagram API Simulation.
"""
import re
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

def generate_id() -> str:
    """
    Generate a unique identifier for new entities.
    
    Returns:
        str: A unique UUID string
    """
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        str: Current timestamp in ISO format
    """
    return datetime.now().isoformat()

def validate_user_id_format(user_id: str) -> None:
    """
    Validates that user_id contains only alphanumeric characters, underscores, and periods.
    
    Args:
        user_id (str): The user ID to validate
        
    Raises:
        ValueError: If user_id contains invalid characters
    """
    if not re.match(r'^[a-zA-Z0-9_.]+$', user_id):
        raise ValueError("User ID can only contain letters, numbers, underscores, and periods.")

def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL format.
    
    Args:
        url (str): URL string to validate
        
    Returns:
        bool: True if valid URL format, False otherwise
    """
    url_pattern = re.compile(
        r'^(https?://)?'  # http:// or https://
        r'(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})'  # domain...
        r'(:\d+)?'  # optional port
        r'(/[-a-zA-Z0-9@:%._+~#=]*)?'  # optional path
        r'(\?[;&a-zA-Z0-9@:%._+~#=]*)?'  # optional query string
        r'(#[-a-zA-Z0-9_]*)?$'  # optional fragment
    )
    return bool(url_pattern.match(url))

def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string by trimming whitespace and optionally truncating.
    
    Args:
        text (str): Text to sanitize
        max_length (Optional[int]): Maximum length allowed
        
    Returns:
        str: Sanitized text
        
    Raises:
        ValueError: If text is empty after trimming or exceeds max_length
    """
    if not isinstance(text, str):
        raise TypeError("Text must be a string")
    
    sanitized = text.strip()
    if not sanitized:
        raise ValueError("Text cannot be empty or contain only whitespace")
    
    if max_length and len(sanitized) > max_length:
        raise ValueError(f"Text exceeds maximum length of {max_length} characters")
    
    return sanitized

def paginate_results(results: List[Dict[str, Any]], page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    """
    Paginate a list of results.
    
    Args:
        results (List[Dict[str, Any]]): List of results to paginate
        page (int): Page number (1-based)
        per_page (int): Number of items per page
        
    Returns:
        Dict[str, Any]: Paginated results with metadata
    """
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 10
    
    total_items = len(results)
    total_pages = (total_items + per_page - 1) // per_page
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_items = results[start_idx:end_idx]
    
    return {
        "items": paginated_items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    } 
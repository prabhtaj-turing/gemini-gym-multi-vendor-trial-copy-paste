from common_utils.tool_spec_decorator import tool_spec
# APIs/confluence/Search.py
from typing import Dict, List, Any, Optional
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _evaluate_cql_tree, _preprocess_cql_functions
from .SimulationEngine.custom_errors import InvalidPaginationValueError, InvalidParameterValueError
import re


@tool_spec(
    spec={
        'name': 'search_content',
        'description': """ Search for content based on a CQL (Confluence Query Language) query.
        
        This function performs a comprehensive search across all content items using the provided CQL query.
        It supports complex queries with logical operators, field comparisons, and returns paginated results
        with optional field expansion. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The CQL query string. Supported syntax:
                    - Field operators: = (equals), != (not equals), ~ (contains), !~ (does not contain),
                      >, <, >=, <= (numeric/date comparison)
                    - Logical operators: AND, OR, NOT (case-insensitive)
                    - Grouping: Use parentheses () for complex expressions
                    - Value types: Strings ('value' or "value"), Numbers (123 or 45.67), Keywords (null, true, false), Functions (now())
                    - Supported fields: type, space, spaceKey, title, status, id, text, created, postingDay, label
                    - Field mappings:
                        * type: Content type ('page', 'blogpost', 'comment', 'attachment')
                        * space/spaceKey: The key of the space containing this content
                        * title: The title/name of the content item
                        * status: Content status
                        * id: Unique identifier for the content item
                        * text: Master field that searches across title, content body, and labels (supports ~ and !~ operators)
                        * created: Maps to history.createdDate (supports date comparison operators)
                        * postingDay: Direct field on blogpost content (YYYY-MM-DD format, supports date comparison)
                        * label: Searches content labels directly (supports =, != operators for exact match)
                        - Examples:
                          * "type='page' AND spaceKey='DOC'"
                          * "type='page' AND space='DOC'"
                          * "title~'meeting' OR title~'notes'"
                          * "status='current' AND NOT type='comment'"
                          * "text~'marketing' AND type='page'"
                          * "created>='2024-01-01T00:00:00.000Z'"
                          * "type='blogpost' AND postingDay>='2024-01-01'"
                          * "label='finished' AND type='page'"
                          * "label!='draft' OR type='blogpost'"
                          * "id = 1" (unquoted number)
                          * "postingDay = null" (null keyword for fields without values)
                          * "postingDay != null" (fields that have values)
                    - CQL Functions:
                      * now(): Current timestamp
                      * now("-4w"): 4 weeks ago
                      * now("+1d"): 1 day from now
                      * Supported units: d/day, w/week, m/month, y/year, h/hour, min/minute
                    - Function Examples:
                      * "created > now('-4w')" - Content created in last 4 weeks
                      * "title~'project launch' and created > now('-4w')" - Project launch content from last 4 weeks
                    - Note: space field is used for CQL queries, expand='space' returns structured objects """
                },
                'expand': {
                    'type': 'string',
                    'description': """ Comma-separated list of properties to expand in results.
                    Supported values:
                    - space: Include detailed space information (object with 'key', 'name', 'description' fields)
                    - version: Include version information (enhanced object format)
                    - body: Include content body with proper storage structure (may affect pagination limits)
                    - body.storage: Include only the storage representation of the body
                    - body.view: Include only the view representation of the body
                    - metadata: Include content metadata (labels and properties)
                    - metadata.labels: Include only the labels from metadata
                    - history: Include content history information (integrated with ContentAPI)
                    - ancestors: Include ancestor content references
                    - container: Include the same information as the space field """
                },
                'start': {
                    'type': 'integer',
                    'description': 'Starting index for pagination (default: 0, must be non-negative)'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'Maximum number of results to return (default: 25, range: 1-1000)'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def search_content(
    query: str, expand: Optional[str] = None, start: Optional[int] = 0, limit: Optional[int] = 25
) -> List[Dict[str, Any]]:
    """
    Search for content based on a CQL (Confluence Query Language) query.

    This function performs a comprehensive search across all content items using the provided CQL query.
    It supports complex queries with logical operators, field comparisons, and returns paginated results
    with optional field expansion.

    Args:
        query (str): The CQL query string. Supported syntax:
            - Field operators: = (equals), != (not equals), ~ (contains), !~ (does not contain),
              >, <, >=, <= (numeric/date comparison)
            - Logical operators: AND, OR, NOT (case-insensitive)
            - Grouping: Use parentheses () for complex expressions
            - Value types: Strings ('value' or "value"), Numbers (123 or 45.67), Keywords (null, true, false), Functions (now())
            - Supported fields: type, space, spaceKey, title, status, id, text, created, postingDay, label
            - Field mappings:
                * type: Content type ('page', 'blogpost', 'comment', 'attachment')
                * space/spaceKey: The key of the space containing this content
                * title: The title/name of the content item
                * status: Content status
                * id: Unique identifier for the content item
                * text: Master field that searches across title, content body, and labels (supports ~ and !~ operators)
                * created: Maps to history.createdDate (supports date comparison operators)
                * postingDay: Direct field on blogpost content (YYYY-MM-DD format, supports date comparison)
                * label: Searches content labels directly (supports =, != operators for exact match)
                - Examples:
                  * "type='page' AND spaceKey='DOC'"
                  * "type='page' AND space='DOC'"
                  * "title~'meeting' OR title~'notes'"
                  * "status='current' AND NOT type='comment'"
                  * "text~'marketing' AND type='page'"
                  * "created>='2024-01-01T00:00:00.000Z'"
                  * "type='blogpost' AND postingDay>='2024-01-01'"
                  * "label='finished' AND type='page'"
                  * "label!='draft' OR type='blogpost'"
                  * "id = 1" (unquoted number)
                  * "postingDay = null" (null keyword for fields without values)
                  * "postingDay != null" (fields that have values)
            - CQL Functions:
              * now(): Current timestamp
              * now("-4w"): 4 weeks ago
              * now("+1d"): 1 day from now
              * Supported units: d/day, w/week, m/month, y/year, h/hour, min/minute
            - Function Examples:
              * "created > now('-4w')" - Content created in last 4 weeks
              * "title~'project launch' and created > now('-4w')" - Project launch content from last 4 weeks
            - Note: space field is used for CQL queries, expand='space' returns structured objects
        
        expand (Optional[str]): Comma-separated list of properties to expand in results.
            Supported values:
            - space: Include detailed space information (object with 'key', 'name', 'description' fields)
            - version: Include version information (enhanced object format)
            - body: Include content body with proper storage structure (may affect pagination limits)
            - body.storage: Include only the storage representation of the body
            - body.view: Include only the view representation of the body
            - metadata: Include content metadata (labels and properties)
            - metadata.labels: Include only the labels from metadata
            - history: Include content history information (integrated with ContentAPI)
            - ancestors: Include ancestor content references
            - container: Include the same information as the space field
        
        start (Optional[int]): Starting index for pagination (default: 0, must be non-negative)
        limit (Optional[int]): Maximum number of results to return (default: 25, range: 1-1000)

    Returns:
        List[Dict[str, Any]]: List of content items matching the search criteria. Base fields include:
            - id (str): Unique identifier for the content item
            - type (str): Content type ('page', 'blogpost', 'comment', 'attachment')
            - spaceKey (str): The key of the space containing this content
            - title (str): The title/name of the content item
            - status (str): Content status
            - body (Dict[str, str]): Content body with nested structure:
                - storage (str): The actual content in Confluence storage format
            - postingDay (Optional[str]): Publication date for blogposts (YYYY-MM-DD format), null for pages
            
        Additional fields are included based on the expand parameter:
            - space: Structured space object with 'key', 'name', and 'description' fields (modern format)
            - version: Version information array format (consistent with ContentAPI)
            - body: Content body with proper storage structure
            - body.storage: Only the storage representation of the body
            - body.view: Only the view representation of the body (converted from storage)
            - metadata: Additional content properties and labels
            - metadata.labels: Only the labels from metadata
            - history: Creation and modification history (integrated with ContentAPI)
            - ancestors: References to ancestor content items
            - container: The same information as the space field

    Raises:
        TypeError: If 'query' is not a string, or 'start'/'limit' are not integers.
        InvalidPaginationValueError: If 'start' is negative or 'limit' is outside valid range (1-1000).
        InvalidParameterValueError: If 'expand' contains unsupported field names.
        ValueError: If the CQL query is missing, empty, or contains invalid syntax.
        
    """
    # Input validation
    if not isinstance(query, str):
        raise TypeError("Argument 'query' must be a string.")
    if expand is not None and not isinstance(expand, str):
        raise TypeError("Argument 'expand' must be a string if provided.")
    if not isinstance(start, int):
        raise TypeError("Argument 'start' must be an integer.")
    if not isinstance(limit, int):
        raise TypeError("Argument 'limit' must be an integer.")

    if start < 0:
        raise InvalidPaginationValueError("Argument 'start' must be non-negative.")
    if not (1 <= limit <= 1000):
        raise InvalidPaginationValueError("Argument 'limit' must be between 1 and 1000.")

    if not query.strip():
        raise ValueError("CQL query is missing.")
    
    # Preprocess CQL functions (like now()) before tokenizing
    try:
        query = _preprocess_cql_functions(query)
    except ValueError as e:
        raise ValueError(f"CQL function error: {str(e)}")
        
    # Validate expand parameter
    expand_fields = []
    if expand and expand.strip():
        ALLOWED_EXPAND_FIELDS = {
            "space", "version", "body", "metadata", "history",
            "ancestors", "container"
        }
        ALLOWED_NESTED_EXPAND_FIELDS = {
            "body.storage", "body.view", "metadata.labels"
        }
        ALL_ALLOWED_FIELDS = ALLOWED_EXPAND_FIELDS | ALLOWED_NESTED_EXPAND_FIELDS
        
        fields = [field.strip() for field in expand.split(',')]
        for field in fields:
            if not field:  # Handle cases like "space,,version"
                raise InvalidParameterValueError("Argument 'expand' contains an empty field name.")
            if field not in ALL_ALLOWED_FIELDS:
                raise InvalidParameterValueError(
                    f"Argument 'expand' contains an invalid field '{field}'. "
                    f"Allowed fields are: {', '.join(sorted(ALL_ALLOWED_FIELDS))}."
                )
        expand_fields = fields

    # Get all contents from database
    all_contents = list(DB["contents"].values())

    # Enhanced tokenizer regex with support for quoted strings, numbers, keywords, and functions
    tokenizer_regex = r"""
        \b(?:and|or|not)\b|                 # Match 'and', 'or', 'not' as whole words
        \(|\)|                              # Match '(' or ')'
        \w+\s*(?:>=|<=|!=|!~|>|<|=|~)\s*   # Match field name and operator part
        (?:                                 # Non-capturing group for value types
            '[^']*'|                        # Match single-quoted string
            \"[^\"]*\"|                     # Match double-quoted string
            \w+\([^)]*\)|                   # Match function calls like now()
            \b(?:null|true|false)\b|        # Match keywords (case-insensitive)
            \d+(?:\.\d+)?                   # Match numbers (integers and decimals)
        )
    """
    tokens = re.findall(tokenizer_regex, query, re.IGNORECASE | re.VERBOSE)
    
    # Enhanced validation with better error messages
    untokenized_remains = re.sub(tokenizer_regex, "", query, flags=re.IGNORECASE | re.VERBOSE)
    if untokenized_remains.strip():
        # Provide more specific error messages for common issues
        remaining = untokenized_remains.strip()
        
        # Check for common syntax errors with improved detection
        if re.search(r'==', remaining):  # Check for == operator first
            raise ValueError(
                "CQL query is invalid: Unsupported operator detected. "
                "Found '==' operator. Use single '=' for equality. "
                "Supported operators: =, !=, >, <, >=, <=, ~, !~"
            )
        elif re.search(r'\w+\s*[>=<!~]+\s*\w+(?!["\'])', remaining):
            raise ValueError(
                "CQL query is invalid: String values must be quoted. "
                f"Found unquoted value in: '{remaining}'. "
                "Use single or double quotes around string values."
            )
        elif re.search(r'["\'][^"\'\n]*$', remaining):  # Unclosed quote
            raise ValueError(
                "CQL query is invalid: Unclosed quote detected. "
                "Ensure all quoted strings are properly closed."
            )
        elif re.search(r'\w+\s*[^>=<!~\s\'"()]+', remaining):  # Improved unsupported operator detection
            raise ValueError(
                "CQL query is invalid: Unsupported operator detected. "
                "Supported operators: =, !=, >, <, >=, <=, ~, !~"
            )
        else:
            raise ValueError(
                f"CQL query is invalid: Unrecognized syntax '{remaining}'. "
                "Check field names, operators, and quote usage."
            )

    # Validate field names in tokens for better error reporting
    supported_fields = {"type", "space", "spaceKey", "title", "status", "id", "text", "created", "postingday", "label"}
    supported_fields_lower = {field.lower() for field in supported_fields}
    for token in tokens:
        token_lower = token.lower().strip()
        if token_lower not in {"and", "or", "not", "(", ")"}:
            # Check if it's a field expression
            field_match = re.match(r'(\w+)\s*[>=<!~]+', token, re.IGNORECASE)
            if field_match:
                field_name = field_match.group(1).lower()
                if field_name not in supported_fields_lower:
                    raise ValueError(
                        f"CQL query contains unsupported field '{field_match.group(1)}'. "
                        f"Supported fields are: {', '.join(sorted(supported_fields))}."
                    )

    # Filter contents based on the CQL query with enhanced error handling
    try:
        filtered_contents = [
            content for content in all_contents if _evaluate_cql_tree(content, tokens)
        ]
    except ValueError as e:
        # Re-raise ValueError with CQL context
        raise ValueError(f"CQL evaluation error: {str(e)}")
    except Exception as e:
        # Provide more informative error for unexpected issues
        raise ValueError(
            f"CQL query processing failed: {str(e)}. "
            "Please check your query syntax and try again."
        )

    # Apply pagination
    paginated_results = filtered_contents[start : start + limit]
    
    # Apply expand functionality if requested
    if expand_fields:
        expanded_results = []
        for content in paginated_results:
            expanded_content = content.copy()
            
            for field in expand_fields:
                if field == "space" or field == "container":
                    # Fetch space data from DB.spaces and append
                    space_key = content.get("spaceKey")
                    
                    if space_key and space_key in DB.get("spaces", {}):
                        space_data = DB["spaces"][space_key]
                        if field == "container":
                            expanded_content["container"] = space_data
                        else:
                            expanded_content["space"] = space_data
                        
                
                elif field == "version":
                    # Version returns information about the most recent update of the content,
                    # including who updated it and when it was updated
                    existing_version = content.get("version", {})
                    
                    # Get most recent update information from history
                    if "history" in content:
                        enhanced_version = existing_version.copy()
                        
                        # Add when (most recent update time)
                        if "lastUpdated" in content["history"]:
                            enhanced_version["when"] = content["history"]["lastUpdated"]
                        elif "createdDate" in content["history"]:
                            enhanced_version["when"] = content["history"]["createdDate"]
                        
                        # Add by (most recent updater)
                        if "lastUpdatedBy" in content["history"]:
                            enhanced_version["by"] = content["history"]["lastUpdatedBy"]
                        elif "createdBy" in content["history"]:
                            enhanced_version["by"] = content["history"]["createdBy"]
                        
                        expanded_content["version"] = enhanced_version
                    else:
                        # No history available, keep existing version as is
                        expanded_content["version"] = existing_version
                    
                elif field == "body":
                    # Body is already included in base content, ensure it's properly structured
                    body = expanded_content.get("body")
                    if not body or (isinstance(body, dict) and not body):  # Handle missing or empty body
                        expanded_content["body"] = {"storage": {"value": "", "representation": "storage"}}
                    elif isinstance(body, dict) and "storage" in body:
                        # Ensure proper structure for existing body
                        storage = body["storage"]
                        if isinstance(storage, str):
                            expanded_content["body"]["storage"] = {"value": storage, "representation": "storage"}
                        elif isinstance(storage, dict) and "representation" not in storage:
                            storage["representation"] = "storage"
                    else:
                        # Body exists but doesn't have storage structure, create it
                        expanded_content["body"] = {"storage": {"value": "", "representation": "storage"}}
                            
                elif field == "metadata":
                    # Add metadata including labels and properties
                    content_id = content.get("id")
                    metadata = {}
                    
                    # Add labels if available
                    if content_id and content_id in DB.get("content_labels", {}):
                        metadata["labels"] = {
                            "results": [{"name": label} for label in DB["content_labels"][content_id]],
                            "size": len(DB["content_labels"][content_id])
                        }
                    else:
                        metadata["labels"] = {"results": [], "size": 0}
                        
                    # Add properties if available
                    if content_id and content_id in DB.get("content_properties", {}):
                        prop = DB["content_properties"][content_id]
                        metadata["properties"] = {
                            "results": [prop],
                            "size": 1
                        }
                    else:
                        metadata["properties"] = {"results": [], "size": 0}
                        
                    expanded_content["metadata"] = metadata
                    
                elif field == "history":
                    # Keep existing history as-is (official API doesn't specify additional fields)
                    existing_history = content.get("history", {})
                    
                    # Simply use the existing history data as per official API
                    expanded_content["history"] = existing_history
                    
                elif field == "children":
                    # Add children information (simplified - no actual child traversal in current DB structure)
                    expanded_content["children"] = {
                        "results": [],
                        "size": 0
                    }
                    
                elif field == "ancestors":
                    # Enhance existing ancestors with full details (simple array as per official API)
                    existing_ancestors = content.get("ancestors", [])
                    if existing_ancestors:
                        enhanced_ancestors = []
                        for ancestor in existing_ancestors:
                            if isinstance(ancestor, dict) and "id" in ancestor:
                                ancestor_id = ancestor["id"]
                                ancestor_content = DB["contents"].get(ancestor_id)
                                if ancestor_content:
                                    # Add full ancestor details
                                    ancestor_space_key = ancestor_content.get("spaceKey")
                                    ancestor_space = {}
                                    if ancestor_space_key and ancestor_space_key in DB.get("spaces", {}):
                                        ancestor_space = DB["spaces"][ancestor_space_key]
                                    
                                    enhanced_ancestor = {
                                        "id": ancestor_id,
                                        "type": ancestor_content.get("type", "page"),
                                        "title": ancestor_content.get("title", ""),
                                        "status": ancestor_content.get("status", "current"),
                                        "space": ancestor_space,
                                        "_links": ancestor_content.get("_links", {})
                                    }
                                    enhanced_ancestors.append(enhanced_ancestor)
                                else:
                                    # Keep original if ancestor not found
                                    enhanced_ancestors.append(ancestor)
                            else:
                                # Keep original format if not expected structure
                                enhanced_ancestors.append(ancestor)
                        
                        # Simple array format as per official API (not results/size structure)
                        expanded_content["ancestors"] = enhanced_ancestors
                    else:
                        # No ancestors exist - empty array
                        expanded_content["ancestors"] = []
                

                # Handle nested expand fields
                elif field == "body.storage":
                    # Add only storage representation of body
                    if "body" not in expanded_content:
                        expanded_content["body"] = {}
                    
                    body = expanded_content.get("body", {})
                    if isinstance(body, dict) and "storage" in body:
                        storage_value = body["storage"]
                        if isinstance(storage_value, str):
                            expanded_content["body"]["storage"] = {"value": storage_value, "representation": "storage"}
                        elif isinstance(storage_value, dict):
                            expanded_content["body"]["storage"] = {
                                "value": storage_value.get("value", ""),
                                "representation": "storage"
                            }
                    else:
                        expanded_content["body"]["storage"] = {"value": "", "representation": "storage"}
                
                elif field == "body.view":
                    # Add view representation of body (converted from storage)
                    if "body" not in expanded_content:
                        expanded_content["body"] = {}
                    
                    body = expanded_content.get("body", {})
                    storage_content = ""
                    if isinstance(body, dict) and "storage" in body:
                        storage = body["storage"]
                        if isinstance(storage, str):
                            storage_content = storage
                        elif isinstance(storage, dict):
                            storage_content = storage.get("value", "")
                    
                    # Convert storage format to view format (simplified)
                    view_content = storage_content.replace("<p>", "").replace("</p>", "\n").strip()
                    expanded_content["body"]["view"] = {"value": view_content, "representation": "view"}
                
                elif field == "metadata.labels":
                    # Add only labels from metadata
                    if "metadata" not in expanded_content:
                        expanded_content["metadata"] = {}
                    
                    content_id = content.get("id")
                    if content_id and content_id in DB.get("content_labels", {}):
                        expanded_content["metadata"]["labels"] = {
                            "results": [{"name": label} for label in DB["content_labels"][content_id]],
                            "size": len(DB["content_labels"][content_id])
                        }
                    else:
                        expanded_content["metadata"]["labels"] = {"results": [], "size": 0} 
            expanded_results.append(expanded_content)
        return expanded_results
    
    return paginated_results

## Comparison between objects

# - compare_strings
# - compare_datetimes
# - compare_is_list_subset


def normalize_string(string1) -> str:
    """
    Normalizes a string by lowercasing, removing simple punctuations 
    and leading/trailling spaces.
    """
    return (str(string1)
            .replace(".", "")
            .replace(",", "")
            .replace(";", "")
            .replace(":","")
            .strip()
            .lower())

def compare_strings(
    string1,
    string2
) -> bool:
    """
    Compares two strings by first lowering case and remove leading/trailling spaces.

    Args:
    string1 (str): The first string to be compared.
    string2 (str): The second string to be compared.

    Returns:
    bool: True if the strings are identical after applying the chosen normalization logic,
            False otherwise.

    """

    string1 = str(string1)
    string2 = str(string2)

    # Remove leading and trailing whitespaces
    string1_processed = normalize_string(string1)
    string2_processed = normalize_string(string2)

    return string1_processed == string2_processed

def compare_datetimes(dt_obj1, dt_obj2, comparison_type: str = "eq") -> bool:
    """
    Compares two datetime objects based on a specified comparison type.

    This function allows for flexible comparisons (equality, greater than, less than)
    between two `datetime.datetime` objects. It correctly handles scenarios where
    the original string formats of the datetimes might have varied, as long as
    they were successfully parsed into valid `datetime` objects.

    Args:
        dt_obj1 (datetime.datetime): The first datetime object for comparison.
        dt_obj2 (datetime.datetime): The second datetime object for comparison.
        comparison_type (str): Specifies the type of comparison to perform.
                               Valid options are:
                               - "eq": Checks for exact equality (`dt_obj1 == dt_obj2`).
                               - "gt": Checks if the first datetime is greater than the second (`dt_obj1 > dt_obj2`).
                               - "gte": Checks if the first datetime is greater than or equal to the second (`dt_obj1 >= dt_obj2`).
                               - "lte": Checks if the first datetime is less than or equal to the second (`dt_obj1 <= dt_obj2`).
                               - "lt": Checks if the first datetime is less than the second (`dt_obj1 < dt_obj2`).

    Returns:
        bool: `True` if the comparison condition is met; `False` otherwise.

    Raises:
        TypeError: If either `dt_obj1` or `dt_obj2` is not a `datetime.datetime` object.
        ValueError: If `comparison_type` is not one of the allowed values ("eq", "gt", "lt").
    """
    from datetime import datetime

    if not isinstance(dt_obj1, datetime) or not isinstance(dt_obj2, datetime):
        raise TypeError("Both arguments must be datetime objects.")

    if comparison_type == "eq":
        return dt_obj1 == dt_obj2
    elif comparison_type == "gt":
        return dt_obj1 > dt_obj2
    elif comparison_type == "gte":
        return dt_obj1 >= dt_obj2
    elif comparison_type == "lte":
        return dt_obj1 <= dt_obj2
    elif comparison_type == "lt":
        return dt_obj1 < dt_obj2
    else:
        raise ValueError("Invalid comparison type. Must be 'eq', 'gt', 'gte', 'lte', or 'lt'.")

def compare_is_list_subset(search_value, input_list:list, list_comparison_function:str="all") -> bool:
    """
    Checks for the presence of a value or multiple values within a list,
    handling string normalization and flexible list comparisons.

    Args:
        search_value: The item(s) to find. Can be a single value (like a string or int)
                      or a list of values. If it's a string or contains strings,
                      they'll be normalized (e.g., lowercased) for comparison.
        input_list (list): The list to search through. Any strings within this list
                           will also be normalized to ensure consistent comparisons.
        list_comparison_function: Controls how the search behaves when `search_value` is a list.
                                  Must be either "all" or "any":
                                  - "all": Returns `True` only if **every** normalized item
                                           from `search_value` is found in `input_list`.
                                  - "any": Returns `True` if **at least one** normalized item
                                           from `search_value` is found in `input_list`.

    Returns:
        bool: `True` if the search criteria are met; `False` otherwise.

    Raises:
        TypeError: If `input_list` is not actually a list.
        ValueError: If `search_value` is a list and `list_comparison_function`
                    is not set to "all" or "any".
    """

    if not isinstance(input_list, list):
        raise TypeError("input_list must be a list")
    if len(input_list) == 0:
        raise ValueError("input_list must not be empty")
    if len(search_value) == 0:
        raise ValueError("search_value must not be empty")
    
    input_list = [normalize_string(item) if isinstance(item, str) else item for item in input_list]


    if isinstance(search_value, str):
        search_value = normalize_string(search_value)
        return search_value in input_list

    elif isinstance(search_value, list):
        if list_comparison_function not in ["all", "any"]:
            raise ValueError("The 'comparison_type' parameter must be 'all' or 'any'.")

        search_value = [normalize_string(item) if isinstance(item, str) else item for item in search_value ]

        if list_comparison_function == "all":
            return all(item in input_list for item in search_value)
        elif list_comparison_function == "any":
            return any(item in input_list for item in search_value)
    else:
        return search_value in input_list
         
def compare_is_string_subset(search_value, string_to_check) -> bool:
    """
    Checks if a search value is a substring of an input string.

    Args:
        search_value (str): The substring to search for.
        string_to_check (str): The string to search within.

    Returns:
        bool: True if the search value is a substring of the input string, False otherwise.
    """
    search_value = str(search_value)
    string_to_check = str(string_to_check)

    if len(search_value) == 0:
        raise ValueError("search_value must not be empty")
    if len(string_to_check) == 0:
        raise ValueError("string_to_check must not be empty")
    


    # Remove leading and trailing whitespaces
    search_value_processed = normalize_string(search_value)
    string_to_check_processed = normalize_string(string_to_check)

    return search_value_processed in string_to_check_processed

def parse_iso_datetime_string_to_utc(timestamp_str):
    """
    Converts an ISO 8601/RFC3339 timestamp string to a timezone-aware UTC datetime object.

    This function accepts multiple timestamp formats and always returns a
    timezone-aware datetime object in UTC. It is robust against common variations
    in date/time formats found in APIs and logs.

    Args:
        timestamp_str (str): The timestamp string in ISO 8601/RFC3339 format.
                             It may or may not include a timezone, fractional seconds,
                             and use 'Z' or '+00:00' to indicate UTC.

    Returns:
        datetime: A datetime object in UTC with a defined timezone, or None if the
                  input string is empty or None.

    Accepted formats:
        - "2023-12-25T14:30:00Z"
        - "2023-12-25T14:30:00+00:00" 
        - "2023-12-25T14:30:00.123Z"
        - "2023-12-25T14:30:00-03:00"
        - "2023-12-25T14:30:00" (assumed to be UTC)

    Example:
        >>> parse_iso_datetime_to_utc("2023-12-25T14:30:00Z")
        datetime.datetime(2023, 12, 25, 14, 30, tzinfo=datetime.timezone.utc)
        
        >>> parse_iso_datetime_to_utc("2023-12-25T14:30:00-03:00")
        datetime.datetime(2023, 12, 25, 17, 30, tzinfo=datetime.timezone.utc)
    """
    from datetime import datetime, timezone

    if not timestamp_str:
        return None
        
    # Normalize 'Z' to standard timezone format
    normalized_str = timestamp_str.replace("Z", "+00:00")
    
    try:
        # Primary attempt: use fromisoformat (Python 3.7+)
        dt = datetime.fromisoformat(normalized_str)
        if dt.tzinfo is None:
            # If no timezone, assume UTC
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
        
    except ValueError:
        # Fallback 1: try strptime with timezone
        try:
            return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S%z").astimezone(timezone.utc)
            
        except Exception:
            # Fallback 2: strip fractional seconds and try again
            main_part = timestamp_str.split('.')[0].rstrip('Z')
            return datetime.strptime(main_part, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
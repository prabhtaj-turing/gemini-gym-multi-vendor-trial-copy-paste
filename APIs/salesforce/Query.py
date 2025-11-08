from common_utils.tool_spec_decorator import tool_spec
# APIs/salesforce/Query.py
from typing import List, Tuple, Dict, Any, Union
import urllib.parse
import re
from datetime import datetime, timedelta
from salesforce.SimulationEngine.db import DB
from salesforce.SimulationEngine.models import ConditionsListModel, ValidationError
from salesforce.SimulationEngine import custom_errors


def _parse_where_clause(condition_string: str) -> Union[Dict, None]:
    """
    Parse a WHERE clause string into a condition tree that supports AND/OR operations.
    
    Args:
        condition_string (str): The WHERE clause content (without the WHERE keyword)
        
    Returns:
        Dict: Condition tree with structure:
            - {"type": "condition", "field": str, "operator": str, "value": str/list}
            - {"type": "and", "conditions": [condition1, condition2, ...]}
            - {"type": "or", "conditions": [condition1, condition2, ...]}
    """
    if not condition_string.strip():
        return None
    
    # Handle parentheses by recursively parsing grouped expressions
    condition_string = condition_string.strip()
    
    # Find top-level AND/OR operators (not inside parentheses)
    and_positions = _find_top_level_operators(condition_string, "AND")
    or_positions = _find_top_level_operators(condition_string, "OR")
    
    # If we have both AND and OR at the same level, we need to handle precedence
    # In SOQL, AND has higher precedence than OR
    if or_positions:
        # Split by OR first (lowest precedence)
        conditions = []
        last_pos = 0
        for pos in or_positions:
            part = condition_string[last_pos:pos].strip()
            conditions.append(_parse_where_clause(part))
            last_pos = pos + 2  # Skip "OR"
        # Don't forget the last part
        part = condition_string[last_pos:].strip()
        conditions.append(_parse_where_clause(part))
        return {"type": "or", "conditions": [c for c in conditions if c]}
    
    elif and_positions:
        # Split by AND
        conditions = []
        last_pos = 0
        for pos in and_positions:
            part = condition_string[last_pos:pos].strip()
            conditions.append(_parse_where_clause(part))
            last_pos = pos + 3  # Skip "AND"
        # Don't forget the last part
        part = condition_string[last_pos:].strip()
        conditions.append(_parse_where_clause(part))
        return {"type": "and", "conditions": [c for c in conditions if c]}
    
    else:
        # Single condition or parenthesized expression
        if condition_string.startswith('(') and condition_string.endswith(')'):
            # Remove outer parentheses and parse the inner content
            inner = condition_string[1:-1].strip()
            return _parse_where_clause(inner)
        else:
            # Parse single condition
            return _parse_single_condition(condition_string)


def _find_top_level_operators(text: str, operator: str) -> List[int]:
    """Find positions of operators that are not inside parentheses."""
    positions = []
    paren_depth = 0
    i = 0
    
    while i < len(text):
        if text[i] == '(':
            paren_depth += 1
        elif text[i] == ')':
            paren_depth -= 1
        elif paren_depth == 0:
            # Check if we're at the start of the operator
            if (text[i:i+len(operator)] == operator and 
                (i == 0 or text[i-1].isspace()) and 
                (i + len(operator) >= len(text) or text[i + len(operator)].isspace())):
                positions.append(i)
                i += len(operator) - 1  # Skip the operator
        i += 1
    
    return positions


def _parse_in_values(values_str: str) -> List[str]:
    """
    Parse comma-separated values in an IN clause, respecting quoted strings.
    Handles cases like: 'value1', 'value2', 'value with, comma'
    
    Args:
        values_str: String containing comma-separated values
        
    Returns:
        List of parsed values with quotes removed
    """
    values = []
    current_value = []
    in_quotes = False
    quote_char = None
    
    for i, char in enumerate(values_str):
        if char in ('"', "'") and (i == 0 or values_str[i-1] != '\\'):
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
            else:
                current_value.append(char)
        elif char == ',' and not in_quotes:
            # End of current value
            value = ''.join(current_value).strip()
            if value:
                values.append(value)
            current_value = []
        else:
            current_value.append(char)
    
    # Add the last value
    value = ''.join(current_value).strip()
    if value:
        values.append(value)
    
    return values


def _parse_single_condition(condition: str) -> Dict:
    """Parse a single condition like 'Status = 'Completed'' or 'Subject LIKE '%test%''."""
    condition = condition.strip()
    
    # Handle LIKE operator
    if " LIKE " in condition:
        field, value = condition.split(" LIKE ", 1)
        field = field.strip()
        value = value.strip().strip("'").strip('"')
        return {"type": "condition", "field": field, "operator": "LIKE", "value": value}
    
    # Handle CONTAINS operator
    elif " CONTAINS " in condition:
        field, value = condition.split(" CONTAINS ", 1)
        field = field.strip()
        value = value.strip().strip("'").strip('"')
        return {"type": "condition", "field": field, "operator": "CONTAINS", "value": value}
    
    # Handle IN operator
    elif " IN " in condition:
        field, values_part = condition.split(" IN ", 1)
        field = field.strip()
        # Extract values from parentheses
        values_part = values_part.strip()
        if values_part.startswith('(') and values_part.endswith(')'):
            values_str = values_part[1:-1]
            # Parse values respecting quoted strings (handles commas inside quotes)
            values = _parse_in_values(values_str)
            return {"type": "condition", "field": field, "operator": "IN", "value": values}
    
    # Handle comparison operators (=, >, <, >=, <=, !=)
    for op in [">=", "<=", "!=", "=", ">", "<"]:
        if f" {op} " in condition:
            field, value = condition.split(f" {op} ", 1)
            field = field.strip()
            value = value.strip().strip("'").strip('"')
            return {"type": "condition", "field": field, "operator": op, "value": value}
    
    # If no operator found, return as-is (might be malformed)
    return {"type": "condition", "field": condition, "operator": "=", "value": ""}


def _evaluate_condition_tree(tree: Dict, record: Dict) -> bool:
    """Evaluate a condition tree against a record."""
    if not tree:
        return True
    
    if tree["type"] == "and":
        return all(_evaluate_condition_tree(cond, record) for cond in tree["conditions"])
    
    elif tree["type"] == "or":
        return any(_evaluate_condition_tree(cond, record) for cond in tree["conditions"])
    
    elif tree["type"] == "condition":
        return _evaluate_single_condition(tree, record)
    
    return True


def _parse_date_literal(literal: str) -> Union[str, List[str], None]:
    """
    Parse Salesforce date literals into actual date values.
    
    Args:
        literal (str): Date literal like 'TODAY', 'NEXT_N_DAYS:7', 'LAST_N_DAYS:30', etc.
        
    Returns:
        Union[str, List[str], None]: Parsed date value(s) or None if not a date literal
    """
    literal = literal.strip().upper()
    today = datetime.now().date()
    
    # Handle simple date literals
    if literal == "TODAY":
        return today.isoformat()
    elif literal == "YESTERDAY":
        return (today - timedelta(days=1)).isoformat()
    elif literal == "TOMORROW":
        return (today + timedelta(days=1)).isoformat()
    elif literal == "THIS_WEEK":
        # Start of current week (Monday)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return [start_of_week.isoformat(), end_of_week.isoformat()]
    elif literal == "LAST_WEEK":
        # Start of last week (Monday)
        start_of_last_week = today - timedelta(days=today.weekday() + 7)
        end_of_last_week = start_of_last_week + timedelta(days=6)
        return [start_of_last_week.isoformat(), end_of_last_week.isoformat()]
    elif literal == "NEXT_WEEK":
        # Start of next week (Monday)
        start_of_next_week = today + timedelta(days=7 - today.weekday())
        end_of_next_week = start_of_next_week + timedelta(days=6)
        return [start_of_next_week.isoformat(), end_of_next_week.isoformat()]
    elif literal == "THIS_MONTH":
        # Start and end of current month
        start_of_month = today.replace(day=1)
        if today.month == 12:
            end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return [start_of_month.isoformat(), end_of_month.isoformat()]
    elif literal == "LAST_MONTH":
        # Start and end of last month
        if today.month == 1:
            start_of_last_month = today.replace(year=today.year - 1, month=12, day=1)
            end_of_last_month = today.replace(day=1) - timedelta(days=1)
        else:
            start_of_last_month = today.replace(month=today.month - 1, day=1)
            end_of_last_month = today.replace(day=1) - timedelta(days=1)
        return [start_of_last_month.isoformat(), end_of_last_month.isoformat()]
    elif literal == "NEXT_MONTH":
        # Start and end of next month
        if today.month == 12:
            start_of_next_month = today.replace(year=today.year + 1, month=1, day=1)
            end_of_next_month = today.replace(year=today.year + 1, month=2, day=1) - timedelta(days=1)
        else:
            start_of_next_month = today.replace(month=today.month + 1, day=1)
            if today.month == 11:
                end_of_next_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_of_next_month = today.replace(month=today.month + 2, day=1) - timedelta(days=1)
        return [start_of_next_month.isoformat(), end_of_next_month.isoformat()]
    
    # Handle N_DAYS literals
    elif ":" in literal:
        if literal.startswith("LAST_N_DAYS:"):
            try:
                n = int(literal.split(":")[1])
                start_date = today - timedelta(days=n)  # Include n days ago
                return [start_date.isoformat(), today.isoformat()]
            except (ValueError, IndexError):
                return None
        elif literal.startswith("NEXT_N_DAYS:"):
            try:
                n = int(literal.split(":")[1])
                end_date = today + timedelta(days=n)  # Include n days from today
                return [today.isoformat(), end_date.isoformat()]
            except (ValueError, IndexError):
                return None
        elif literal.startswith("N_DAYS_AGO:"):
            try:
                n = int(literal.split(":")[1])
                target_date = today - timedelta(days=n)
                return target_date.isoformat()
            except (ValueError, IndexError):
                return None
    
    return None


def _is_date_literal(value: str) -> bool:
    """Check if a value is a Salesforce date literal."""
    value = value.strip().upper()
    simple_literals = [
        "TODAY", "YESTERDAY", "TOMORROW", "THIS_WEEK", "LAST_WEEK", "NEXT_WEEK",
        "THIS_MONTH", "LAST_MONTH", "NEXT_MONTH"
    ]
    
    if value in simple_literals:
        return True
    
    # Check N_DAYS patterns
    n_days_patterns = ["LAST_N_DAYS:", "NEXT_N_DAYS:", "N_DAYS_AGO:"]
    return any(value.startswith(pattern) for pattern in n_days_patterns)


def _evaluate_date_condition(field_value: str, operator: str, literal_value: Union[str, List[str]]) -> bool:
    """
    Evaluate a date condition with date literals.
    
    Args:
        field_value (str): The field value from the record
        operator (str): The comparison operator
        literal_value (Union[str, List[str]]): The parsed date literal value(s)
        
    Returns:
        bool: True if condition matches, False otherwise
    """
    try:
        # Parse field value as date (handle various formats)
        if 'T' in field_value:
            # ISO datetime format
            field_date = datetime.fromisoformat(field_value.replace('Z', '+00:00')).date()
        else:
            # Date only format
            field_date = datetime.fromisoformat(field_value).date()
        
        if isinstance(literal_value, list):
            # Range comparison (for week/month literals)
            start_date = datetime.fromisoformat(literal_value[0]).date()
            end_date = datetime.fromisoformat(literal_value[1]).date()
            
            if operator == "=":
                return start_date <= field_date <= end_date
            elif operator == "!=":
                return not (start_date <= field_date <= end_date)
            elif operator == ">":
                return field_date > end_date
            elif operator == "<":
                return field_date < start_date
            elif operator == ">=":
                return field_date >= start_date
            elif operator == "<=":
                return field_date <= end_date
        else:
            # Single date comparison
            literal_date = datetime.fromisoformat(literal_value).date()
            
            if operator == "=":
                return field_date == literal_date
            elif operator == "!=":
                return field_date != literal_date
            elif operator == ">":
                return field_date > literal_date
            elif operator == "<":
                return field_date < literal_date
            elif operator == ">=":
                return field_date >= literal_date
            elif operator == "<=":
                return field_date <= literal_date
                
    except (ValueError, TypeError):
        # If date parsing fails, fall back to string comparison
        return False
    
    return False


def _evaluate_single_condition(condition: Dict, record: Dict) -> bool:
    """Evaluate a single condition against a record."""
    field = condition["field"]
    operator = condition["operator"]
    value = condition["value"]
    
    if field not in record:
        return False
    
    record_value = record[field]
    
    # Check if value is a date literal (for date fields)
    if isinstance(value, str) and _is_date_literal(value):
        parsed_literal = _parse_date_literal(value)
        if parsed_literal is not None:
            # Convert to string for date comparison
            return _evaluate_date_condition(str(record_value), operator, parsed_literal)
    
    # Handle string operators that require string conversion
    if operator in ["LIKE", "CONTAINS"]:
        record_value_str = str(record_value)
        if operator == "LIKE":
            # Convert SQL LIKE pattern to regex
            pattern = value.replace('%', '.*').replace('_', '.')
            return bool(re.search(pattern, record_value_str, re.IGNORECASE))
        elif operator == "CONTAINS":
            return value.lower() in record_value_str.lower()
    
    # For comparison operators, try to match types
    if operator in ["=", "!=", ">", "<", ">=", "<="]:
        # Try to match the type of the value to the record value
        try:
            # If value is a string representation of a boolean
            if isinstance(value, str) and value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            # If value is a string representation of a number
            elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
        except (ValueError, AttributeError):
            pass
        
        # Perform comparison
        try:
            if operator == "=":
                return record_value == value
            elif operator == "!=":
                return record_value != value
            elif operator == ">":
                return record_value > value
            elif operator == "<":
                return record_value < value
            elif operator == ">=":
                return record_value >= value
            elif operator == "<=":
                return record_value <= value
        except TypeError:
            # If comparison fails due to type mismatch, convert both to strings
            return False
    
    elif operator == "IN":
        # For IN operator, check if record value is in the list
        # Try to match types for each value in the list
        matched_values = []
        for v in value:
            try:
                if isinstance(v, str) and v.lower() in ['true', 'false']:
                    matched_values.append(v.lower() == 'true')
                elif isinstance(v, str) and v.replace('.', '').replace('-', '').isdigit():
                    if '.' in v:
                        matched_values.append(float(v))
                    else:
                        matched_values.append(int(v))
                else:
                    matched_values.append(v)
            except (ValueError, AttributeError):
                matched_values.append(v)
        
        return record_value in matched_values
    
    return False


@tool_spec(
    spec={
        'name': 'execute_soql_query',
        'description': """ Executes a SOQL-like query against the in-memory database.
        
        The query string is first URL-decoded. 
        The parser has specific behaviors and improved parsing logic as detailed below. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'q': {
                    'type': 'string',
                    'description': """ The SOQL-like query string. Examples:
                    - "SELECT Name, Location FROM Event WHERE Location = 'Boardroom' ORDER BY Name ASC OFFSET 0 LIMIT 5"
                    - "SELECT Id, Subject, Status FROM Task WHERE (Status = 'Completed' OR Status = 'Closed') AND Subject LIKE '%important%'"
                    - "SELECT Id, Subject, DueDate FROM Task WHERE DueDate = TODAY"
                    - "SELECT Id, Subject, DueDate FROM Task WHERE DueDate >= NEXT_N_DAYS:7" """
                }
            },
            'required': [
                'q'
            ]
        }
    }
)
def get(q: str) -> Dict[str, Any]:
    """
    Executes a SOQL-like query against the in-memory database.

    The query string is first URL-decoded. 
    The parser has specific behaviors and improved parsing logic as detailed below.

    Args:
        q (str): The SOQL-like query string. Examples:
                 - "SELECT Name, Location FROM Event WHERE Location = 'Boardroom' ORDER BY Name ASC OFFSET 0 LIMIT 5"
                 - "SELECT Id, Subject, Status FROM Task WHERE (Status = 'Completed' OR Status = 'Closed') AND Subject LIKE '%important%'"
                 - "SELECT Id, Subject, DueDate FROM Task WHERE DueDate = TODAY"
                 - "SELECT Id, Subject, DueDate FROM Task WHERE DueDate >= NEXT_N_DAYS:7"

    Returns:
        Dict[str, Any]: Query results with structure:
            - results (List[Dict[str, Any]]): List of matching records.

    Raises:
        TypeError: If the query is not a string.
        ValueError: If the query is fundamentally malformed (e.g., missing SELECT or FROM clause)
                    or if the object is not found in the database
                    or if the query fails for any other reason.

    Notes:
        Supported Clauses & Parsing Behaviors:
        --------------------------------------
        SELECT <field1[, field2...]>
            - Purpose: Specifies fields to retrieve.
            - Keyword 'SELECT': Case-insensitive.
            - Fields: Comma-separated if multiple. All specified fields are now reliably selected.
            The parser correctly identifies fields listed between SELECT and FROM.

        FROM <ObjectName>
            - Purpose: Specifies the object to query (e.g., "FROM Event").
            - Keyword 'FROM': MUST be UPPERCASE.

        WHERE <conditions>
            - Purpose: Filters records based on conditions.
            - Keywords 'WHERE', 'AND', 'OR': MUST be UPPERCASE.
            - Logical Operators: Supports AND, OR with proper precedence (AND has higher precedence than OR).
            - Parentheses: Supports grouping with parentheses for complex conditions.
            - Operators: '=', '!=', '>', '<', '>=', '<=', 'IN', 'LIKE', 'CONTAINS'.
            - String Literals: Must be enclosed in single or double quotes (e.g., "Name = 'Test Value'").
            - LIKE Patterns: Use '%' for wildcard matching (e.g., "Subject LIKE '%meeting%'").
            - IN Lists: Use parentheses for value lists (e.g., "Status IN ('Open', 'Closed')").
            - Parsing: The WHERE condition string is parsed to correctly end before other major clauses
            like 'ORDER BY', 'LIMIT', or 'OFFSET'. This prevents tokens from these clauses from being
            incorrectly included in the WHERE condition.

        ORDER BY <field> [ASC|DESC]
            - Purpose: Sorts the results.
            - Keywords 'ORDER BY', 'ASC', 'DESC': MUST be UPPERCASE. 'ASC' is default.
            - Behavior: Sorting by <field> works correctly if <field> is selected (i.e., present in the
            records after the SELECT phase). If the <field> to sort by is not present in the
            records being sorted (e.g., not selected, or does not exist on records), the sort key
            becomes an empty string for those items, potentially resulting in an unstable sort
            (often preserving the original retrieval order for those items relative to each other).

        OFFSET <number>
            - Purpose: Skips a specified number of records from the beginning of the result set *after sorting*.
            - Keyword 'OFFSET': MUST be UPPERCASE.
            - Interaction with LIMIT: OFFSET is applied to the result set first, then LIMIT is applied.
            The order of OFFSET and LIMIT keywords in the query string does not affect this execution sequence.
            The internal logic first applies OFFSET to the sorted list, then LIMIT to that offsetted list.

        LIMIT <number>
            - Purpose: Restricts the number of records returned *after sorting and offsetting*.
            - Keyword 'LIMIT': MUST be UPPERCASE.
            
        Date Literals:
            - Purpose: Dynamic date filtering without specifying exact dates.
            - Supported literals: TODAY, YESTERDAY, TOMORROW, THIS_WEEK, LAST_WEEK, NEXT_WEEK, 
              THIS_MONTH, LAST_MONTH, NEXT_MONTH, LAST_N_DAYS:n, NEXT_N_DAYS:n, N_DAYS_AGO:n
            - Usage: Can be used in WHERE clauses with date/datetime fields
            - Examples: "WHERE DueDate = TODAY", "WHERE CreatedDate >= LAST_N_DAYS:30"
            - Range literals (WEEK/MONTH) work with = operator to check if date falls within range
    """
    if not isinstance(q, str):
        raise TypeError("Argument 'q' must be a string.")

    try:
        # Decode URL-encoded query
        q = urllib.parse.unquote(q)
        parts = q.split()

        if parts[0].upper() != "SELECT":
            raise ValueError("Invalid SOQL query: Must start with SELECT")

        # Object to query (determine from_index first for robust field parsing)
        from_index = -1
        # Find FROM keyword considering it might not be in 'parts' if query is malformed before FROM
        temp_q_parts = q.split() # Use a fresh split of q to reliably find FROM's original position
        for i, part in enumerate(temp_q_parts):
            if part.upper() == "FROM":
                from_index = i # This index is relative to temp_q_parts
                break
        
        if from_index == -1 or from_index == 0: # from_index == 0 means SELECT is missing or FROM is first
             # Try to find FROM in the original 'parts' as a fallback if temp_q_parts logic is insufficient or query is very short
            if "FROM" in parts:
                from_index = parts.index("FROM")
            else:
                raise ValueError("Invalid SOQL query: Missing FROM clause or malformed structure")

        # Fields to select
        # Use 'parts' for field string construction as 'parts' is what's used for subsequent parsing
        # Ensure from_index used for slicing 'parts' is valid for 'parts' list length
        actual_from_index_in_parts = parts.index("FROM") if "FROM" in parts else -1
        if actual_from_index_in_parts <= 0 : # Must be at least after SELECT (parts[0])
            raise ValueError("Invalid SOQL query: FROM clause misplaced or missing")

        fields_string = " ".join(parts[1:actual_from_index_in_parts])
        fields = [field.strip() for field in fields_string.split(",") if field.strip()]

        # Object to query
        if actual_from_index_in_parts + 1 >= len(parts):
            raise ValueError("Invalid SOQL query: Missing object name after FROM")
        obj = parts[actual_from_index_in_parts + 1]

        # Initialize variables for conditions, limit, offset, and order_by
        where_index = -1
        limit = None
        offset = None
        order_by = None

        # Extract WHERE clause conditions
        condition_tree = None
        if "WHERE" in parts:
            where_index = parts.index("WHERE")
            # Determine the end of the WHERE clause
            end_where_index = len(parts)
            # Find the start of the next major clause to delimit WHERE
            for i in range(where_index + 1, len(parts)):
                # Check if the current part is a keyword that terminates a WHERE clause
                # ORDER BY is two words, so check parts[i] and parts[i+1]
                if parts[i].upper() == "ORDER" and i + 1 < len(parts) and parts[i+1].upper() == "BY":
                    end_where_index = i
                    break
                elif parts[i].upper() in ["LIMIT", "OFFSET"]:
                    end_where_index = i
                    break
            
            condition_string = " ".join(parts[where_index + 1 : end_where_index])
            condition_tree = _parse_where_clause(condition_string)

        # Extract LIMIT clause
        if "LIMIT" in parts:
            limit_index = parts.index("LIMIT")
            limit = int(parts[limit_index + 1])
            #parts = parts[:limit_index]  # Remove LIMIT part from the query

        # Extract OFFSET clause
        if "OFFSET" in parts:
            offset_index = parts.index("OFFSET")
            offset = int(parts[offset_index + 1])
            #parts = parts[:offset_index]  # Remove OFFSET part from the query

        # Extract ORDER BY clause
        if "ORDER BY" in q:
            order_by_index = q.index("ORDER BY")
            order_by = q[order_by_index + 9 :].strip()  # 9 is length of "ORDER BY "
            if "LIMIT" in order_by:
                order_by = order_by[: order_by.index("LIMIT")].strip()
            if "OFFSET" in order_by:
                order_by = order_by[: order_by.index("OFFSET")].strip()

        # Get the appropriate database collection
        if obj not in DB:
            raise ValueError(f"Object {obj} not found in database")

        # Apply conditions
        results = []
        for record in DB[obj].values():
            match = True
            if condition_tree:
                match = _evaluate_condition_tree(condition_tree, record)
            
            if match:
                # Select only requested fields
                filtered_record = {}
                for field in fields:
                    if field in record:
                        filtered_record[field] = record[field]
                results.append(filtered_record)

        # Apply ORDER BY
        if order_by:
            parts = order_by.split()
            field = parts[0].strip()
            # Default to ASC if direction not specified
            direction = parts[1].strip().upper() if len(parts) > 1 else 'ASC'
            results.sort(key=lambda x: x.get(field, ""), reverse=(direction == "DESC"))

        # Apply OFFSET and LIMIT
        if offset is not None:
            results = results[offset:]
        if limit is not None:
            results = results[:limit]

        return {"results": results}

    except Exception as e:
        raise ValueError(f"Error executing query: {str(e)}")

@tool_spec(
    spec={
        'name': 'parse_where_clause_conditions',
        'description': """ Parse the conditions in the WHERE clause.
        
        Handles '=', 'IN', 'LIKE', 'CONTAINS', '>', and '<'. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'conditions': {
                    'type': 'array',
                    'description': """ List of condition strings to parse. Example:
                    - "Subject = 'Meeting'"
                    - "IsAllDayEvent = true"
                    - "Location IN ('Boardroom', 'Conference Room')"
                    - "Description LIKE '%important%'"
                    - "Subject CONTAINS 'review'",
                    - "Priority < 'High'" """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'conditions'
            ]
        }
    }
)
def parse_conditions(conditions: List[str]) -> List[Tuple[str, str, str | List[str]]]:
    """
    Parse the conditions in the WHERE clause.
    Handles '=', 'IN', 'LIKE', 'CONTAINS', '>', and '<'.

    Args:
        conditions (List[str]): List of condition strings to parse. Example:
            - "Subject = 'Meeting'"
            - "IsAllDayEvent = true"
            - "Location IN ('Boardroom', 'Conference Room')"
            - "Description LIKE '%important%'"
            - "Subject CONTAINS 'review'",
            - "Priority < 'High'"

    Returns:
        List[Tuple[str, str, str | List[str]]]: List of tuples containing (condition_type, field, value) where:
            - condition_type (str): One of '=', 'IN', 'LIKE', 'CONTAINS'
            - field (str): The field name to check
            - value (str | List[str]): The value(s) to compare against

    Raises:
        InvalidConditionsError: If the conditions parameter is not a valid list of strings.
        UnsupportedOperatorError: If a condition uses an unsupported operator.
    """
    # Validate input using Pydantic model
    try:
        validated_conditions = ConditionsListModel(conditions).root
    except ValidationError as e:
        raise e
    except Exception as e:
        if "Input should be a valid list" in str(e) or "Conditions must be a list" in str(e):
            raise ValidationError.from_exception_data("ValidationError", [{"type": "list_type", "loc": (), "input": conditions}])
        raise e
    
    parsed_conditions: List[Tuple[str, str, str | List[str]]] = []
    for cond in validated_conditions:
        cond = cond.strip()

        # Handle equality condition (but not !=, >=, <=)
        if "=" in cond and "!=" not in cond and ">=" not in cond and "<=" not in cond:
            field, value = cond.split("=", 1)
            field = field.strip()
            value = value.strip().strip("'()\"")
            parsed_conditions.append(("=", field, value))

        # Handle CONTAINS condition (case-insensitive with word boundaries)
        elif re.search(r'\bCONTAINS\b', cond, re.IGNORECASE):
            field, value = re.split(r'\bCONTAINS\b', cond, 1, flags=re.IGNORECASE)
            field = field.strip()
            value = value.strip().strip("'()\"")
            parsed_conditions.append(("CONTAINS", field, value))

        # Handle IN condition (case-insensitive with word boundaries)
        elif re.search(r'\bIN\b', cond, re.IGNORECASE):
            field, values = re.split(r'\bIN\b', cond, 1, flags=re.IGNORECASE)
            field = field.strip()
            values = values.split(",")
            values = [v.strip().strip("'()\"") for v in values]
            parsed_conditions.append(("IN", field, values))

        # Handle LIKE condition (case-insensitive with word boundaries)
        elif re.search(r'\bLIKE\b', cond, re.IGNORECASE):
            field, value = re.split(r'\bLIKE\b', cond, 1, flags=re.IGNORECASE)
            field = field.strip()
            value = value.strip().strip("'()\"").replace("%", "")
            parsed_conditions.append(("LIKE", field, value))

        # Handle > condition
        elif ">" in cond:
            field, value = cond.split(">", 1)
            field = field.strip()
            value = value.strip().strip("'()\"")
            parsed_conditions.append((">", field, value))

        # Handle < condition
        elif "<" in cond:
            field, value = cond.split("<", 1)
            field = field.strip()
            value = value.strip().strip("'()\"")
            parsed_conditions.append(("<", field, value))

        else:
            # Raise UnsupportedOperatorError for unsupported operators or malformed conditions
            raise custom_errors.UnsupportedOperatorError("Condition must contain one of the supported operators: =, IN, LIKE, CONTAINS, >, <")

    return parsed_conditions
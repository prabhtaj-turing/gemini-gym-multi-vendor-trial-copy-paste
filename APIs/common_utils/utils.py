import os
import re
from copy import deepcopy
from jsonpath_ng.ext import parse
from jsonpath_ng.jsonpath import Fields, Index, Slice
from typing import Any, Union, List, Dict, Tuple, Set
from pydantic import validate_email
from .custom_errors import InvalidEmailError

from common_utils.terminal_filesystem_utils import find_binary_files

# Generic JSON-like type
JSONType = Union[Dict[Any, Any], List[Any], str, int, float, bool, None]

def discover_services() -> list[str]:
    """
    Discovers all available services by listing directories in the APIs folder.
    """
    services = []
    api_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    for entry in os.listdir(api_root_dir):
        if os.path.isdir(os.path.join(api_root_dir, entry)) and entry != "common_utils" and not entry.startswith("__"):
            services.append(entry)
    return sorted(services)

def get_minified_data(
    data: JSONType,
    blacklist_paths: List[str],
    in_place: bool = False,
) -> JSONType:
    """
    Remove all values referenced by JSONPath expressions in `blacklist_paths`.
    Supports both string and integer dict keys.
    """
    minified_data = data if in_place else deepcopy(data)

    # Collect list deletions separately (indices must be removed in reverse order)
    pending_list_deletions: Dict[int, Tuple[List[Any], Set[int]]] = {}

    def schedule_list_delete(parent_list: List[Any], idx: int) -> None:
        bucket = pending_list_deletions.setdefault(id(parent_list), (parent_list, set()))
        bucket[1].add(idx)

    def handle_hit(hit: Any) -> None:
        parent = hit.context.value
        path = hit.path

        # Dict field removal
        if isinstance(parent, dict) and isinstance(path, Fields):
            for field in path.fields:
                parent.pop(field, None)
            return

        # Dict int key removal (jsonpath-ng won’t hit this, so we need manual fallback)
        if isinstance(parent, dict) and isinstance(path, Index):
            if path.index in parent:  # treat index as dict key
                parent.pop(path.index, None)
                return

        # List index removal
        if isinstance(parent, list) and isinstance(path, Index):
            schedule_list_delete(parent, path.index)
            return

        # List slice removal
        if isinstance(parent, list) and isinstance(path, Slice):
            rng = range(*path.slice.indices(len(parent)))
            for i in rng:
                schedule_list_delete(parent, i)
            return

        # Fallback: identity-based deletion
        if isinstance(parent, dict):
            for k, v in list(parent.items()):
                if v is hit.value:
                    parent.pop(k, None)
                    break
        elif isinstance(parent, list):
            for i, v in enumerate(parent):
                if v is hit.value:
                    schedule_list_delete(parent, i)

    # Regex to detect dict int key paths like a[10], foo.bar[42]
    dict_int_key_pattern = re.compile(r"(.*)\[(\d+)\]$")

    for expr_str in blacklist_paths:
        m = dict_int_key_pattern.match(expr_str)
        if m:
            prefix, num_str = m.groups()
            dict_key = int(num_str)

            # Navigate manually to parent dict
            expr = parse(prefix) if prefix else parse("$")
            hits: List[Any] = list(expr.find(minified_data))
            for h in hits:
                parent = h.value
                if isinstance(parent, dict) and dict_key in parent:
                    parent.pop(dict_key, None)
            continue

        # Normal JSONPath handling
        expr = parse(expr_str)
        hits: List[Any] = list(expr.find(minified_data))
        for h in hits:
            handle_hit(h)

    # Perform list deletions (reverse order for safe index removal)
    for parent_list, indices in pending_list_deletions.values():
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(parent_list):
                del parent_list[idx]

    return minified_data

# ---------------------------
# Example usage
if __name__ == "__main__":
    data = {
        "a": {
            "b": [
                {"c": [{"qw": 1, "ok": 2}, {"qw": 3, "keep": 4}]},
                {"c": [{"qw": 5}]}
            ],
            10: "integer-key",
        },
        "arr": [10, 20, 30, 40, 50]
    }

    blacklist = [
        "a.b[*].c[*].qw",   # remove qw fields
        "arr[1:4]",         # remove arr indices 1..3 (20,30,40)
        "a[10]"             # remove dict entry with int key 10
    ]

    result = get_minified_data(data, blacklist)
    print(result)
    # -> {'a': {'b': [{'c': [{'ok': 2}, {'keep': 4}]}, {'c': [{}]}]}, 'arr': [10, 50]}

def validate_email_util(email: str, field_name: str) -> None:
    """Validates an email address.
    
    Args:
        email (str): The email address to validate.
        field_name (str): The name of the field being validated.
        
    Raises:
        InvalidEmailError: If the email address is invalid.
    """
    try:
        validate_email(email)
    except Exception:
        raise InvalidEmailError(f"Invalid email value '{email}' for field '{field_name}'")

def get_minified_state(DB) -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    blacklist = [
        # $.. means "match this field recursively at any depth in the JSON"
        "$..timestamps",  # remove all "metadata" blocks
        "$..last_modified"  # remove last_modified
        # "$..size_bytes",  # remove size_bytes
    ]

    file_system = DB.get("file_system", {})
    binary_files = find_binary_files(file_system)
    # get_minified_data expects JSONPath, not Python-style dotted keys.
    # Each file path must be quoted as a key in JSONPath, e.g. file_system["/content/workspace/binary_file.bin"].content_lines[1:]
    blacklist.extend([
        f'file_system["{file}"].content_lines[1:]' for file in binary_files
    ])
    minified_data = get_minified_data(DB, blacklist)
    return minified_data

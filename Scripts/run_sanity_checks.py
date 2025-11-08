"""
Usage:
    python Scripts/run_sanity_checks.py --checks <check1> <check2> ... [--report-file <path>] [--format <md|csv>]

Description:
    This script runs a series of sanity checks on the JSON schema files located in the 'Schemas/' directory.
    It can perform various checks and generate a report in markdown or CSV format.

Arguments:
    --checks (required): A space-separated list of checks to run.
                         Available checks are:
                         - only_alphanumeric_and_underscore_keys
                         - no_duplicate_required_fields
                         - no_duplicate_property_keys
                         - no_empty_descriptions
                         - valid_type_values
                         - schema_structure
                         - function_name_format

    --report-file (optional): The path to the output report file.
                              Defaults to 'sanity_report.md'.

    --format (optional): The format of the report.
                         Can be 'md' (markdown) or 'csv'.
                         Defaults to 'md'.

Example:
    python Scripts/run_sanity_checks.py --checks schema_structure no_empty_descriptions --format csv --report-file my_report.csv
"""
import json
import os
import sys
import argparse
import re
import csv

# --- Sanity Check Functions ---

def _get_functions_from_file(file_path):
    """A helper generator to load a JSON file and yield each function definition with a descriptive path."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    functions = data if isinstance(data, list) else [data]
    
    for i, func_def in enumerate(functions):
        func_name = func_def.get("name") if isinstance(func_def, dict) else None
        
        path_prefix = "root"
        if len(functions) > 1:
            if func_name and isinstance(func_name, str) and func_name.strip():
                path_prefix = f"function({func_name})"
            else:
                path_prefix = f"function_at_index[{i}]"
        
        yield func_def, path_prefix

def check_json_key_characters(schemas_dir="Schemas"):
    """
    Recursively checks all JSON files in the schemas_dir for keys containing
    characters other than alphanumerics and underscores.
    Returns a list of structured error dicts.
    """
    errors = []
    invalid_char_pattern = re.compile(r'[^a-zA-Z0-9_]')

    if not os.path.isdir(schemas_dir):
        return [{"file_path": schemas_dir, "path": "N/A", "issue": "Directory not found."}]

    def _check_keys_recursive(obj, file_path, path):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}"
                if invalid_char_pattern.search(key):
                    errors.append({
                        "file_path": file_path,
                        "path": current_path,
                        "issue": f"Key `\"{key}\"` contains invalid characters. Only alphanumeric characters and underscores are allowed."
                    })
                _check_keys_recursive(value, file_path, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _check_keys_recursive(item, file_path, f"{path}[{i}]")

    for filename in os.listdir(schemas_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(schemas_dir, filename)
            try:
                for func_def, path_prefix in _get_functions_from_file(file_path):
                    _check_keys_recursive(func_def, file_path, path_prefix)
            except json.JSONDecodeError:
                errors.append({"file_path": file_path, "path": "N/A", "issue": "Could not decode JSON."})
    return errors

def check_duplicate_required_fields(schemas_dir="Schemas"):
    """
    Recursively checks for duplicate values within any 'required' array in JSON files.
    Returns a list of structured error dicts.
    """
    errors = []
    if not os.path.isdir(schemas_dir):
        return [{"file_path": schemas_dir, "path": "N/A", "issue": "Directory not found."}]

    def _check_recursive(obj, file_path, path):
        if isinstance(obj, dict):
            if "required" in obj and isinstance(obj["required"], list):
                if len(obj["required"]) != len(set(obj["required"])):
                    seen = set()
                    dupes = {x for x in obj["required"] if x in seen or seen.add(x)}
                    errors.append({
                        "file_path": file_path,
                        "path": path,
                        "issue": f"`required` array has duplicates: {sorted(list(dupes))}"
                    })
            for key, value in obj.items():
                _check_recursive(value, file_path, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _check_recursive(item, file_path, f"{path}[{i}]")

    for filename in os.listdir(schemas_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(schemas_dir, filename)
            try:
                for func_def, path_prefix in _get_functions_from_file(file_path):
                    _check_recursive(func_def, file_path, path_prefix)
            except json.JSONDecodeError:
                errors.append({"file_path": file_path, "path": "N/A", "issue": "Could not decode JSON."})
    return errors

def check_duplicate_property_keys(schemas_dir="Schemas"):
    """
    Checks for duplicate keys within any JSON object in the files.
    This is stricter than standard JSON parsers, which may silently overwrite duplicates.
    Returns a list of structured error dicts.
    """
    errors = []
    if not os.path.isdir(schemas_dir):
        return [{"file_path": schemas_dir, "path": "N/A", "issue": "Directory not found."}]

    def _check_for_duplicates_hook(pairs):
        keys = [key for key, value in pairs]
        if len(keys) != len(set(keys)):
            seen = set()
            dupes = {x for x in keys if x in seen or seen.add(x)}
            raise ValueError(f"Duplicate keys found: {sorted(list(dupes))}")
        return dict(pairs)

    for filename in os.listdir(schemas_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(schemas_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    json.load(f, object_pairs_hook=_check_for_duplicates_hook)
                except ValueError as e:
                    if "Duplicate keys found" in str(e):
                        errors.append({"file_path": file_path, "path": "N/A", "issue": str(e)})
                    else:
                        raise # Reraise other ValueErrors
                except json.JSONDecodeError:
                    errors.append({"file_path": file_path, "path": "N/A", "issue": "Could not decode JSON."})
    return errors

def check_empty_descriptions(schemas_dir="Schemas"):
    """
    Recursively checks for 'description' fields that are empty or just whitespace.
    Returns a list of structured error dicts.
    """
    errors = []
    if not os.path.isdir(schemas_dir):
        return [{"file_path": schemas_dir, "path": "N/A", "issue": "Directory not found."}]

    def _check_recursive(obj, file_path, path):
        if isinstance(obj, dict):
            if "description" in obj and isinstance(obj["description"], str):
                if not obj["description"].strip():
                    errors.append({
                        "file_path": file_path,
                        "path": path,
                        "issue": "`description` is empty or contains only whitespace."
                    })
            for key, value in obj.items():
                _check_recursive(value, file_path, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _check_recursive(item, file_path, f"{path}[{i}]")

    for filename in os.listdir(schemas_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(schemas_dir, filename)
            try:
                for func_def, path_prefix in _get_functions_from_file(file_path):
                    _check_recursive(func_def, file_path, path_prefix)
            except json.JSONDecodeError:
                errors.append({"file_path": file_path, "path": "N/A", "issue": "Could not decode JSON."})
    return errors

def check_schema_structure(schemas_dir="Schemas"):
    """
    Recursively validates the schema against a defined meta-structure.
    Ensures required keys are present, value types are correct, and descriptions are not empty.
    Returns a list of structured error dicts.
    """
    errors = []
    if not os.path.isdir(schemas_dir):
        return [{"file_path": schemas_dir, "path": "N/A", "issue": "Directory not found."}]

    def _validate_node(node, path, file_path, is_exempt_from_description=False):
        if not isinstance(node, dict):
            errors.append({"file_path": file_path, "path": path, "issue": f"Expected an object/dictionary, but got {type(node).__name__}."})
            return

        if not is_exempt_from_description:
            if "description" not in node or not isinstance(node.get("description"), str):
                errors.append({"file_path": file_path, "path": path, "issue": "Node must have a 'description' key."})

        if "type" not in node or not isinstance(node.get("type"), str):
            errors.append({"file_path": file_path, "path": path, "issue": "Node must have a 'type' key."})
            return

        node_type = node.get("type")

        if node_type == "object":
            if "properties" not in node or not isinstance(node.get("properties"), dict):
                errors.append({"file_path": file_path, "path": path, "issue": "Node with type 'object' must have a 'properties' object."})
            else:
                for key, value in node["properties"].items():
                    _validate_node(value, f"{path}.properties.{key}", file_path)

            if "required" not in node or not isinstance(node.get("required"), list):
                errors.append({"file_path": file_path, "path": path, "issue": f"'required' key must be a list, but got {type(node.get('required')).__name__}."})

            if "items" in node:
                errors.append({"file_path": file_path, "path": path, "issue": "Node with type 'object' must not have an 'items' key."})

        elif node_type == "array":
            if "items" not in node or not isinstance(node.get("items"), dict):
                errors.append({"file_path": file_path, "path": path, "issue": "Node with type 'array' must have an 'items' object."})
            else:
                _validate_node(node["items"], f"{path}.items", file_path, is_exempt_from_description=True)

            if "properties" in node:
                errors.append({"file_path": file_path, "path": path, "issue": "Node with type 'array' must not have a 'properties' key."})
        
        else: # Primitives
            if "properties" in node:
                errors.append({"file_path": file_path, "path": path, "issue": f"Node with primitive type '{node_type}' must not have a 'properties' key."})
            if "items" in node:
                errors.append({"file_path": file_path, "path": path, "issue": f"Node with primitive type '{node_type}' must not have an 'items' key."})

    for filename in os.listdir(schemas_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(schemas_dir, filename)
            try:
                for func_def, path_prefix in _get_functions_from_file(file_path):
                    if not isinstance(func_def, dict):
                        errors.append({"file_path": file_path, "path": path_prefix, "issue": "Top-level element is not an object."})
                        continue

                    if "name" not in func_def or not isinstance(func_def.get("name"), str) or not func_def.get("name").strip():
                        errors.append({"file_path": file_path, "path": path_prefix, "issue": "Root must have a non-empty 'name' string."})
                    
                    if "description" not in func_def or not isinstance(func_def.get("description"), str) or not func_def.get("description").strip():
                        errors.append({"file_path": file_path, "path": path_prefix, "issue": "Root must have a non-empty 'description' string."})

                    if "parameters" not in func_def or not isinstance(func_def.get("parameters"), dict):
                        errors.append({"file_path": file_path, "path": path_prefix, "issue": "Root must have a 'parameters' object."})
                    else:
                        _validate_node(func_def["parameters"], f"{path_prefix}.parameters", file_path, is_exempt_from_description=True)

            except json.JSONDecodeError:
                errors.append({"file_path": file_path, "path": "N/A", "issue": "Could not decode JSON."})
    return errors


def check_valid_type_values(schemas_dir="Schemas"):
    """
    Recursively checks that the 'type' key only contains allowed JSON schema type values.
    Returns a list of structured error dicts.
    """
    errors = []
    VALID_TYPES = {"string", "integer", "number", "boolean", "array", "object", "null"}
    if not os.path.isdir(schemas_dir):
        return [{"file_path": schemas_dir, "path": "N/A", "issue": "Directory not found."}]

    def _check_recursive(obj, file_path, path):
        if isinstance(obj, dict):
            if "type" in obj and isinstance(obj["type"], str):
                if obj["type"] not in VALID_TYPES:
                    errors.append({
                        "file_path": file_path,
                        "path": path,
                        "issue": f"Invalid value for `type`: '{obj['type']}'. Must be one of {sorted(list(VALID_TYPES))}."
                    })
            for key, value in obj.items():
                _check_recursive(value, file_path, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _check_recursive(item, file_path, f"{path}[{i}]")

    for filename in os.listdir(schemas_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(schemas_dir, filename)
            try:
                for func_def, path_prefix in _get_functions_from_file(file_path):
                    _check_recursive(func_def, file_path, path_prefix)
            except json.JSONDecodeError:
                errors.append({"file_path": file_path, "path": "N/A", "issue": "Could not decode JSON."})
    return errors

def check_function_name_format(schemas_dir="Schemas"):
    """
    Checks that the top-level 'name' of each function is a non-empty alphanumeric string with underscores.
    Returns a list of structured error dicts.
    """
    errors = []
    # This regex matches strings that contain ONLY alphanumeric chars and underscores.
    valid_name_pattern = re.compile(r'^[a-zA-Z0-9_]+$')
    if not os.path.isdir(schemas_dir):
        return [{"file_path": schemas_dir, "path": "N/A", "issue": "Directory not found."}]

    for filename in os.listdir(schemas_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(schemas_dir, filename)
            try:
                for func_def, path_prefix in _get_functions_from_file(file_path):
                    func_name = func_def.get("name")
                    if not func_name or not isinstance(func_name, str) or not func_name.strip():
                        errors.append({
                            "file_path": file_path,
                            "path": path_prefix,
                            "issue": "Function 'name' is missing, empty, or not a string."
                        })
                    elif not valid_name_pattern.match(func_name):
                        errors.append({
                            "file_path": file_path,
                            "path": path_prefix,
                            "issue": f"Function name '{func_name}' contains invalid characters. Only alphanumeric characters and underscores are allowed."
                        })
            except json.JSONDecodeError:
                errors.append({"file_path": file_path, "path": "N/A", "issue": "Could not decode JSON."})
    return errors


# --- Runner ---

AVAILABLE_CHECKS = {
    "only_alphanumeric_and_underscore_keys": check_json_key_characters,
    "no_duplicate_required_fields": check_duplicate_required_fields,
    "no_duplicate_property_keys": check_duplicate_property_keys,
    "no_empty_descriptions": check_empty_descriptions,
    "valid_type_values": check_valid_type_values,
    "schema_structure": check_schema_structure,
    "function_name_format": check_function_name_format,
}

def main():
    parser = argparse.ArgumentParser(description="Run sanity checks on generated schemas.")
    parser.add_argument(
        "--checks",
        nargs="+",
        required=True,
        help=f"Space-separated list of checks to run. Available: {', '.join(AVAILABLE_CHECKS.keys())}",
    )
    parser.add_argument(
        "--report-file",
        default="sanity_report.md",
        help="Path to write the output report file."
    )
    parser.add_argument(
        "--format",
        default="md",
        choices=["md", "csv"],
        help="Format for the output report. Default: md"
    )
    args = parser.parse_args()

    all_errors = []
    errors_per_check = {}

    for check_name in args.checks:
        check_func = AVAILABLE_CHECKS.get(check_name)
        if not check_func:
            error_msg = f"Unknown check: '{check_name}'"
            print(error_msg, file=sys.stderr)
            all_errors.append({"file_path": "N/A", "path": "N/A", "issue": error_msg})
            continue

        try:
            errors = check_func()
            if errors:
                errors_per_check[check_name] = errors
                all_errors.extend(errors)
        except Exception as e:
            error_msg = f"Exception during check '{check_name}': {e}"
            print(error_msg, file=sys.stderr)
            all_errors.append({"file_path": "N/A", "path": check_name, "issue": error_msg})

    if args.format == "csv":
        with open(args.report_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["File name", "Path", "Issue"])
            sorted_errors = sorted(all_errors, key=lambda x: (x['file_path'], x['path']))
            for error in sorted_errors:
                writer.writerow([error['file_path'], error['path'], error['issue']])
        print(f"CSV report written to {args.report_file}")
    else: # md format
        report_lines = []
        passed_checks = []
        failed_checks = []

        for check_name in sorted(args.checks):
            if check_name in errors_per_check:
                failed_checks.append(check_name)
            else:
                passed_checks.append(check_name)

        summary = f"**Sanity Check Summary:** {len(passed_checks)} passed, {len(failed_checks)} failed."
        report_lines.append(summary)

        if passed_checks:
            report_lines.append("\n--- ✅ Passed Checks ---")
            for check_name in passed_checks:
                report_lines.append(f"- ✅ `{check_name}`")

        if failed_checks:
            report_lines.append("\n--- ❌ Failed Checks ---")
            for check_name in failed_checks:
                report_lines.append(f"\n**❌ {check_name}**")
                sorted_errors = sorted(errors_per_check[check_name], key=lambda x: (x['file_path'], x['path']))
                for err in sorted_errors:
                    path_str = f"at `{err['path']}`" if err['path'] != "N/A" else ""
                    report_lines.append(f"  - In `{err['file_path']}` {path_str}: {err['issue']}")
        
        final_report = "\n".join(report_lines)
        with open(args.report_file, 'w', encoding='utf-8') as f:
            f.write(final_report)
        print(f"Markdown report written to {args.report_file}")

    if all_errors:
        sys.exit(1)

if __name__ == "__main__":
    main()

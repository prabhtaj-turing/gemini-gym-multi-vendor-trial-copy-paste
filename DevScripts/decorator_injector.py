import os
import sys
import argparse
from collections import defaultdict

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from DevScripts.extract_fcspecs import load_fcspecs
from DevScripts.generate_decorator import format_fcspec_to_decorator
from DevScripts.locate_tool_functions import locate_tool_function
from DevScripts.extract_function_maps import extract_function_maps

def inject_decorators(dry_run=False, overwrite=True, service_filter=None):
    """
    Finds all tool functions, generates their @tool_spec decorators,
    and injects the decorators into the source files.
    
    Args:
        dry_run: If True, print changes without modifying files
        overwrite: If True, overwrite existing @tool_spec decorators
        service_filter: If provided, only process this specific service
    """
    apis_dir = os.path.abspath(os.path.join(project_root, 'APIs'))
    schemas_dir = os.path.abspath(os.path.join(project_root, 'Schemas'))
    
    print("Loading all tool specs and function maps...")
    all_specs = load_fcspecs(schemas_dir)
    all_function_maps = extract_function_maps(apis_dir)
    print("Load complete.")
    
    # Filter services if requested
    if service_filter:
        if service_filter not in all_function_maps:
            print(f"ERROR: Service '{service_filter}' not found in function maps.")
            return
        all_function_maps = {service_filter: all_function_maps[service_filter]}
        print(f"Filtering to service: {service_filter}")

    # Step 1: Gather all required injections, grouped by file path.
    tasks = defaultdict(list)
    for service, function_map in all_function_maps.items():
        for tool_name in function_map.keys():
            location_info = locate_tool_function(apis_dir, service, tool_name)
            
            if "error" in location_info:
                continue

            if location_info.get("has_decorator") and not overwrite:
                print(f"INFO: Decorator already exists for '{service}.{tool_name}'. Skipping.")
                continue

            if service not in all_specs or tool_name not in all_specs[service]:
                print(f"WARNING: Spec not found for '{service}.{tool_name}'. Skipping.")
                continue
                
            spec = all_specs[service][tool_name]
            decorator_code = format_fcspec_to_decorator(spec).replace('\n', '\n')
            
            task_info = {
                "line": location_info['line'],
                "decorator_code": decorator_code,
                "tool_name": tool_name,
                "has_existing_decorator": location_info.get("has_decorator", False)
            }
            
            # If we have existing decorator info, add it for removal
            if location_info.get("tool_spec_info"):
                task_info["tool_spec_info"] = location_info["tool_spec_info"]
                
            tasks[location_info['file_path']].append(task_info)

    print(f"\nFound {sum(len(v) for v in tasks.values())} functions to process in {len(tasks)} files.")
    
    # Step 2: Process each file that needs modification.
    for file_path, injections in tasks.items():
        print(f"\n--- Processing: {file_path} ---")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except IOError as e:
            print(f"  ERROR: Could not read file. Skipping. Reason: {e}")
            continue

        # Check if the required import already exists.
        import_str = "from common_utils.tool_spec_decorator import tool_spec\n"
        import_present = any(line.strip().replace('"', "'") == "from common_utils.tool_spec_decorator import tool_spec" for line in lines)
        import_insert_index = 0

        if import_present:
            print("  INFO: tool_spec import already present.")
        else:
            # Determine the correct insertion point for the import.
            # It must appear after the module header (shebang, encoding),
            # the top-level docstring (if present), and after any
            # `from __future__ import ...` lines.
            def find_import_insertion_index(file_lines):
                idx = 0
                total = len(file_lines)

                # Shebang line
                if idx < total and file_lines[idx].startswith('#!'):
                    idx += 1

                # Encoding declaration can be in the first or second line
                def is_encoding_declaration(s):
                    return 'coding:' in s or 'coding=' in s

                if idx < total and is_encoding_declaration(file_lines[idx]):
                    idx += 1
                elif idx == 1 and idx < total and is_encoding_declaration(file_lines[idx]):
                    idx += 1

                # Top-level module docstring
                if idx < total:
                    stripped = file_lines[idx].lstrip()
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        delim = stripped[:3]
                        # Single-line docstring
                        if stripped.count(delim) >= 2:
                            idx += 1
                        else:
                            idx += 1
                            while idx < total and delim not in file_lines[idx]:
                                idx += 1
                            if idx < total:
                                idx += 1  # move past closing delimiter line

                # Blank lines after docstring/header
                while idx < total and file_lines[idx].strip() == '':
                    idx += 1

                # Any contiguous `from __future__ import ...` lines
                while idx < total and file_lines[idx].lstrip().startswith('from __future__ import'):
                    idx += 1

                return idx

            import_insert_index = find_import_insertion_index(lines)
        
        # Track line offsets for removal operations
        line_offset = 0
        
        # IMPORTANT: Sort injections by line number in reverse order.
        injections.sort(key=lambda x: x['line'], reverse=True)
        
        # Apply the injections (in reverse order).
        for injection in injections:
            tool_name = injection['tool_name']
            
            # If there's an existing decorator to remove
            if injection.get('has_existing_decorator') and injection.get('tool_spec_info'):
                spec_info = injection['tool_spec_info']
                start_line = spec_info['start_line'] - 1  # Convert to 0-based
                end_line = spec_info['end_line']  # Inclusive end line
                
                # Remove the old decorator lines
                del lines[start_line:end_line]
                lines_removed = end_line - start_line
                
                print(f"  - Removed existing @tool_spec decorator for '{tool_name}' (lines {spec_info['start_line']}-{spec_info['end_line']}).")
                
                # Adjust the insertion line based on removed lines
                adjusted_line = injection['line'] - lines_removed - 1
            else:
                adjusted_line = injection['line'] - 1
            
            # Insert the new decorator
            lines.insert(adjusted_line, injection['decorator_code'] + '\n')
            action = "Replaced" if injection.get('has_existing_decorator') else "Added"
            print(f"  - {action} decorator for '{tool_name}' at line {adjusted_line + 1}.")

        # Add the import statement if it's missing.
        if not import_present:
            lines.insert(import_insert_index, import_str)
            print(f"  - Prepared tool_spec import at line {import_insert_index + 1} (after headers/future imports).")
            
        # Write the changes back to the file if not in dry-run mode.
        if not dry_run:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print("  SUCCESS: Wrote changes to file.")
            except IOError as e:
                print(f"  ERROR: Could not write to file. Reason: {e}")
        else:
            print("  DRY RUN: Would have written changes to file.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Injects @tool_spec decorators into API function files.")
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Print the actions that would be taken without modifying any files."
    )
    parser.add_argument(
        '--no-overwrite',
        action='store_true',
        help="Skip functions that already have @tool_spec decorators instead of overwriting them."
    )
    parser.add_argument(
        '--service', '-s',
        type=str,
        help="Process only the specified service (e.g., 'zendesk')."
    )
    args = parser.parse_args()

    inject_decorators(dry_run=args.dry_run, overwrite=not args.no_overwrite, service_filter=args.service)
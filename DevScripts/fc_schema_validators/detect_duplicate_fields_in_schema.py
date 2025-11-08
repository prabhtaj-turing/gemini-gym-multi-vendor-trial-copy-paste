import os
import json
import csv
from collections import Counter

def find_duplicate_required_fields(schema, path="root", root_names=None):
    """
    Recursively traverse the schema, and for every object with a 'required' array,
    find duplicates in that array. Also, for every 'anyOf' array, find duplicate
    sub-schemas (by their dict representation). Returns two lists:
      - required_dups: (path, duplicates, full_required_list, name, root_index, root_name)
      - anyof_dups: (path, duplicate_indices, duplicate_items, root_index, root_name)
    """
    required_dups = []
    anyof_dups = []
    # Determine root[n] context
    root_index = None
    root_name = None
    if path.startswith("root[") and path.count("]") == 1:
        try:
            idx = int(path[len("root["):path.index("]")])
            root_index = idx
            if root_names and 0 <= idx < len(root_names):
                root_name = root_names[idx]
        except Exception:
            pass
    if isinstance(schema, dict):
        # Check for duplicate required fields
        if schema.get("type") == "object" and "required" in schema and isinstance(schema["required"], list):
            required_list = schema["required"]
            counter = Counter(required_list)
            duplicates = [item for item, count in counter.items() if count > 1]
            name = schema.get("name")
            if duplicates:
                required_dups.append((path, duplicates, required_list, name, root_index, root_name))
        # Check for duplicate anyOf entries (by dict representation)
        if "anyOf" in schema and isinstance(schema["anyOf"], list):
            seen = {}
            dups = []
            for idx, item in enumerate(schema["anyOf"]):
                # Use json.dumps for canonicalization (sort_keys for stable comparison)
                try:
                    key = json.dumps(item, sort_keys=True)
                except Exception:
                    key = str(item)
                if key in seen:
                    dups.append(idx)
                else:
                    seen[key] = idx
            if dups:
                # Collect the duplicate items for reporting
                duplicate_items = [schema["anyOf"][i] for i in dups]
                anyof_dups.append((f"{path}.anyOf", dups, duplicate_items, root_index, root_name))
        # Recurse into all dict values
        for k, v in schema.items():
            child_path = f"{path}.{k}"
            # Don't double-process anyOf here (already handled above)
            if k == "anyOf" and isinstance(v, list):
                for idx, anyof_item in enumerate(v):
                    anyof_path = f"{child_path}[{idx}]"
                    req, anyof = find_duplicate_required_fields(anyof_item, anyof_path, root_names)
                    required_dups.extend(req)
                    anyof_dups.extend(anyof)
            else:
                req, anyof = find_duplicate_required_fields(v, child_path, root_names)
                required_dups.extend(req)
                anyof_dups.extend(anyof)
    elif isinstance(schema, list):
        for idx, item in enumerate(schema):
            child_path = f"{path}[{idx}]"
            # If this is the root array, pass root_names (list of names at root)
            if path == "root":
                # Build root_names if not already provided
                if root_names is None:
                    # Try to get names for all items at root
                    names = []
                    for obj in schema:
                        if isinstance(obj, dict):
                            names.append(obj.get("name"))
                        else:
                            names.append(None)
                    req, anyof = find_duplicate_required_fields(item, child_path, names)
                    required_dups.extend(req)
                    anyof_dups.extend(anyof)
                else:
                    req, anyof = find_duplicate_required_fields(item, child_path, root_names)
                    required_dups.extend(req)
                    anyof_dups.extend(anyof)
            else:
                req, anyof = find_duplicate_required_fields(item, child_path, root_names)
                required_dups.extend(req)
                anyof_dups.extend(anyof)
    return required_dups, anyof_dups

def main():
    schemas_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Schemas")
    required_report = []
    anyof_report = []
    # Rows for CSV export
    required_rows = []  # schema_file, path, duplicates_json, full_required_json, name, root_index, root_name
    anyof_rows = []     # schema_file, path, duplicate_indices_json, duplicate_items_json, root_index, root_name
    for filename in os.listdir(schemas_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(schemas_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                required_report.append(f"### {filename}\n- Error loading JSON: {e}\n")
                continue
            # If the root is a list, build root_names for root[n]
            root_names = None
            if isinstance(data, list):
                root_names = []
                for obj in data:
                    if isinstance(obj, dict):
                        root_names.append(obj.get("name"))
                    else:
                        root_names.append(None)
            required_dups, anyof_dups = find_duplicate_required_fields(data, path="root", root_names=root_names)
            if required_dups:
                required_report.append(f"## `{filename}`")
                for path, dups, full_required, name, root_index, root_name in required_dups:
                    root_name_line = ""
                    if root_index is not None and root_name is not None:
                        root_name_line = f"    - root[{root_index}].name: `{root_name}`\n"
                    name_line = f"    - name: `{name}`\n" if name is not None else ""
                    required_report.append(
                        f"- **Path:** `{path}`\n"
                        f"    - Duplicate(s): `{dups}`\n"
                        f"    - Full `required` array: `{full_required}`\n"
                        f"{name_line}"
                        f"{root_name_line}"
                    )
                    # CSV row for duplicate required fields
                    required_rows.append({
                        "schema_file": filename,
                        "path": path,
                        "duplicates": json.dumps(dups, ensure_ascii=False),
                        "full_required": json.dumps(full_required, ensure_ascii=False),
                        "name": name if name is not None else "",
                        "root_index": root_index if root_index is not None else "",
                        "root_name": root_name if root_name is not None else "",
                    })
            if anyof_dups:
                anyof_report.append(f"## `{filename}`")
                for path, dups, duplicate_items, root_index, root_name in anyof_dups:
                    root_name_line = ""
                    if root_index is not None and root_name is not None:
                        root_name_line = f"    - root[{root_index}].name: `{root_name}`\n"
                    anyof_report.append(
                        f"- **Path:** `{path}`\n"
                        f"    - Duplicate indices: `{dups}`\n"
                        f"    - Duplicate items: `{[json.dumps(item, ensure_ascii=False) for item in duplicate_items]}`\n"
                        f"{root_name_line}"
                    )
                    # CSV row for duplicate anyOf entries
                    anyof_rows.append({
                        "schema_file": filename,
                        "path": path,
                        "duplicate_indices": json.dumps(dups, ensure_ascii=False),
                        "duplicate_items": json.dumps(duplicate_items, ensure_ascii=False),
                        "root_index": root_index if root_index is not None else "",
                        "root_name": root_name if root_name is not None else "",
                    })
    # Write CSV files
    output_dir = os.path.join(os.path.dirname(__file__), "..", "analysis_output")
    os.makedirs(output_dir, exist_ok=True)
    required_csv_path = os.path.join(output_dir, "duplicate_required_fields.csv")
    anyof_csv_path = os.path.join(output_dir, "duplicate_anyof_entries.csv")
    with open(required_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "schema_file",
                "path",
                "duplicates",
                "full_required",
                "name",
                "root_index",
                "root_name",
            ],
        )
        writer.writeheader()
        for row in required_rows:
            writer.writerow(row)
    with open(anyof_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "schema_file",
                "path",
                "duplicate_indices",
                "duplicate_items",
                "root_index",
                "root_name",
            ],
        )
        writer.writeheader()
        for row in anyof_rows:
            writer.writerow(row)
    if not required_report:
        print("# Duplicate `required` fields report\n\nNo duplicates found in any schema.")
    else:
        print("# Duplicate `required` fields report\n")
        print("\n".join(required_report))
    print("\n\n")
    if not anyof_report:
        print("# Duplicate `anyOf` entries report\n\nNo duplicates found in any schema.")
    else:
        print("# Duplicate `anyOf` entries report\n")
        print("\n".join(anyof_report))

if __name__ == "__main__":
    main()

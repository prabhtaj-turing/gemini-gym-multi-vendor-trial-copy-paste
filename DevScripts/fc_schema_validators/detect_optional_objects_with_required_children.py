import os
import json
import csv
from typing import Any, Dict, List, Tuple, Optional


def _is_object_like(schema: Any) -> bool:
    """
    Determine if a schema can represent an object at the current level.
    We consider it object-like if:
      - type == "object"
      - or it has a "properties" key (JSON Schema object shortcut)
      - or it has a top-level "required" array (valid only for objects)
      - or it uses anyOf/oneOf/allOf with at least one object-like branch
    """
    if not isinstance(schema, dict):
        return False
    if schema.get("type") == "object":
        return True
    if "properties" in schema and isinstance(schema["properties"], dict):
        return True
    if isinstance(schema.get("required"), list):
        return True
    for key in ("anyOf", "oneOf", "allOf"):
        branches = schema.get(key)
        if isinstance(branches, list):
            for item in branches:
                if _is_object_like(item):
                    return True
    return False


def _top_level_required_fields(schema: Any) -> List[str]:
    """
    Return the list of required fields at the CURRENT schema level if it is object-like.
    For combinators (anyOf/oneOf/allOf), collect required fields from any object-like branch.
    """
    if not isinstance(schema, dict):
        return []

    # Direct object case
    required_fields: List[str] = []
    if _is_object_like(schema):
        if isinstance(schema.get("required"), list):
            # Only include strings
            required_fields.extend([x for x in schema["required"] if isinstance(x, str)])

    # Combinators: union of top-level requireds from object-like branches
    for key in ("anyOf", "oneOf", "allOf"):
        branches = schema.get(key)
        if isinstance(branches, list):
            for item in branches:
                if _is_object_like(item) and isinstance(item.get("required"), list):
                    required_fields.extend([x for x in item["required"] if isinstance(x, str)])

    # Deduplicate while preserving order
    seen = set()
    deduped: List[str] = []
    for r in required_fields:
        if r not in seen:
            seen.add(r)
            deduped.append(r)
    return deduped


def find_optional_object_fields_with_required_children(
    schema: Any,
    path: str = "root",
    root_names: Optional[List[Optional[str]]] = None,
) -> List[Tuple[str, str, List[str], Optional[str], Optional[int], Optional[str]]]:
    """
    Traverse the schema and find properties where:
      - the property is optional at its parent (not listed in parent's required[]), and
      - the property's schema is object-like and declares required subfields (top-level).

    Returns a list of tuples:
      (property_path, property_name, child_required_fields, parent_name, root_index, root_name)
    """
    findings: List[Tuple[str, str, List[str], Optional[str], Optional[int], Optional[str]]] = []

    # Determine root[n] context for this path
    root_index: Optional[int] = None
    root_name: Optional[str] = None
    if path.startswith("root[") and path.count("]") == 1:
        try:
            idx = int(path[len("root["): path.index("]")])
            root_index = idx
            if root_names and 0 <= idx < len(root_names):
                root_name = root_names[idx]
        except Exception:
            pass

    if isinstance(schema, dict):
        # If current node is an object with properties, inspect children
        properties = schema.get("properties")
        if isinstance(properties, dict):
            parent_required = schema.get("required")
            parent_required_set = set(parent_required) if isinstance(parent_required, list) else set()
            parent_name = schema.get("name")

            for prop_name, prop_schema in properties.items():
                # Optional at parent?
                if prop_name not in parent_required_set:
                    if _is_object_like(prop_schema):
                        child_required = _top_level_required_fields(prop_schema)
                        if child_required:
                            prop_path = f"{path}.properties.{prop_name}"
                            findings.append(
                                (prop_path, prop_name, child_required, parent_name, root_index, root_name)
                            )

        # Recurse into dict values
        for k, v in schema.items():
            child_path = f"{path}.{k}"
            # Avoid infinite recursion safeguards aren't needed here as JSON is acyclic
            findings.extend(
                find_optional_object_fields_with_required_children(v, child_path, root_names)
            )

    elif isinstance(schema, list):
        for idx, item in enumerate(schema):
            child_path = f"{path}[{idx}]"
            if path == "root":
                # Build root_names once when visiting the root array
                if root_names is None:
                    names: List[Optional[str]] = []
                    for obj in schema:
                        if isinstance(obj, dict):
                            names.append(obj.get("name"))
                        else:
                            names.append(None)
                    findings.extend(
                        find_optional_object_fields_with_required_children(item, child_path, names)
                    )
                else:
                    findings.extend(
                        find_optional_object_fields_with_required_children(item, child_path, root_names)
                    )
            else:
                findings.extend(
                    find_optional_object_fields_with_required_children(item, child_path, root_names)
                )

    return findings


def main() -> None:
    schemas_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Schemas")
    report_lines: List[str] = []
    csv_rows: List[Dict[str, Any]] = []

    for filename in os.listdir(schemas_dir):
        if not filename.endswith(".json"):
            continue
        file_path = os.path.join(schemas_dir, filename)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            report_lines.append(f"## `{filename}`\n- Error loading JSON: {e}\n")
            continue

        # Pre-compute root names if root is a list
        root_names: Optional[List[Optional[str]]] = None
        if isinstance(data, list):
            root_names = []
            for obj in data:
                if isinstance(obj, dict):
                    root_names.append(obj.get("name"))
                else:
                    root_names.append(None)

        findings = find_optional_object_fields_with_required_children(data, path="root", root_names=root_names)
        if findings:
            report_lines.append(f"## `{filename}`")
            for prop_path, prop_name, req_fields, parent_name, root_index, root_name in findings:
                root_line = ""
                if root_index is not None and root_name is not None:
                    root_line = f"    - root[{root_index}].name: `{root_name}`\n"
                # Fallback parent name from path if schema lacks explicit name
                fallback_parent_name = ""
                try:
                    parts = prop_path.split(".properties.")
                    if len(parts) >= 2:
                        fallback_parent_name = parts[-2].split(".")[-1]
                except Exception:
                    fallback_parent_name = ""
                effective_parent_name = parent_name if parent_name else fallback_parent_name
                parent_line = f"    - parent.name: `{effective_parent_name}`\n" if effective_parent_name else ""
                report_lines.append(
                    f"- **Path:** `{prop_path}`\n"
                    f"    - property: `{prop_name}`\n"
                    f"    - child required fields: `{req_fields}`\n"
                    f"{parent_line}"
                    f"{root_line}"
                )
                csv_rows.append({
                    "schema_file": filename,
                    "path": prop_path,
                    "property": prop_name,
                    "child_required_fields": json.dumps(req_fields, ensure_ascii=False),
                    "parent_name": effective_parent_name,
                    "root_index": root_index if root_index is not None else "",
                    "root_name": root_name if root_name is not None else "",
                })

    if not report_lines:
        print("# Optional object fields with nested required subfields\n\nNo issues found in any schema.")
    else:
        print("# Optional object fields with nested required subfields\n")
        print("\n".join(report_lines))
    # Write CSV
    output_dir = os.path.join(os.path.dirname(__file__), "..", "analysis_output")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "optional_object_with_required_children.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "schema_file",
                "path",
                "property",
                "child_required_fields",
                "parent_name",
                "root_index",
                "root_name",
            ],
        )
        writer.writeheader()
        for row in csv_rows:
            writer.writerow(row)


if __name__ == "__main__":
    main()



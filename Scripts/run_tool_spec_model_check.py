import os
import re
import sys
import argparse
import importlib
from pathlib import Path
from typing import Dict, Any, Tuple, List, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
APIS_DIR = REPO_ROOT / "APIs"
if str(APIS_DIR) not in sys.path:
    sys.path.insert(0, str(APIS_DIR))


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def find_decorator_models_in_module(py_file: str) -> Dict[str, Tuple[str, str]]:
    text = read_text(py_file)
    results: Dict[str, Tuple[str, str]] = {}
    pattern = re.compile(
        r"@tool_spec\s*\((?P<args>.*?)\)\s*def\s+(?P<func>\w+)\s*\(", re.DOTALL
    )
    for match in pattern.finditer(text):
        args_block = match.group("args")
        func_name = match.group("func")
        im = re.search(r"input_model\s*=\s*([A-Za-z_][A-Za-z0-9_]*)", args_block)
        om = re.search(r"output_model\s*=\s*([A-Za-z_][A-Za-z0-9_]*)", args_block)
        if im and om:
            results[func_name] = (im.group(1), om.group(1))
    return results


def clean_schema_from_model(model_cls) -> Dict[str, Any]:
    from APIs.common_utils.tool_spec_decorator import _clean_and_inline_schema

    raw = model_cls.model_json_schema()
    defs = raw.pop("$defs", {})
    return _clean_and_inline_schema(raw, defs)


def safe_types(node: Any) -> List[str]:
    if not isinstance(node, dict):
        return []
    types: List[str] = []
    t = node.get("type")
    if isinstance(t, str):
        types.append(t)
    if node.get("nullable") is True and "null" not in types:
        types.append("null")
    any_of = node.get("anyOf")
    if isinstance(any_of, list):
        for alt in any_of:
            if isinstance(alt, dict) and isinstance(alt.get("type"), str):
                if alt["type"] not in types:
                    types.append(alt["type"])
    return sorted(types)


def types_compatible(expected_types: List[str], actual_types: List[str]) -> bool:
    if expected_types == actual_types:
        return True
    e = set(expected_types)
    a = set(actual_types)
    if e == {"integer", "number"} and a == {"number"}:
        return True
    if e == {"number"} and a == {"integer", "number"}:
        return True
    return False


def extract_properties(node: Any) -> Dict[str, Any]:
    if not isinstance(node, dict):
        return {}
    
    if isinstance(node.get("properties"), dict):
        return node["properties"]
    
    any_of = node.get("anyOf")
    if isinstance(any_of, list):
        for alt in any_of:
            if isinstance(alt, dict) and isinstance(alt.get("properties"), dict):
                return alt["properties"]
    
    return {}


def compare_nodes(
    expected: Any, actual: Any, issues: list, file_path: str, path: str
) -> None:
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        issues.append(
            {
                "file_path": file_path,
                "path": path,
                "issue": "Schemas are not comparable objects.",
            }
        )
        return
    etypes = safe_types(expected)
    atypes = safe_types(actual)
    
    has_expected_object = "object" in etypes
    has_actual_object = "object" in atypes
    
    if has_expected_object and has_actual_object:
        eprops = extract_properties(expected)
        aprops = extract_properties(actual)
        ekeys = set(eprops.keys())
        akeys = set(aprops.keys())
        missing = sorted(list(ekeys - akeys))
        extra = sorted(list(akeys - ekeys))
        if missing:
            issues.append(
                {
                    "file_path": file_path,
                    "path": path,
                    "issue": f"Missing properties in spec: {missing}",
                }
            )
        if extra:
            issues.append(
                {
                    "file_path": file_path,
                    "path": path,
                    "issue": f"Extra properties in spec: {extra}",
                }
            )
        for key in sorted(ekeys & akeys):
            compare_nodes(
                eprops[key], aprops[key], issues, file_path, f"{path}.properties.{key}"
            )
    
    if not types_compatible(etypes, atypes):
        issues.append(
            {
                "file_path": file_path,
                "path": path,
                "issue": f"Type mismatch. expected={etypes}, actual={atypes}",
            }
        )
    
    if "array" in etypes and "array" in atypes:
        expected_items = expected.get("items")
        actual_items = actual.get("items")
        
        if not expected_items and "anyOf" in expected:
            for alt in expected.get("anyOf", []):
                if isinstance(alt, dict) and alt.get("type") == "array" and "items" in alt:
                    expected_items = alt["items"]
                    break
        
        if not actual_items and "anyOf" in actual:
            for alt in actual.get("anyOf", []):
                if isinstance(alt, dict) and alt.get("type") == "array" and "items" in alt:
                    actual_items = alt["items"]
                    break
        
        if expected_items and actual_items:
            compare_nodes(
                expected_items, actual_items, issues, file_path, f"{path}.items"
            )


def iterate_service_functions() -> Iterable[Dict[str, Any]]:
    root = str(REPO_ROOT)
    apis_root = os.path.join(root, "APIs")
    from APIs.common_utils.utils import discover_services

    services = discover_services()
    for service in services:
        service_dir = os.path.join(apis_root, service)
        if not os.path.isdir(service_dir):
            continue
        py_files = [
            f
            for f in os.listdir(service_dir)
            if f.endswith(".py") and f != "__init__.py"
        ]
        for py_name in py_files:
            py_path = os.path.join(service_dir, py_name)
            func_to_models = find_decorator_models_in_module(py_path)
            if not func_to_models:
                continue
            module_name = f"APIs.{service}.{os.path.splitext(py_name)[0]}"
            try:
                module = importlib.import_module(module_name)
            except Exception:
                try:
                    module_name = f"{service}.{os.path.splitext(py_name)[0]}"
                    module = importlib.import_module(module_name)
                except Exception:
                    continue
            models_mod = None
            for mm in (
                f"APIs.{service}.SimulationEngine.models",
                f"{service}.SimulationEngine.models",
            ):
                try:
                    models_mod = importlib.import_module(mm)
                    break
                except Exception:
                    continue
            if models_mod is None:
                continue
            for func_name, (
                input_model_name,
                output_model_name,
            ) in func_to_models.items():
                func = getattr(module, func_name, None)
                if func is None or not hasattr(func, "spec"):
                    continue
                yield {
                    "py_path": py_path,
                    "func_name": func_name,
                    "spec": getattr(func, "spec") or {},
                    "models_mod": models_mod,
                    "input_model_name": input_model_name,
                    "output_model_name": output_model_name,
                }


def generate_report() -> Dict[str, Any]:
    input_issues: List[Dict[str, str]] = []
    output_issues: List[Dict[str, str]] = []
    checked_functions = 0
    for item in iterate_service_functions():
        file_path = item["py_path"]
        func_name = item["func_name"]
        spec = item["spec"]
        models_mod = item["models_mod"]
        checked_functions += 1
        params_schema = spec.get("parameters")
        try:
            input_model_cls = getattr(models_mod, item["input_model_name"])
        except AttributeError as e:
            input_issues.append(
                {
                    "file_path": file_path,
                    "path": f"function({func_name})",
                    "issue": f"Model class not found: {e}",
                }
            )
            continue
        expected_params = clean_schema_from_model(input_model_cls)
        if isinstance(params_schema, dict):
            compare_nodes(
                expected_params,
                params_schema,
                input_issues,
                file_path,
                f"function({func_name}).parameters",
            )
        else:
            input_issues.append(
                {
                    "file_path": file_path,
                    "path": f"function({func_name}).parameters",
                    "issue": "Missing or invalid 'parameters' in spec.",
                }
            )

        response_schema = spec.get("response")
        try:
            output_model_cls = getattr(models_mod, item["output_model_name"])
        except AttributeError as e:
            output_issues.append(
                {
                    "file_path": file_path,
                    "path": f"function({func_name})",
                    "issue": f"Model class not found: {e}",
                }
            )
            continue
        expected_response = clean_schema_from_model(output_model_cls)
        if isinstance(response_schema, dict):
            compare_nodes(
                expected_response,
                response_schema,
                output_issues,
                file_path,
                f"function({func_name}).response",
            )
    return {
        "checked_functions": checked_functions,
        "input_issues": input_issues,
        "output_issues": output_issues,
    }


def trim_path_to_apis(file_path: str) -> str:
    try:
        p = Path(file_path)
        parts = p.parts
        if "APIs" in parts:
            idx = parts.index("APIs")
            return str(Path(*parts[idx:]))
    except Exception:
        pass
    return file_path


def format_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("## Tool Spec Model/Schema Match Report")
    lines.append("")
    lines.append(f"- Checked functions: {report['checked_functions']}")
    lines.append(f"- Input model mismatches: {len(report['input_issues'])}")
    lines.append(f"- Output model mismatches: {len(report['output_issues'])}")
    lines.append("")
    if report["input_issues"]:
        lines.append("### Input Model Issues")
        for i in report["input_issues"]:
            path_disp = trim_path_to_apis(i["file_path"]) if i.get("file_path") else "N/A"
            lines.append(f"- In `{path_disp}` at `{i['path']}`: {i['issue']}")
        lines.append("")
    if report["output_issues"]:
        lines.append("### Output Model Issues")
        for i in report["output_issues"]:
            path_disp = trim_path_to_apis(i["file_path"]) if i.get("file_path") else "N/A"
            lines.append(f"- In `{path_disp}` at `{i['path']}`: {i['issue']}")
        lines.append("")
    if not report["input_issues"] and not report["output_issues"]:
        lines.append("All checks passed.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-file", default="tool_spec_model_report.md")
    args = parser.parse_args()

    report = generate_report()
    md = format_markdown(report)
    with open(args.report_file, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Tool Spec Model/Schema Match Report written to {args.report_file}")
    has_issues = bool(report["input_issues"] or report["output_issues"])
    return 1 if has_issues else 0


if __name__ == "__main__":
    sys.exit(main())

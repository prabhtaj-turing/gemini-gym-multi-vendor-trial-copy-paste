#!/usr/bin/env python3
"""
Analyze function usage from specified modules across .ipynb notebooks.

This version has a **hardcoded config block** at the top. Edit only the CONFIG
section to set the notebook directory, modules to track, recursion, and output
file prefix.

Outputs
- <OUT_PREFIX>_per_notebook.csv (notebook, module, function, count)
- <OUT_PREFIX>_overall.csv (module, function, count, notebooks_used_in)
- <OUT_PREFIX>_summary.json (structured per-notebook + overall; now also includes
  unique notebook counts per function under `overall`)

Notes
- Handles: `import module as alias`, `from module import func`, `from module.sub import func as alias`
- Detects calls like `module.func()`, `alias.func()`, `module.sub.func()`, and `alias.sub.func()`
- Processes notebooks cell-by-cell to accumulate imports before counting later calls
- A "module" match is any call whose resolved module path starts with one of the provided names.
- "function" in outputs is the dotted path after the matched module root, e.g. for
  `slack.users.find_user()` -> module="slack", function="users.find_user".
"""

from __future__ import annotations

# ======================
# ====== CONFIG =========
# ======================
from pathlib import Path
import os  # <-- moved up so we can build MODULES here safely

# Directory containing your .ipynb notebooks
NOTEBOOK_DIR: Path = Path("./notebooks")  # <-- change to your path

# Which top-level modules/packages to track
# If you want to auto-track everything under a folder, keep the comprehension below.
# It turns filenames like "requests.py" into "requests" and keeps directory names as-is.
# (Skips hidden/dunder entries.)
MODULES = {
    name.split(".")[0]
    for name in os.listdir("clean_workspace/APIs")
    if not name.startswith((".", "__"))
}
# Or: MODULES = {"slack", "slack_sdk", "requests"}

# Recurse into subdirectories under NOTEBOOK_DIR
RECURSIVE: bool = True

# Output filename prefix (three files will be created)
OUT_PREFIX: str = "module_function_usage"

# ======================
# === IMPLEMENTATION ===
# ======================
import ast
import csv
import json
from typing import Dict, List, Tuple, Optional, Set


def dotted_name_from_attr(node: ast.AST) -> Optional[List[str]]:
    """
    Reconstruct a dotted name from an Attribute/Name AST node.

    Returns list like ["slack", "users", "find_user"] for slack.users.find_user
    or ["find_user"] for a bare Name.

    Returns None if not a Name/Attribute chain.
    """
    parts: List[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        parts.reverse()
        return parts
    return None


def root_of_module(module_path: str) -> str:
    """Return the top-level package (first segment) of a dotted module path."""
    return module_path.split('.')[0]


class ModuleCallAnalyzer(ast.NodeVisitor):
    """
    Tracks:
      - module_aliases: alias -> full module path (e.g., {'sl': 'slack', 'sdk': 'slack_sdk.web'})
      - from_imported_funcs: func_alias -> (full module path, original_name)
    Counts calls that resolve to one of target modules.
    """
    def __init__(self, target_modules: Set[str]) -> None:
        self.target_modules = set(target_modules)
        self.module_aliases: Dict[str, str] = {}           # alias -> full module path
        self.from_imported_funcs: Dict[str, Tuple[str,str]] = {}  # alias -> (module path, original func/class)
        self.collected_calls: List[Tuple[str, str]] = []    # list of (matched_module_root, function_dotted_after_root)

    def _matches_target(self, module_path: str) -> Optional[str]:
        """If module_path starts with any target module, return that target root; else None."""
        for m in self.target_modules:
            if module_path == m or module_path.startswith(m + "."):
                return m
        return None

    # ---- Imports ----

    def visit_Import(self, node: ast.Import) -> None:
        # import slack as sl   -> module_aliases['sl'] = 'slack'
        # import slack_sdk.web as web -> module_aliases['web'] = 'slack_sdk.web'
        for alias in node.names:
            mod = alias.name
            asname = alias.asname or root_of_module(mod)
            self.module_aliases[asname] = mod

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        # from slack import find_user as fu -> from_imported_funcs['fu'] = ('slack', 'find_user')
        # from slack_sdk.web import WebClient -> ('slack_sdk.web', 'WebClient')
        if node.level and node.level > 0:
            return  # Skip relative imports for simplicity
        if not node.module:
            return
        base_module = node.module
        for alias in node.names:
            if alias.name == '*':
                continue  # Not trackable reliably
            asname = alias.asname or alias.name
            self.from_imported_funcs[asname] = (base_module, alias.name)

    # ---- Calls ----

    def visit_Call(self, node: ast.Call) -> None:
        # Handle func being an Attribute chain or a Name
        # 1) Attribute: something.like.this()
        dotted = dotted_name_from_attr(node.func)
        if dotted:
            base = dotted[0]
            # Resolve base if it's an alias to a module
            if base in self.module_aliases:
                full_module = self.module_aliases[base]
            else:
                # The base might itself be a top-level module name
                full_module = base

            matched_root = self._matches_target(full_module)
            if matched_root:
                # Build function path AFTER the matched root
                full_call_path = dotted[:]  # e.g., ['slack', 'users', 'find_user'] or ['sl', 'x', 'y']
                # Replace alias with its full module path split to compute accurate "after root"
                if base in self.module_aliases:
                    expanded = self.module_aliases[base].split(".")
                    full_call_path = expanded + full_call_path[1:]
                # Now strip the matched root prefix
                after_root: List[str] = full_call_path[len(matched_root.split(".")):]
                function_after_root = ".".join(after_root)
                if function_after_root:
                    self.collected_calls.append((matched_root, function_after_root))
            self.generic_visit(node)
            return

        # 2) Name: bare function like find_user()
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name in self.from_imported_funcs:
                mod_path, original = self.from_imported_funcs[name]
                matched_root = self._matches_target(mod_path)
                if matched_root:
                    # function path after root might include submodules if any
                    tail = mod_path.split(".")[len(matched_root.split(".")):]
                    func_after_root = ".".join(tail + [original]) if tail else original
                    self.collected_calls.append((matched_root, func_after_root))

        self.generic_visit(node)


# --------------------------
# Notebook & FS utilities
# --------------------------

def _strip_jupyter_magics(code: str) -> str:
    """Remove common Jupyter magics / shell escapes that break AST parsing."""
    lines = []
    for line in code.splitlines():
        if line.lstrip().startswith(('%', '!')):
            lines.append('')
        else:
            lines.append(line)
    return "\n".join(lines)


def read_code_cells_from_notebook(nb_path: Path) -> List[str]:
    """Return list of source strings for code cells in a .ipynb."""
    try:
        with nb_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to read {nb_path}: {e}")
        return []

    cells = data.get("cells", [])
    code_sources: List[str] = []
    for cell in cells:
        if cell.get("cell_type") == "code":
            src = cell.get("source", "")
            if isinstance(src, list):
                raw = "".join(src)
            elif isinstance(src, str):
                raw = src
            else:
                raw = ""
            code_sources.append(_strip_jupyter_magics(raw))
    return code_sources


def iter_ipynb_files(root: Path, recursive: bool) -> List[Path]:
    if recursive:
        return [p for p in root.rglob("*.ipynb") if p.is_file()]
    else:
        return [p for p in root.glob("*.ipynb") if p.is_file()]


# --------------------------
# Main analysis pipeline
# --------------------------

def analyze_notebook(nb_path: Path, target_modules: Set[str]) -> Dict[Tuple[str,str], int]:
    """
    Returns a dict mapping (module_root, function_after_root) -> count for a single notebook.
    """
    counts: Dict[Tuple[str,str], int] = {}
    analyzer = ModuleCallAnalyzer(target_modules)

    # Process cells in order so imports can appear before usage
    for code in read_code_cells_from_notebook(nb_path):
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Skip cells with invalid syntax (e.g., remaining magics)
            continue
        analyzer.visit(tree)

    for mod_root, func_after_root in analyzer.collected_calls:
        counts[(mod_root, func_after_root)] = counts.get((mod_root, func_after_root), 0) + 1

    return counts


def aggregate_counts(per_nb: Dict[str, Dict[Tuple[str,str], int]]) -> Dict[Tuple[str,str], int]:
    overall: Dict[Tuple[str,str], int] = {}
    for nb, counts in per_nb.items():
        for k, v in counts.items():
            overall[k] = overall.get(k, 0) + v
    return overall


def compute_unique_notebook_counts(per_nb: Dict[str, Dict[Tuple[str,str], int]]) -> Dict[Tuple[str,str], int]:
    """Number of distinct notebooks that use each (module,function)."""
    seen: Dict[Tuple[str,str], Set[str]] = {}
    for nb, counts in per_nb.items():
        for key, c in counts.items():
            if c > 0:
                seen.setdefault(key, set()).add(nb)
    return {k: len(v) for k, v in seen.items()}


def write_csv_per_notebook(per_nb: Dict[str, Dict[Tuple[str,str], int]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["notebook", "module", "function", "count"])
        for nb, counts in sorted(per_nb.items()):
            for (mod, func), c in sorted(counts.items()):
                writer.writerow([nb, mod, func, c])


def write_csv_overall(overall: Dict[Tuple[str,str], int], out_csv: Path, unique_counts: Optional[Dict[Tuple[str,str], int]] = None) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["module", "function", "count", "notebooks_used_in"])  # new column
        for (mod, func), c in sorted(overall.items()):
            unique = (unique_counts or {}).get((mod, func), 0)
            writer.writerow([mod, func, c, unique])


def write_json_summary(per_nb: Dict[str, Dict[Tuple[str,str], int]],
                       overall: Dict[Tuple[str,str], int],
                       unique_counts: Dict[Tuple[str,str], int],
                       out_json: Path) -> None:
    # Structure: {
    #   "per_notebook": { ... },
    #   "overall": {
    #       "slack": {
    #           "total_calls": N,
    #           "functions": {"users.find_user": X, ...},
    #           "unique_notebook_counts": {"users.find_user": Y, ...}
    #       }, ...
    #   }
    # }
    result = {"per_notebook": {}, "overall": {}}

    for nb, counts in per_nb.items():
        by_mod: Dict[str, Dict[str,int]] = {}
        for (mod, func), c in counts.items():
            by_mod.setdefault(mod, {})
            by_mod[mod][func] = by_mod[mod].get(func, 0) + c

        nb_obj = {}
        for mod, func_map in by_mod.items():
            nb_obj[mod] = {
                "total_calls": sum(func_map.values()),
                "functions": dict(sorted(func_map.items()))
            }
        result["per_notebook"][nb] = nb_obj

    overall_by_mod: Dict[str, Dict[str,int]] = {}
    overall_unique_by_mod: Dict[str, Dict[str,int]] = {}
    for (mod, func), c in overall.items():
        overall_by_mod.setdefault(mod, {})
        overall_by_mod[mod][func] = overall_by_mod[mod].get(func, 0) + c
        overall_unique_by_mod.setdefault(mod, {})
        overall_unique_by_mod[mod][func] = unique_counts.get((mod, func), 0)

    overall_obj = {}
    for mod in sorted(overall_by_mod.keys()):
        func_map = overall_by_mod[mod]
        overall_obj[mod] = {
            "total_calls": sum(func_map.values()),
            "functions": dict(sorted(func_map.items())),
            "unique_notebook_counts": dict(sorted(overall_unique_by_mod.get(mod, {}).items()))
        }
    result["overall"] = overall_obj

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


def main():
    root = NOTEBOOK_DIR.expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Directory not found: {root}")

    target_modules = set(MODULES)
    if not target_modules:
        print("[WARN] No modules configured to track; results will be empty.")

    notebooks = iter_ipynb_files(root, recursive=RECURSIVE)
    if not notebooks:
        print(f"No .ipynb files found under {root} (recursive={RECURSIVE}).")
        return

    per_nb_counts: Dict[str, Dict[Tuple[str,str], int]] = {}
    for nb in notebooks:
        counts = analyze_notebook(nb, target_modules)
        per_nb_counts[nb.name] = counts

    overall_counts = aggregate_counts(per_nb_counts)
    unique_counts = compute_unique_notebook_counts(per_nb_counts)

    out_per_nb_csv = Path(f"{OUT_PREFIX}_per_notebook.csv")
    out_overall_csv = Path(f"{OUT_PREFIX}_overall.csv")
    out_summary_json = Path(f"{OUT_PREFIX}_summary.json")

    write_csv_per_notebook(per_nb_counts, out_per_nb_csv)
    write_csv_overall(overall_counts, out_overall_csv, unique_counts=unique_counts)
    write_json_summary(per_nb_counts, overall_counts, unique_counts, out_summary_json)

    print(f"Wrote: {out_per_nb_csv}")
    print(f"Wrote: {out_overall_csv}")
    print(f"Wrote: {out_summary_json}")


if __name__ == "__main__":
    main()

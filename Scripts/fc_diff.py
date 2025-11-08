# Scripts/fc_diff.py
import os, re, json, argparse, subprocess, sys, difflib
from pathlib import Path
import ast
import docstring_parser  # ensure installed via workflow

# ---------------------------
# File helpers
# ---------------------------
def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def relpath(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root).as_posix())
    except Exception:
        return str(p.as_posix())

# ---------------------------
# AST utilities
# ---------------------------
def extract_docstrings_per_file(py_source: str):
    """
    Returns mapping of local function FQN (like 'Class.func' or 'func') -> docstring text (or None).
    """
    out = {}
    if not py_source:
        return out
    try:
        tree = ast.parse(py_source)
    except SyntaxError:
        return out

    class StackVisitor(ast.NodeVisitor):
        def __init__(self):
            self.stack = []

        def visit_ClassDef(self, node: ast.ClassDef):
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef):
            self._add(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            self._add(node)

        def _add(self, node):
            name = ".".join(self.stack + [node.name]) if self.stack else node.name
            doc = ast.get_docstring(node)
            out[name] = doc

    StackVisitor().visit(tree)
    return out

def walk_py_files(root: Path):
    for p in root.rglob("*.py"):
        if any(part in {".venv","venv","site-packages","__pycache__",".git"} for part in p.parts):
            continue
        yield p

# ---------------------------
# Repo-specific: _function_map and FQN resolution
# ---------------------------
def get_function_map(init_path: Path) -> dict:
    src = read_text(init_path)
    if not src:
        return {}
    try:
        tree = ast.parse(src, filename=str(init_path))
    except SyntaxError:
        return {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "_function_map":
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        return {}
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "_function_map":
            try:
                return ast.literal_eval(node.value)
            except Exception:
                return {}
    return {}

def resolve_fqn_to_path(fqn: str, apis_root: Path) -> Path | None:
    parts = fqn.split(".")
    for i in range(len(parts), 0, -1):
        module_parts = parts[:i]
        potential = apis_root.joinpath(*module_parts)
        if potential.with_suffix(".py").is_file():
            return potential.with_suffix(".py")
        if potential.is_dir() and potential.joinpath("__init__.py").is_file():
            return potential.joinpath("__init__.py")
    simple = apis_root.joinpath(*parts)
    if simple.with_suffix(".py").is_file():
        return simple.with_suffix(".py")
    if simple.joinpath("__init__.py").is_file():
        return simple.joinpath("__init__.py")
    return None

def fqn_tail_matches_local(fqn: str, local_name: str) -> bool:
    tail = fqn.split(".")
    if "." in local_name and len(tail) >= 2:
        return ".".join(tail[-2:]) == local_name
    return tail[-1] == local_name

# ---------------------------
# Detect ONLY docstring changes under APIs/
# ---------------------------
def detect_docstring_changes(base_root: Path, head_root: Path):
    apis_rel = "APIs"
    base_apis = base_root / apis_rel
    head_apis = head_root / apis_rel

    changed = []  # list of dicts: file_rel, local_name, base_doc, head_doc, status
    base_files = {relpath(p, base_root) for p in walk_py_files(base_apis)} if base_apis.exists() else set()
    head_files = {relpath(p, head_root) for p in walk_py_files(head_apis)} if head_apis.exists() else set()
    files = sorted(base_files | head_files)

    for rel in files:
        base_src = read_text(base_root / rel) if (base_root / rel).exists() else ""
        head_src = read_text(head_root / rel) if (head_root / rel).exists() else ""
        base_map = extract_docstrings_per_file(base_src) if base_src else {}
        head_map = extract_docstrings_per_file(head_src) if head_src else {}
        all_funcs = set(base_map.keys()) | set(head_map.keys())
        for name in sorted(all_funcs):
            b = base_map.get(name)
            h = head_map.get(name)
            if b == h:
                continue
            status = "modified"
            if b is None and h is not None:
                status = "added"
            elif b is not None and h is None:
                status = "removed"
            changed.append({
                "file_rel": rel,
                "local_name": name,
                "base_doc": b,
                "head_doc": h,
                "status": status
            })
    return changed

# ---------------------------
# Stubs & runner
# ---------------------------
def ensure_google_genai_stub(root: Path):
    """
    If Scripts/FCSpec.py imports 'from google import genai' and it's unavailable,
    create a stub so import doesn't fail when running FCSpec.py.
    """
    stub_root = root / "_stubs" / "google"
    (stub_root).mkdir(parents=True, exist_ok=True)
    write_text(stub_root / "__init__.py", "")
    write_text(stub_root / "genai.py", "# stubbed google.genai\n")
    return stub_root.parent  # parent of 'google' to prepend in PYTHONPATH

def run_fcspec_for_tree(repo_root: Path):
    """
    Run the tree's own Scripts/FCSpec.py to generate Schemas/*.
    """
    stub_parent = ensure_google_genai_stub(repo_root)
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{stub_parent}:{env.get('PYTHONPATH','')}"
    cmd = [sys.executable, "Scripts/FCSpec.py"]
    subprocess.run(cmd, cwd=str(repo_root), check=True, env=env)

# ---------------------------
# Patch/restore _function_map to only target public names
# ---------------------------
def patch_function_map(init_path: Path, filtered_map: dict) -> str | None:
    """
    Replace the _function_map assignment in __init__.py with a filtered dict.
    Returns the original file text (for restore) or None if not patched.
    """
    text = read_text(init_path)
    if not text:
        return None

    try:
        tree = ast.parse(text, filename=str(init_path))
    except SyntaxError:
        return None

    target_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "_function_map":
                    target_node = node
                    break
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "_function_map":
            target_node = node
        if target_node:
            break

    if not target_node or not hasattr(target_node, "lineno") or not hasattr(target_node, "end_lineno"):
        return None

    start = target_node.lineno
    end = target_node.end_lineno
    lines = text.splitlines()

    indent = re.match(r"\s*", lines[start-1]).group(0) if 0 <= start-1 < len(lines) else ""
    # Build new assignment for only the selected public names
    body = [f'{indent}_function_map = {{']
    for pub, fqn in filtered_map.items():
        body.append(f'{indent}    "{pub}": "{fqn}",')
    body.append(f'{indent}}}')
    new_block = "\n".join(body)

    new_text = "\n".join(lines[:start-1] + [new_block] + lines[end:])
    write_text(init_path, new_text)
    return text  # original for restore

def restore_file(path: Path, original_text: str | None):
    if original_text is not None:
        write_text(path, original_text)

# ---------------------------
# Link docstring-changed functions to public names in that tree
# ---------------------------
def index_public_map(repo_root: Path):
    apis_dir = repo_root / "APIs"
    pkgs = []
    pkg_to_map = {}
    if not apis_dir.exists():
        return pkgs, pkg_to_map
    for child in apis_dir.iterdir():
        if child.is_dir() and (child / "__init__.py").is_file():
            pkgs.append((child.name, child))
            pkg_to_map[child.name] = get_function_map(child / "__init__.py")
    return pkgs, pkg_to_map

def locate_public_names_for_changed(repo_root: Path, changed_entry: dict):
    """
    For a changed docstring entry (file_rel, local_name), find matching (package, public_name) in this tree.
    """
    matches = []
    file_rel = changed_entry["file_rel"]
    local_name = changed_entry["local_name"]
    apis_root = repo_root / "APIs"
    pkgs, funcmaps = index_public_map(repo_root)
    for pkg_name, pkg_dir in pkgs:
        fmap = funcmaps.get(pkg_name, {})
        for public_name, fqn in fmap.items():
            fqn_path = resolve_fqn_to_path(fqn, apis_root)
            if not fqn_path:
                continue
            if relpath(fqn_path, repo_root) != file_rel:
                continue
            if not fqn_tail_matches_local(fqn, local_name):
                continue
            matches.append((pkg_name, public_name))
    # de-dupe while preserving order
    seen = set()
    out = []
    for m in matches:
        if m not in seen:
            out.append(m)
            seen.add(m)
    return out

# ---------------------------
# Read FCs from Schemas outputs
# ---------------------------
def load_package_schema(repo_root: Path, package_name: str):
    p = repo_root / "Schemas" / f"{package_name}.json"
    if not p.is_file():
        return []
    try:
        return json.loads(read_text(p)) or []
    except Exception:
        return []

def pull_fc(repo_root: Path, package_name: str, public_name: str):
    arr = load_package_schema(repo_root, package_name)
    for item in arr:
        if item.get("name") == public_name:
            return item
    return None

# ---------------------------
# Diff helpers
# ---------------------------
def fc_param_summary(base_fc: dict | None, head_fc: dict | None) -> dict:
    base_fc = base_fc or {}
    head_fc = head_fc or {}
    b_params = (base_fc.get("parameters") or {}).get("properties") or {}
    h_params = (head_fc.get("parameters") or {}).get("properties") or {}
    b_req = set((base_fc.get("parameters") or {}).get("required") or [])
    h_req = set((head_fc.get("parameters") or {}).get("required") or [])

    added_params = sorted(set(h_params) - set(b_params))
    removed_params = sorted(set(b_params) - set(h_params))
    common = sorted(set(h_params) & set(b_params))

    modified_params = []
    for p in common:
        bt = (b_params[p] or {}).get("type")
        ht = (h_params[p] or {}).get("type")
        bdesc = ((b_params[p] or {}).get("description") or "").strip()
        hdesc = ((h_params[p] or {}).get("description") or "").strip()
        changes = []
        if bt != ht:
            changes.append(f"type: `{bt}` → `{ht}`")
        if bdesc != hdesc:
            changes.append("description changed")
        if ((b_params[p] or {}).get("properties") or {}) != ((h_params[p] or {}).get("properties") or {}):
            changes.append("object properties changed")
        if ((b_params[p] or {}).get("items") or {}) != ((h_params[p] or {}).get("items") or {}):
            changes.append("array items changed")
        if changes:
            modified_params.append((p, changes))

    return {
        "added_params": added_params,
        "removed_params": removed_params,
        "modified_params": modified_params,
        "required_added": sorted(h_req - b_req),
        "required_removed": sorted(b_req - h_req),
        "description_changed": (base_fc or {}).get("description","").strip()
                                != (head_fc or {}).get("description","").strip()
    }

def fc_unified_diff(base_fc: dict | None, head_fc: dict | None) -> str:
    b = json.dumps(base_fc or {}, indent=2, ensure_ascii=False, sort_keys=True).splitlines()
    h = json.dumps(head_fc or {}, indent=2, ensure_ascii=False, sort_keys=True).splitlines()
    diff = difflib.unified_diff(b, h, fromfile="Base", tofile="PR", lineterm="")
    return "\n".join(diff)

# ---------------------------
# Report
# ---------------------------
def build_report(doc_changes, base_root: Path, head_root: Path):
    lines = []
    lines.append("<!-- FC-REVIEW:START -->")
    lines.append("## 🔍 Function Calling (FC) Review — Docstring Changes Only (FCSpec.py per-branch)")
    lines.append("")
    if not doc_changes:
        lines.append("_No docstring changes detected in APIs/._")
        lines.append("<!-- FC-REVIEW:END -->")
        return "\n".join(lines)

    added = sum(1 for c in doc_changes if c["status"] == "added")
    removed = sum(1 for c in doc_changes if c["status"] == "removed")
    modified = sum(1 for c in doc_changes if c["status"] == "modified")
    lines.append(f"**Summary:** Added: **{added}**, Modified: **{modified}**, Removed: **{removed}**")
    lines.append("")
    lines.append("_Ran **Scripts/FCSpec.py** separately in Base (development) and PR (head) trees, limited to the docstring-changed functions._")
    lines.append("")

    for i, c in enumerate(doc_changes, 1):
        lines.append(f"### {i}. **{c['file_rel']} :: {c['local_name']}**  —  `{c['status'].upper()}`")

        base_matches = locate_public_names_for_changed(base_root, c)
        head_matches = locate_public_names_for_changed(head_root, c)

        # Base (show all matches)
        lines.append("<details><summary>Base (development)</summary>\n")
        base_fc_first = None
        if not base_matches:
            lines.append("_No matching public function in _function_map for base (or function not present)._")
        else:
            for (pkg, pub) in base_matches:
                base_fc = pull_fc(base_root, pkg, pub)
                if base_fc_first is None and base_fc is not None:
                    base_fc_first = base_fc
                lines.append(f"**Package:** `{pkg}` &nbsp;&nbsp; **Public Name:** `{pub}`")
                if base_fc:
                    lines.append("```json")
                    lines.append(json.dumps(base_fc, indent=2, ensure_ascii=False))
                    lines.append("```")
                else:
                    lines.append("_FC not found in base Schemas (maybe generation filtered or failed)._")
                lines.append("")
        lines.append("\n</details>\n")

        # Head (show all matches)
        lines.append("<details><summary>PR (proposed)</summary>\n")
        head_fc_first = None
        if not head_matches:
            lines.append("_No matching public function in _function_map for PR (or function removed)._")
        else:
            for (pkg, pub) in head_matches:
                head_fc = pull_fc(head_root, pkg, pub)
                if head_fc_first is None and head_fc is not None:
                    head_fc_first = head_fc
                lines.append(f"**Package:** `{pkg}` &nbsp;&nbsp; **Public Name:** `{pub}`")
                if head_fc:
                    lines.append("```json")
                    lines.append(json.dumps(head_fc, indent=2, ensure_ascii=False))
                    lines.append("```")
                else:
                    lines.append("_FC not found in PR Schemas (maybe generation filtered or failed)._")
                lines.append("")
        lines.append("\n</details>\n")

        # Diff summary + unified diff (use first available FC on each side)
        lines.append("<details><summary>Diff (schema changes)</summary>\n")
        summary = fc_param_summary(base_fc_first, head_fc_first)
        lines.append("**Summary**")
        lines.append("")
        lines.append(f"- Description changed: **{'Yes' if summary['description_changed'] else 'No'}**")
        if summary["required_added"]:
            lines.append(f"- Required added: `{', '.join(summary['required_added'])}`")
        if summary["required_removed"]:
            lines.append(f"- Required removed: `{', '.join(summary['required_removed'])}`")
        if summary["added_params"]:
            lines.append(f"- Params added: `{', '.join(summary['added_params'])}`")
        if summary["removed_params"]:
            lines.append(f"- Params removed: `{', '.join(summary['removed_params'])}`")
        if summary["modified_params"]:
            lines.append("- Params modified:")
            for pname, changes in summary["modified_params"]:
                lines.append(f"  - `{pname}`: " + "; ".join(changes))
        if not (summary["required_added"] or summary["required_removed"] or
                summary["added_params"] or summary["removed_params"] or
                summary["modified_params"] or summary["description_changed"]):
            lines.append("- _No schema differences detected._")
        lines.append("")

        diff_text = fc_unified_diff(base_fc_first, head_fc_first)
        if diff_text.strip():
            lines.append("```diff")
            lines.append(diff_text)
            lines.append("```")
        lines.append("\n</details>\n")

        lines.append("---")
    lines.append("<!-- FC-REVIEW:END -->")
    return "\n".join(lines)

# ---------------------------
# Orchestration
# ---------------------------
def run_filtered_fcspec(repo_root: Path, doc_changes):
    """
    For a tree (repo_root), patch each relevant package's _function_map to only the changed public names,
    run Scripts/FCSpec.py, then restore files.
    """
    # Build package -> set(public_names) map for this tree
    pkg_to_publics = {}
    for change in doc_changes:
        for (pkg, pub) in locate_public_names_for_changed(repo_root, change):
            pkg_to_publics.setdefault(pkg, set()).add(pub)

    if not pkg_to_publics:
        return

    # Load original maps and patch
    originals = {}
    apis_dir = repo_root / "APIs"
    for pkg, pubs in pkg_to_publics.items():
        init_path = apis_dir / pkg / "__init__.py"
        full_map = get_function_map(init_path)
        if not full_map:
            continue
        filtered_map = {pub: full_map[pub] for pub in pubs if pub in full_map}
        if not filtered_map:
            continue
        original = patch_function_map(init_path, filtered_map)
        if original is not None:
            originals[init_path] = original

    try:
        # Run this tree's own generator
        run_fcspec_for_tree(repo_root)
    finally:
        # Restore files
        for path, orig in originals.items():
            restore_file(path, orig)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="path to base checkout (development)")
    ap.add_argument("--head", required=True, help="path to head checkout (PR branch)")
    ap.add_argument("--out", default="fc_report.md", help="output markdown file")
    args = ap.parse_args()

    base_root = Path(args.base).resolve()
    head_root = Path(args.head).resolve()

    # 1) Detect docstring-only changes
    doc_changes = detect_docstring_changes(base_root, head_root)

    if not doc_changes:
        report = build_report(doc_changes, base_root, head_root)
        write_text(Path(args.out), report)
        print(f"Wrote {args.out} (no docstring changes).")
        return

    # 2) Run FCSpec.py in BASE, filtered to only changed functions
    try:
        run_filtered_fcspec(base_root, doc_changes)
    except subprocess.CalledProcessError as e:
        print(f"[base] FCSpec.py failed: {e}", file=sys.stderr)

    # 3) Run FCSpec.py in HEAD, filtered to only changed functions
    try:
        run_filtered_fcspec(head_root, doc_changes)
    except subprocess.CalledProcessError as e:
        print(f"[head] FCSpec.py failed: {e}", file=sys.stderr)

    # 4) Build the PR report
    report = build_report(doc_changes, base_root, head_root)
    write_text(Path(args.out), report)
    print(f"Wrote {args.out} with {len(doc_changes)} docstring-changed function(s).")

if __name__ == "__main__":
    main()

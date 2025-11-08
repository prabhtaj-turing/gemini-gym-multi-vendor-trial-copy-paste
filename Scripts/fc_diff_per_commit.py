# Scripts/fc_diff_per_commit.py
import os, re, json, argparse, subprocess, sys, difflib
from pathlib import Path
from tempfile import TemporaryDirectory
import ast
import docstring_parser

# ---------------------------
# Utility Functions
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

def extract_docstrings_per_file(py_source: str):
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
        if any(part in {".venv", "venv", "site-packages", "__pycache__", ".git"} for part in p.parts):
            continue
        yield p

def detect_docstring_changes(base_root: Path, head_root: Path, only_files: list[str] | None = None):
    apis_rel = "APIs"
    base_apis = base_root / apis_rel
    head_apis = head_root / apis_rel
    changed = []
    base_files = {relpath(p, base_root) for p in walk_py_files(base_apis)} if base_apis.exists() else set()
    head_files = {relpath(p, head_root) for p in walk_py_files(head_apis)} if head_apis.exists() else set()
    files = sorted(set(only_files) & (base_files | head_files)) if only_files else sorted(base_files | head_files)

    for rel in files:
        base_src = read_text(base_root / rel) if (base_root / rel).exists() else ""
        head_src = read_text(head_root / rel) if (head_root / rel).exists() else ""
        base_map = extract_docstrings_per_file(base_src) if base_src else {}
        head_map = extract_docstrings_per_file(head_src) if head_src else {}
        all_funcs = set(base_map) | set(head_map)
        for name in sorted(all_funcs):
            b = base_map.get(name)
            h = head_map.get(name)
            if b == h:
                continue
            status = "modified"
            if b is None:
                status = "added"
            elif h is None:
                status = "removed"
            changed.append({"file_rel": rel, "local_name": name, "base_doc": b, "head_doc": h, "status": status})
    return changed

def get_commit_shas(base_sha: str, head_sha: str, repo_path: Path) -> list[str]:
    cmd = ["git", "rev-list", f"{base_sha}..{head_sha}", "--reverse"]
    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, check=True)
    return result.stdout.strip().splitlines()

def get_commit_message(commit_sha: str, repo_path: Path) -> str:
    result = subprocess.run(["git", "log", "--format=%s", "-n", "1", commit_sha], cwd=repo_path, capture_output=True, text=True, check=True)
    return result.stdout.strip()

def get_changed_files(prev_sha: str, curr_sha: str, repo_path: Path) -> list[str]:
    result = subprocess.run(["git", "diff", "--name-only", prev_sha, curr_sha], cwd=repo_path, capture_output=True, text=True, check=True)
    return [f for f in result.stdout.strip().splitlines() if f.startswith("APIs/") and f.endswith(".py")]

def checkout_commit(commit_sha: str, repo_path: Path, dest_path: Path):
    subprocess.run(["git", "--work-tree", str(dest_path), "checkout", commit_sha, "--", "APIs", "Schemas", "Scripts"], cwd=repo_path, check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Path to full repo with .git")
    ap.add_argument("--base_sha", required=True)
    ap.add_argument("--head_sha", required=True)
    ap.add_argument("--out", default="fc_report.md")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    commit_shas = get_commit_shas(args.base_sha, args.head_sha, repo)
    commits = list(zip([args.base_sha] + commit_shas[:-1], commit_shas))

    with TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        lines = []
        lines.append("<!-- FC-REVIEW:START -->")
        lines.append("## 🔍 FC Review — Per Commit (Docstring Changes Only)")
        lines.append("")

        total_changes = 0
        for prev, curr in commits:
            commit_msg = get_commit_message(curr, repo)
            commit_dir_base = tmp / f"{prev[:7]}"
            commit_dir_head = tmp / f"{curr[:7]}"

            checkout_commit(prev, repo, commit_dir_base)
            checkout_commit(curr, repo, commit_dir_head)

            files = get_changed_files(prev, curr, repo)
            changes = detect_docstring_changes(commit_dir_base, commit_dir_head, only_files=files)

            if not changes:
                continue
            total_changes += len(changes)
            lines.append(f"### 📦 Commit `{curr[:7]}` — {commit_msg}")
            for c in changes:
                lines.append(f"- `{c['file_rel']} :: {c['local_name']}` — `{c['status'].upper()}`")
            lines.append("")

        if total_changes == 0:
            lines.append("_No docstring changes detected in any commit._")

        lines.append("<!-- FC-REVIEW:END -->")
        write_text(Path(args.out), "\n".join(lines))
        print(f"Wrote {args.out} with {total_changes} total changes across {len(commits)} commits.")

if __name__ == "__main__":
    main()

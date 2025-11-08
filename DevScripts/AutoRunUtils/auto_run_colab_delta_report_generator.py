#!/usr/bin/env python3
import argparse
import csv
import os
import sys
from typing import Dict, List, Tuple


def read_csv_rows(csv_path: str) -> List[Dict[str, str]]:
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    with open(csv_path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def classify_by_status(rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    passing_rows: List[Dict[str, str]] = []
    failing_rows: List[Dict[str, str]] = []
    for row in rows:
        status_value = (row.get("Status") or "").strip()
        if status_value == "Success":
            passing_rows.append(row)
        else:
            failing_rows.append(row)
    return passing_rows, failing_rows


def truncate_text(text: str, max_length: int = 180) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


def print_summary(passing_rows: List[Dict[str, str]], failing_rows: List[Dict[str, str]]) -> None:
    total = len(passing_rows) + len(failing_rows)
    pass_count = len(passing_rows)
    fail_count = len(failing_rows)
    pass_pct = (pass_count / total * 100.0) if total else 0.0
    fail_pct = (fail_count / total * 100.0) if total else 0.0

    print(f"Total: {total}")
    print(f"Passing (Status == 'Success'): {pass_count} ({pass_pct:.1f}%)")
    print(f"Failing (Status != 'Success'): {fail_count} ({fail_pct:.1f}%)")
    print()

    if passing_rows:
        print("Passing colabs:")
        for row in sorted(passing_rows, key=lambda r: (r.get("Notebook") or "")):
            notebook = row.get("Notebook") or ""
            url = row.get("colab_url") or ""
            exec_time = row.get("Execution Time (seconds)") or ""
            print(f"- {notebook} | time={exec_time}s | {url}")
        print()

    if failing_rows:
        print("Failing colabs:")
        for row in sorted(failing_rows, key=lambda r: (r.get("Notebook") or "")):
            notebook = row.get("Notebook") or ""
            url = row.get("colab_url") or ""
            status_value = row.get("Status") or ""
            print(f"- {notebook} | {url}")
            if status_value:
                print(f"  Reason: {truncate_text(status_value)}")

    # Always print counts again at the end so they are visible even if the output is long
    print()
    print(f"Passing: {pass_count}")
    print(f"Failing: {fail_count}")
    print(f"Total: {total}")


def parse_args() -> argparse.Namespace:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_csv = os.path.join(
        project_root,
        "aug25_development_20250825_095238.csv",
    )
    before_csv_default = os.path.join(
        project_root,
        "aug25_development_20250825_095238.csv",
    )
    after_csv_default = os.path.join(
        project_root,
        "aug25_email-validations_20250825_112426.csv",
    )
    parser = argparse.ArgumentParser(
        description="Summarize passing and failing colabs from a run CSV (by Status column)."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=default_csv,
        help=f"Path to CSV file (default: {default_csv})",
    )
    parser.add_argument(
        "--counts-only",
        "-c",
        action="store_true",
        help="Print only counts for passing and failing, suppress detailed lists.",
    )
    # Compare mode
    parser.add_argument(
        "--compare",
        "-d",
        action="store_true",
        help="Compare two CSVs (before vs after) and write a Markdown delta report.",
    )
    parser.add_argument(
        "--before",
        default=before_csv_default,
        help=f"Before CSV path (default: {before_csv_default})",
    )
    parser.add_argument(
        "--after",
        default=after_csv_default,
        help=f"After CSV path (default: {after_csv_default})",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(project_root, "DevScripts", "colab_delta_report.log.md"),
        help="Output Markdown path for the delta report.",
    )
    parser.add_argument(
        "--full-errors",
        dest="full_errors",
        action="store_true",
        default=True,
        help="Include full error messages as Markdown code blocks under each failing entry (default: enabled).",
    )
    parser.add_argument(
        "--no-full-errors",
        dest="full_errors",
        action="store_false",
        help="Disable inclusion of full error messages in the report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # Compare mode branch
    if getattr(args, "compare", False):
        try:
            before_rows = read_csv_rows(args.before)
            after_rows = read_csv_rows(args.after)
        except Exception as exc:  # noqa: BLE001 - concise error
            print(f"Error: {exc}")
            sys.exit(1)

        before_pass, before_fail = classify_by_status(before_rows)
        after_pass, after_fail = classify_by_status(after_rows)

        def index_by_notebook(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
            index: Dict[str, Dict[str, str]] = {}
            for r in rows:
                name = (r.get("Notebook") or "").strip()
                if name:
                    index[name] = r
            return index

        before_index = index_by_notebook(before_rows)
        after_index = index_by_notebook(after_rows)

        before_pass_names = { (r.get("Notebook") or "").strip() for r in before_pass }
        before_fail_names = { (r.get("Notebook") or "").strip() for r in before_fail }
        after_pass_names = { (r.get("Notebook") or "").strip() for r in after_pass }
        after_fail_names = { (r.get("Notebook") or "").strip() for r in after_fail }
        before_all_names = set(before_index.keys())

        # Deltas
        regressions = sorted([n for n in (before_pass_names & after_fail_names) if n])
        fixes = sorted([n for n in (before_fail_names & after_pass_names) if n])
        new_failing = sorted([n for n in (after_fail_names - before_all_names) if n])
        new_passing = sorted([n for n in (after_pass_names - before_all_names) if n])

        # Markdown report
        lines: List[str] = []
        lines.append("# Colab Delta Report")
        lines.append("")
        lines.append(f"- Before: `{args.before}`")
        lines.append(f"- After: `{args.after}`")
        lines.append("")
        lines.append("## Summary")
        lines.append(f"- Before passing: {len(before_pass)}")
        lines.append(f"- Before failing: {len(before_fail)}")
        lines.append(f"- After passing: {len(after_pass)}")
        lines.append(f"- After failing: {len(after_fail)}")
        lines.append("")
        lines.append(f"- Regressions (was passing → now failing): {len(regressions)}")
        lines.append(f"- Fixes (was failing → now passing): {len(fixes)}")
        lines.append(f"- New failing (not present before): {len(new_failing)}")
        lines.append(f"- New passing (not present before): {len(new_passing)}")
        lines.append("")

        def md_escape(text: str) -> str:
            return (text or "").replace("|", "\\|").strip()

        def add_list(title: str, names: List[str], include_reason: bool = False, include_time: bool = False) -> None:
            if not names:
                return
            lines.append(f"## {title}")
            for name in names:
                row = after_index.get(name)
                url = md_escape((row or {}).get("colab_url") or "")
                status_value = (row or {}).get("Status") or ""
                exec_time = (row or {}).get("Execution Time (seconds)") or ""
                base = f"- {md_escape(name)}"
                if include_time and exec_time:
                    base += f" | time={exec_time}s"
                if url:
                    base += f" | {url}"
                lines.append(base)
                if include_reason and status_value:
                    if args.full_errors:
                        lines.append("  ```python")
                        lines.append("  " + status_value.strip())
                        lines.append("  ```")
                    else:
                        reason = truncate_text(status_value, 240)
                        lines.append(f"  - Reason: {md_escape(reason)}")
            lines.append("")

        add_list("Regressions (was passing → now failing)", regressions, include_reason=True)
        add_list("Fixes (was failing → now passing)", fixes, include_time=True)
        add_list("New failing (not present before)", new_failing, include_reason=True)
        add_list("New passing (not present before)", new_passing, include_time=True)

        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Delta report written to: {args.out}")
        print(f"Regressions: {len(regressions)} | Fixes: {len(fixes)} | New failing: {len(new_failing)} | New passing: {len(new_passing)}")
        return

    # Default: single-file summary
    try:
        rows = read_csv_rows(args.csv_path)
    except Exception as exc:  # noqa: BLE001 - show concise error to user
        print(f"Error: {exc}")
        sys.exit(1)

    passing_rows, failing_rows = classify_by_status(rows)
    if args.counts_only:
        total = len(passing_rows) + len(failing_rows)
        print(f"Passing: {len(passing_rows)}")
        print(f"Failing: {len(failing_rows)}")
        print(f"Total: {total}")
    else:
        print_summary(passing_rows, failing_rows)


if __name__ == "__main__":
    main()

